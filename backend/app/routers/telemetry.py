"""
IoT 时序数据聚合与分析
对齐现网：水质监测历史曲线、设备预警功能
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.response import ApiError, ok
from app.db import get_db
from app.deps import CurrentUser, get_current_user
from app.models import IotDevice, TsTelemetry

router = APIRouter(prefix="/iot/telemetry", tags=["iot-telemetry"])


@router.get("/aggregated")
def get_aggregated_telemetry(
    deviceId: int,
    indicators: str,  # 逗号分隔，如：temperature,DO,pH
    startTime: str,
    endTime: str,
    interval: str = "1h",  # 1min, 5min, 1h, 1d
    cu: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    数据聚合查询
    对齐现网：水质历史曲线
    
    现网交互：
    1. 用户选择设备、指标、时间范围
    2. 选择聚合间隔（1小时/1天）
    3. 调用此接口获取聚合数据
    4. 前端绘制历史曲线
    
    现网水质指标：
    - temperature: 水温
    - DO: 溶解氧
    - pH: pH值
    - ammonia: 氨氮
    - nitrite: 亚硝酸盐
    - permanganate: 高锰酸盐指数
    - alkalinity: 碱度
    - salinity: 盐度
    - suspended: 悬浮物
    - algae: 藻类
    """
    # 权限检查
    device = db.get(IotDevice, deviceId)
    if not device:
        raise ApiError(40400, "设备不存在", 404)
    
    if cu.user.user_type == "ENTERPRISE" and device.enterprise_id != cu.user.enterprise_id:
        raise ApiError(40300, "无权限访问此设备", 403)
    
    # 时间间隔映射（简化版，不使用数据库的时间桶函数）
    interval_minutes = {
        "1min": 1,
        "5min": 5,
        "1h": 60,
        "1d": 1440
    }
    
    minutes = interval_minutes.get(interval, 60)
    
    # 查询原始数据
    start_dt = datetime.fromisoformat(startTime)
    end_dt = datetime.fromisoformat(endTime)
    
    indicator_list = [ind.strip() for ind in indicators.split(',')]
    
    data = db.scalars(
        select(TsTelemetry)
        .where(
            TsTelemetry.device_id == deviceId,
            TsTelemetry.point_code.in_(indicator_list),
            TsTelemetry.occurred_at >= start_dt,
            TsTelemetry.occurred_at <= end_dt,
            TsTelemetry.deleted == 0
        )
        .order_by(TsTelemetry.occurred_at)
    ).all()
    
    # 聚合计算（Python实现）
    buckets = {}
    for d in data:
        # 计算所属时间桶
        bucket_time = d.occurred_at.replace(
            minute=(d.occurred_at.minute // minutes) * minutes,
            second=0,
            microsecond=0
        )
        bucket_key = bucket_time.isoformat()
        
        if bucket_key not in buckets:
            buckets[bucket_key] = {"time": bucket_key}
        
        code = d.point_code
        if code not in buckets[bucket_key]:
            buckets[bucket_key][code] = []
        buckets[bucket_key][code].append(float(d.point_value))
    
    # 计算统计值
    result = []
    for bucket_key in sorted(buckets.keys()):
        bucket = buckets[bucket_key]
        item = {"time": bucket["time"]}
        
        for code in indicator_list:
            if code in bucket:
                values = bucket[code]
                item[code] = {
                    "avg": round(sum(values) / len(values), 2),
                    "min": round(min(values), 2),
                    "max": round(max(values), 2),
                    "count": len(values)
                }
        
        result.append(item)
    
    return ok({
        "interval": interval,
        "deviceId": deviceId,
        "indicators": indicator_list,
        "data": result
    })


@router.get("/latest")
def get_latest_telemetry(
    deviceId: int,
    indicators: Optional[str] = None,
    cu: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取最新数据
    对齐现网：水质实时监测卡片
    
    现网交互：
    1. 前端轮询此接口（每5秒）
    2. 获取最新的水质数据
    3. 更新实时数据卡片
    """
    device = db.get(IotDevice, deviceId)
    if not device:
        raise ApiError(40400, "设备不存在", 404)
    
    if cu.user.user_type == "ENTERPRISE" and device.enterprise_id != cu.user.enterprise_id:
        raise ApiError(40300, "无权限", 403)
    
    q = select(TsTelemetry).where(
        TsTelemetry.device_id == deviceId,
        TsTelemetry.deleted == 0
    )
    
    if indicators:
        indicator_list = [ind.strip() for ind in indicators.split(',')]
        q = q.where(TsTelemetry.point_code.in_(indicator_list))
    
    # 获取每个指标的最新值
    latest_data = {}
    for d in db.scalars(q.order_by(TsTelemetry.occurred_at.desc())).all():
        if d.point_code not in latest_data:
            latest_data[d.point_code] = {
                "value": float(d.point_value),
                "time": d.occurred_at.isoformat()
            }
    
    return ok({
        "deviceId": deviceId,
        "data": latest_data,
        "timestamp": datetime.utcnow().isoformat()
    })


@router.get("/anomalies")
def detect_anomalies(
    deviceId: int,
    indicator: str,
    hours: int = 24,
    cu: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    异常检测
    对齐现网：设备预警功能
    
    现网交互：
    1. 系统定时任务调用此接口
    2. 检测过去N小时的数据异常
    3. 发现异常触发告警
    """
    device = db.get(IotDevice, deviceId)
    if not device:
        raise ApiError(40400, "设备不存在", 404)
    
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    
    # 获取历史数据
    data = db.scalars(
        select(TsTelemetry)
        .where(
            TsTelemetry.device_id == deviceId,
            TsTelemetry.point_code == indicator,
            TsTelemetry.occurred_at >= start_time,
            TsTelemetry.occurred_at <= end_time,
            TsTelemetry.deleted == 0
        )
        .order_by(TsTelemetry.occurred_at)
    ).all()
    
    if len(data) < 10:
        return ok({
            "anomalies": [],
            "message": "数据不足，无法检测异常",
            "stats": None
        })
    
    # 计算统计特征
    values = [float(d.point_value) for d in data]
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    std = variance ** 0.5
    
    # 异常检测（Z-score > 2）
    anomalies = []
    for d in data:
        value = float(d.point_value)
        z_score = abs(value - mean) / std if std > 0 else 0
        if z_score > 2.0:
            anomalies.append({
                "time": d.occurred_at.isoformat(),
                "value": round(value, 2),
                "zScore": round(z_score, 2),
                "type": "HIGH" if value > mean else "LOW"
            })
    
    return ok({
        "anomalies": anomalies,
        "stats": {
            "mean": round(mean, 2),
            "std": round(std, 2),
            "min": round(min(values), 2),
            "max": round(max(values), 2),
            "count": len(data)
        },
        "threshold": {
            "lower": round(mean - 2 * std, 2),
            "upper": round(mean + 2 * std, 2)
        }
    })


@router.get("/statistics")
def get_statistics(
    deviceId: int,
    indicator: str,
    startTime: str,
    endTime: str,
    cu: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    统计分析
    对齐现网：水质数据导出
    
    现网交互：
    1. 用户选择时间范围
    2. 调用此接口获取统计数据
    3. 前端展示统计卡片
    4. 支持导出为CSV
    """
    device = db.get(IotDevice, deviceId)
    if not device:
        raise ApiError(40400, "设备不存在", 404)
    
    start_dt = datetime.fromisoformat(startTime)
    end_dt = datetime.fromisoformat(endTime)
    
    data = db.scalars(
        select(TsTelemetry)
        .where(
            TsTelemetry.device_id == deviceId,
            TsTelemetry.point_code == indicator,
            TsTelemetry.occurred_at >= start_dt,
            TsTelemetry.occurred_at <= end_dt,
            TsTelemetry.deleted == 0
        )
        .order_by(TsTelemetry.occurred_at)
    ).all()
    
    if not data:
        return ok({
            "indicator": indicator,
            "count": 0,
            "message": "无数据"
        })
    
    values = [float(d.point_value) for d in data]
    
    # 计算统计值
    mean = sum(values) / len(values)
    sorted_values = sorted(values)
    n = len(values)
    
    # 百分位数
    p10 = sorted_values[int(n * 0.1)]
    p50 = sorted_values[int(n * 0.5)]
    p90 = sorted_values[int(n * 0.9)]
    
    # 标准差
    variance = sum((v - mean) ** 2 for v in values) / n
    std = variance ** 0.5
    
    return ok({
        "indicator": indicator,
        "count": n,
        "mean": round(mean, 2),
        "std": round(std, 2),
        "min": round(min(values), 2),
        "max": round(max(values), 2),
        "percentiles": {
            "p10": round(p10, 2),
            "p50": round(p50, 2),
            "p90": round(p90, 2)
        },
        "firstTime": data[0].occurred_at.isoformat(),
        "lastTime": data[-1].occurred_at.isoformat()
    })
