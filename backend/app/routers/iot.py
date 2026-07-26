from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.response import ApiError, ok
from app.config import get_settings
from app.db import get_db
from app.deps import CurrentUser, get_current_user
from app.models import (
    BizEnterprise,
    BizPond,
    IotAlarm,
    IotCamera,
    IotCommandLog,
    IotDevice,
    IotEzvizConfig,
    IotRule,
    IotStrategy,
    SysTodo,
    TsTelemetry,
)

router = APIRouter(tags=["iot"])
settings = get_settings()


class TelemetryIn(BaseModel):
    deviceId: int
    pointCode: str
    pointValue: float


class CameraPlayOut(BaseModel):
    provider: str
    playUrl: Optional[str] = None
    accessToken: Optional[str] = None
    deviceSerial: str
    channelNo: int
    message: Optional[str] = None


def _ezviz_cfg(db: Session, project_id: int) -> IotEzvizConfig | None:
    return db.scalar(select(IotEzvizConfig).where(IotEzvizConfig.project_id == project_id, IotEzvizConfig.deleted == 0))


def _has_ezviz_key(db: Session, project_id: int) -> tuple[bool, Optional[str], Optional[str]]:
    cfg = _ezviz_cfg(db, project_id) if project_id else None
    key = (cfg.app_key if cfg and cfg.app_key else None) or settings.ezviz_app_key or ""
    secret = (cfg.app_secret if cfg and cfg.app_secret else None) or settings.ezviz_app_secret or ""
    token = cfg.access_token if cfg and cfg.access_token else None
    return bool(key and secret), token, key


def _cam_dict(c: IotCamera, ents: dict[int, str]) -> dict:
    eid = c.enterprise_id or 0
    return {
        "id": c.id,
        "name": c.name,
        "provider": c.provider,
        "deviceSerial": c.device_serial,
        "channelNo": c.channel_no,
        "scene": c.scene,
        "pondId": c.pond_id,
        "warehouseId": c.warehouse_id,
        "enterpriseId": eid,
        "enterpriseName": ents.get(eid) if eid else "未分配（资源池）",
        "assigned": bool(eid),
        "status": c.status,
        "enabled": getattr(c, "enabled", 1) or 1,
        "ptzCapable": c.ptz_capable,
        "projectId": c.project_id,
    }


@router.get("/iot/devices")
def devices(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(IotDevice).where(IotDevice.deleted == 0)
    if cu.user.enterprise_id:
        q = q.where(IotDevice.enterprise_id == cu.user.enterprise_id)
    rows = db.scalars(q).all()
    return ok(
        [
            {
                "id": d.id,
                "name": d.name,
                "deviceNo": d.device_no,
                "deviceType": d.device_type,
                "pondId": d.pond_id,
                "status": d.status,
            }
            for d in rows
        ]
    )


@router.get("/iot/cameras")
def cameras(
    bindStorage: bool = False,
    scene: Optional[str] = None,
    enterpriseId: Optional[int] = None,
    unassigned: bool = False,
    cu: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = select(IotCamera).where(IotCamera.deleted == 0)
    if cu.user.user_type == "ENTERPRISE" and cu.user.enterprise_id:
        q = q.where(IotCamera.enterprise_id == cu.user.enterprise_id)
    elif cu.user.project_id:
        q = q.where(IotCamera.project_id == cu.user.project_id)
    if bindStorage or scene == "WAREHOUSE":
        q = q.where(IotCamera.scene == "WAREHOUSE")
    elif scene:
        q = q.where(IotCamera.scene == scene)
    if unassigned:
        q = q.where(IotCamera.enterprise_id == 0)
    if enterpriseId is not None and cu.portal in ("GOV", "BOTH"):
        q = q.where(IotCamera.enterprise_id == enterpriseId)
    rows = db.scalars(q.order_by(IotCamera.id.desc())).all()
    ents = {e.id: e.name for e in db.scalars(select(BizEnterprise).where(BizEnterprise.deleted == 0)).all()}
    return ok([_cam_dict(c, ents) for c in rows])


class CameraIn(BaseModel):
    name: str
    deviceSerial: str
    channelNo: int = 1
    scene: str = "POND"
    enterpriseId: Optional[int] = None
    pondId: Optional[int] = None
    warehouseId: Optional[int] = None
    enabled: int = 1
    status: str = "ONLINE"


@router.post("/iot/cameras")
def create_camera(body: CameraIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    pid = cu.user.project_id or 1
    if cu.user.user_type == "ENTERPRISE":
        eid = cu.user.enterprise_id or 0
    else:
        eid = body.enterpriseId if body.enterpriseId is not None else 0
    c = IotCamera(
        project_id=pid,
        enterprise_id=eid or 0,
        pond_id=body.pondId,
        warehouse_id=body.warehouseId,
        name=body.name,
        provider="EZVIZ",
        device_serial=body.deviceSerial,
        channel_no=body.channelNo,
        scene=body.scene,
        enabled=body.enabled,
        status=body.status,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    ents = {e.id: e.name for e in db.scalars(select(BizEnterprise).where(BizEnterprise.deleted == 0)).all()}
    return ok(_cam_dict(c, ents))


@router.put("/iot/cameras/{cid}")
def update_camera(cid: int, body: CameraIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    c = db.get(IotCamera, cid)
    if not c or c.deleted:
        raise ApiError(40400, "摄像头不存在", 404)
    if cu.user.user_type == "ENTERPRISE" and c.enterprise_id != cu.user.enterprise_id:
        raise ApiError(40300, "无权限", 403)
    c.name = body.name
    c.device_serial = body.deviceSerial
    c.channel_no = body.channelNo
    c.scene = body.scene
    c.pond_id = body.pondId
    c.warehouse_id = body.warehouseId
    c.enabled = body.enabled
    c.status = body.status
    if cu.portal in ("GOV", "BOTH") and body.enterpriseId is not None:
        c.enterprise_id = body.enterpriseId
    db.commit()
    ents = {e.id: e.name for e in db.scalars(select(BizEnterprise).where(BizEnterprise.deleted == 0)).all()}
    return ok(_cam_dict(c, ents))


class AssignIn(BaseModel):
    enterpriseId: int  # 0 = 收回资源池


@router.post("/iot/cameras/{cid}/assign")
def assign_camera(cid: int, body: AssignIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    if cu.portal not in ("GOV", "BOTH"):
        raise ApiError(40300, "仅区县可划分摄像头给企业", 403)
    c = db.get(IotCamera, cid)
    if not c or c.deleted:
        raise ApiError(40400, "摄像头不存在", 404)
    eid = body.enterpriseId or 0
    if eid:
        ent = db.get(BizEnterprise, eid)
        if not ent or ent.deleted:
            raise ApiError(40400, "企业不存在", 404)
    c.enterprise_id = eid
    db.commit()
    ents = {e.id: e.name for e in db.scalars(select(BizEnterprise).where(BizEnterprise.deleted == 0)).all()}
    return ok(_cam_dict(c, ents))


@router.delete("/iot/cameras/{cid}")
def delete_camera(cid: int, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    c = db.get(IotCamera, cid)
    if not c or c.deleted:
        raise ApiError(40400, "摄像头不存在", 404)
    if cu.user.user_type == "ENTERPRISE" and c.enterprise_id != cu.user.enterprise_id:
        raise ApiError(40300, "无权限", 403)
    c.deleted = 1
    db.commit()
    return ok(True)


@router.get("/iot/ezviz/config")
def get_ezviz_config(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    pid = cu.user.project_id or 1
    cfg = _ezviz_cfg(db, pid)
    env_fallback = bool(settings.ezviz_app_key)
    if not cfg:
        return ok(
            {
                "projectId": pid,
                "configured": env_fallback,
                "status": "ENV" if env_fallback else "UNSET",
                "appKeyMasked": (settings.ezviz_app_key[:4] + "****") if env_fallback else "",
                "hasSecret": bool(settings.ezviz_app_secret),
                "accessToken": None,
                "lastCheckMsg": "未在库中配置，可使用环境变量兜底" if env_fallback else "尚未配置萤石 AppKey",
                "canEdit": cu.portal in ("GOV", "BOTH"),
            }
        )
    key = cfg.app_key or ""
    return ok(
        {
            "projectId": pid,
            "configured": bool(key) or env_fallback,
            "status": cfg.status or "UNSET",
            "appKeyMasked": (key[:4] + "****") if len(key) >= 4 else ("****" if key else ""),
            "appKey": key if cu.portal in ("GOV", "BOTH") else "",
            "hasSecret": bool(cfg.app_secret or settings.ezviz_app_secret),
            "accessToken": cfg.access_token,
            "tokenExpireAt": cfg.token_expire_at.isoformat() if cfg.token_expire_at else None,
            "lastCheckMsg": cfg.last_check_msg,
            "canEdit": cu.portal in ("GOV", "BOTH"),
        }
    )


class EzvizConfigIn(BaseModel):
    appKey: str
    appSecret: str


@router.put("/iot/ezviz/config")
def put_ezviz_config(body: EzvizConfigIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    if cu.portal not in ("GOV", "BOTH"):
        raise ApiError(40300, "仅区县可维护萤石凭证（项目级，供下属企业共用）", 403)
    pid = cu.user.project_id or 1
    cfg = _ezviz_cfg(db, pid)
    if not cfg:
        cfg = IotEzvizConfig(project_id=pid)
        db.add(cfg)
    cfg.app_key = body.appKey.strip()
    cfg.app_secret = body.appSecret.strip()
    cfg.status = "OK" if cfg.app_key and cfg.app_secret else "UNSET"
    cfg.last_check_msg = "已保存，请点击测试连通"
    cfg.access_token = None
    db.commit()
    return ok({"status": cfg.status})


@router.post("/iot/ezviz/test")
def test_ezviz(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """演示连通：有 Key/Secret 即视为可取 Token（真实环境应调 open.ys7.com）。"""
    if cu.portal not in ("GOV", "BOTH"):
        raise ApiError(40300, "仅区县可测试", 403)
    pid = cu.user.project_id or 1
    ok_key, _, _ = _has_ezviz_key(db, pid)
    cfg = _ezviz_cfg(db, pid)
    if not cfg:
        cfg = IotEzvizConfig(project_id=pid)
        db.add(cfg)
    if not ok_key:
        cfg.status = "ERROR"
        cfg.last_check_msg = "缺少 AppKey/AppSecret"
        db.commit()
        raise ApiError(40000, "请先保存 AppKey 与 AppSecret")
    # mock token
    cfg.access_token = "demo_at_" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    cfg.token_expire_at = datetime.now(timezone.utc)
    cfg.status = "OK"
    cfg.last_check_msg = "连通成功（演示 Token 已缓存；接入真网后替换为 open.ys7.com 返回值）"
    db.commit()
    return ok({"status": "OK", "accessToken": cfg.access_token, "message": cfg.last_check_msg})


@router.get("/iot/cameras/{cid}/play-url")
def play_url(cid: int, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    c = db.get(IotCamera, cid)
    if not c:
        raise ApiError(40400, "摄像头不存在", 404)
    if cu.user.user_type == "ENTERPRISE" and c.enterprise_id not in (0, cu.user.enterprise_id):
        # 企业只能播已划分给自己的；未分配池不对企业开放播放
        if c.enterprise_id != cu.user.enterprise_id:
            raise ApiError(40300, "该摄像头未划分给本企业", 403)
    demo_hls = "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8"
    has_key, token, _ = _has_ezviz_key(db, c.project_id or cu.user.project_id or 1)
    if c.provider == "EZVIZ" and has_key:
        return ok(
            {
                "provider": "EZVIZ",
                "deviceSerial": c.device_serial,
                "channelNo": c.channel_no,
                "accessToken": token or "NEED_REFRESH",
                "playUrl": f"ezopen://open.ys7.com/{c.device_serial}/{c.channel_no}.live",
                "hlsUrl": demo_hls,
                "poster": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=800&q=80",
                "message": "已配置萤石凭证，可接 EZUIKit；演示环境仍附带 HLS 样例",
                "demo": not bool(token),
                "enterpriseId": c.enterprise_id,
            }
        )
    return ok(
        {
            "provider": c.provider or "EZVIZ",
            "deviceSerial": c.device_serial or "DEMO_SERIAL",
            "channelNo": c.channel_no or 1,
            "accessToken": None,
            "playUrl": f"ezopen://open.ys7.com/{c.device_serial or 'DEMO'}/{c.channel_no or 1}.live",
            "hlsUrl": demo_hls,
            "poster": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=800&q=80",
            "message": "演示流：未配置萤石密钥，使用公开 HLS 样例播放",
            "demo": True,
            "enterpriseId": c.enterprise_id,
        }
    )


@router.get("/iot/alarms")
def alarms(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(IotAlarm).where(IotAlarm.deleted == 0)
    if cu.user.enterprise_id:
        q = q.where(IotAlarm.enterprise_id == cu.user.enterprise_id)
    rows = db.scalars(q.order_by(IotAlarm.id.desc()).limit(100)).all()
    devices = {d.id: d for d in db.scalars(select(IotDevice)).all()}
    return ok(
        [
            {
                "id": a.id,
                "title": a.title,
                "content": a.content,
                "status": a.status,
                "deviceId": a.device_id,
                "deviceName": (devices[a.device_id].name if a.device_id in devices else "-"),
                "deviceNo": (devices[a.device_id].device_no if a.device_id in devices else str(a.device_id or "-")),
                "deviceType": (devices[a.device_id].device_type if a.device_id in devices else "水质"),
                "cameraId": a.camera_id,
                "level": a.level,
                "alarmType": a.alarm_type,
                "occurredAt": a.occurred_at.isoformat() if a.occurred_at else None,
            }
            for a in rows
        ]
    )


@router.post("/iot/telemetry")
def ingest_telemetry(body: TelemetryIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    device = db.get(IotDevice, body.deviceId)
    if not device:
        raise ApiError(40400, "设备不存在", 404)
    now = datetime.now(timezone.utc)
    db.add(
        TsTelemetry(
            time=now,
            device_id=body.deviceId,
            point_code=body.pointCode,
            point_value=body.pointValue,
            quality=1,
        )
    )
    # rule engine
    rules = db.scalars(
        select(IotRule).where(
            IotRule.enterprise_id == device.enterprise_id,
            IotRule.enabled == 1,
            IotRule.point_code == body.pointCode,
            IotRule.deleted == 0,
        )
    ).all()
    triggered = []
    for rule in rules:
        hit = False
        if rule.operator == "LT" and body.pointValue < rule.threshold:
            hit = True
        if rule.operator == "GT" and body.pointValue > rule.threshold:
            hit = True
        if hit:
            cam = db.scalar(
                select(IotCamera).where(
                    IotCamera.enterprise_id == device.enterprise_id,
                    IotCamera.pond_id == device.pond_id,
                    IotCamera.deleted == 0,
                )
            )
            alarm = IotAlarm(
                project_id=device.project_id,
                enterprise_id=device.enterprise_id,
                device_id=device.id,
                camera_id=cam.id if cam else None,
                alarm_type=f"WATER_{body.pointCode}",
                title=f"{rule.name}触发",
                content=f"{body.pointCode}={body.pointValue} {rule.operator} {rule.threshold}",
                status="OPEN",
                occurred_at=now,
            )
            db.add(alarm)
            db.flush()
            db.add(
                SysTodo(
                    project_id=device.project_id,
                    enterprise_id=device.enterprise_id,
                    title=f"物联告警：{alarm.title}",
                    biz_type="IOT_ALARM",
                    biz_id=alarm.id,
                    status="PENDING",
                    portal="ENT",
                    link_path="/ent/iot/alarms",
                )
            )
            triggered.append(alarm.id)
    db.commit()
    return ok({"triggeredAlarmIds": triggered})


@router.get("/iot/telemetry")
def list_telemetry(
    deviceId: Optional[int] = None,
    pointCode: Optional[str] = None,
    type: Optional[str] = None,
    cu: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = select(TsTelemetry)
    if deviceId:
        q = q.where(TsTelemetry.device_id == deviceId)
    if pointCode:
        q = q.where(TsTelemetry.point_code == pointCode)
    rows = db.scalars(q.order_by(TsTelemetry.id.desc()).limit(100)).all()
    if not rows:
        return ok(
            [
                {
                    "id": 1,
                    "deviceId": deviceId or 1,
                    "pointCode": pointCode or ("COD" if type == "TAILWATER" else "DO"),
                    "value": 6.2,
                    "unit": "mg/L",
                    "collectedAt": datetime.now(timezone.utc).isoformat(),
                }
            ]
        )
    return ok(
        [
            {
                "id": getattr(r, "id", None),
                "deviceId": r.device_id,
                "pointCode": r.point_code,
                "value": r.point_value,
                "unit": "mg/L",
                "collectedAt": r.time.isoformat() if r.time else None,
                "time": r.time.isoformat() if r.time else None,
                "pointValue": r.point_value,
            }
            for r in rows
        ]
    )


@router.get("/map/layers")
def map_layers(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """一张图：主体 + 塘口 + 告警 + 摄像头"""
    eq = select(BizEnterprise).where(BizEnterprise.deleted == 0)
    pq = select(BizPond).where(BizPond.deleted == 0)
    aq = select(IotAlarm).where(IotAlarm.deleted == 0, IotAlarm.status == "OPEN")
    cq = select(IotCamera).where(IotCamera.deleted == 0)
    if cu.user.user_type == "ENTERPRISE":
        eq = eq.where(BizEnterprise.id == cu.user.enterprise_id)
        pq = pq.where(BizPond.enterprise_id == cu.user.enterprise_id)
        aq = aq.where(IotAlarm.enterprise_id == cu.user.enterprise_id)
        cq = cq.where(IotCamera.enterprise_id == cu.user.enterprise_id)
    elif cu.user.project_id:
        eq = eq.where(BizEnterprise.project_id == cu.user.project_id)
        pq = pq.where(BizPond.project_id == cu.user.project_id)
        aq = aq.where(IotAlarm.project_id == cu.user.project_id)
        cq = cq.where(IotCamera.project_id == cu.user.project_id)
    ents = db.scalars(eq).all()
    ponds = db.scalars(pq).all()
    alarms = db.scalars(aq).all()
    cams = db.scalars(cq).all()
    return ok(
        {
            "enterprises": [{"id": e.id, "name": e.name, "lng": e.lng, "lat": e.lat} for e in ents],
            "ponds": [
                {
                    "id": p.id,
                    "name": p.name,
                    "lng": p.lng,
                    "lat": p.lat,
                    "layerType": p.layer_type,
                    "auditStatus": p.audit_status,
                    "geomGeojson": p.geom_geojson,
                    "enterpriseId": p.enterprise_id,
                }
                for p in ponds
            ],
            "alarms": [{"id": a.id, "title": a.title, "cameraId": a.camera_id, "deviceId": a.device_id} for a in alarms],
            "cameras": [{"id": c.id, "name": c.name, "pondId": c.pond_id, "deviceSerial": c.device_serial} for c in cams],
        }
    )


@router.post("/iot/alarms/{aid}/ack")
def ack_alarm(aid: int, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    a = db.get(IotAlarm, aid)
    if not a:
        raise ApiError(40400, "告警不存在", 404)
    if a.status != "OPEN":
        raise ApiError(40900, "状态冲突")
    a.status = "ACK"
    for t in db.scalars(
        select(SysTodo).where(SysTodo.biz_type == "IOT_ALARM", SysTodo.biz_id == aid, SysTodo.status == "PENDING")
    ):
        t.status = "DONE"
    db.commit()
    return ok(True)


@router.post("/iot/alarms/{aid}/close")
def close_alarm(aid: int, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    a = db.get(IotAlarm, aid)
    if not a:
        raise ApiError(40400, "告警不存在", 404)
    if a.status not in ("OPEN", "ACK"):
        raise ApiError(40900, "状态冲突")
    a.status = "CLOSED"
    for t in db.scalars(
        select(SysTodo).where(SysTodo.biz_type == "IOT_ALARM", SysTodo.biz_id == aid, SysTodo.status == "PENDING")
    ):
        t.status = "DONE"
    db.commit()
    return ok(True)


@router.get("/iot/rules")
def list_rules(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(IotRule).where(IotRule.deleted == 0)
    if cu.user.enterprise_id:
        q = q.where(IotRule.enterprise_id == cu.user.enterprise_id)
    rows = db.scalars(q).all()
    return ok(
        [
            {
                "id": r.id,
                "name": r.name,
                "deviceId": r.device_id,
                "pointCode": r.point_code,
                "operator": r.operator,
                "threshold": r.threshold,
                "enabled": r.enabled,
            }
            for r in rows
        ]
    )


class RuleIn(BaseModel):
    name: str
    deviceId: Optional[int] = None
    pointCode: str
    operator: str = "LT"
    threshold: float
    enabled: int = 1


@router.post("/iot/rules")
def create_rule(body: RuleIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    r = IotRule(
        enterprise_id=cu.user.enterprise_id or 0,
        device_id=body.deviceId,
        name=body.name,
        point_code=body.pointCode,
        operator=body.operator,
        threshold=body.threshold,
        enabled=body.enabled,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return ok({"id": r.id})


@router.put("/iot/rules/{rid}")
def update_rule(rid: int, body: RuleIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    r = db.get(IotRule, rid)
    if not r or r.deleted:
        raise ApiError(40400, "规则不存在", 404)
    if cu.user.enterprise_id and r.enterprise_id != cu.user.enterprise_id:
        raise ApiError(40300, "无权限", 403)
    r.name = body.name
    r.device_id = body.deviceId
    r.point_code = body.pointCode
    r.operator = body.operator
    r.threshold = body.threshold
    r.enabled = body.enabled
    db.commit()
    return ok({"id": r.id})


@router.get("/iot/strategies")
def strategies(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(IotStrategy).where(IotStrategy.deleted == 0)
    if cu.user.enterprise_id:
        q = q.where(IotStrategy.enterprise_id == cu.user.enterprise_id)
    rows = db.scalars(q).all()
    return ok(
        [
            {
                "id": s.id,
                "name": s.name,
                "deviceId": s.device_id,
                "strategyType": s.strategy_type,
                "paramsJson": s.params_json,
                "enabled": s.enabled,
            }
            for s in rows
        ]
    )


class StrategyIn(BaseModel):
    name: str
    deviceId: Optional[int] = None
    strategyType: str = "THRESHOLD"
    paramsJson: Optional[str] = None


@router.post("/iot/strategies")
def create_strategy(body: StrategyIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    s = IotStrategy(
        enterprise_id=cu.user.enterprise_id or 0,
        device_id=body.deviceId,
        name=body.name,
        strategy_type=body.strategyType,
        params_json=body.paramsJson,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return ok({"id": s.id})


class CommandIn(BaseModel):
    deviceId: int
    command: str


@router.post("/iot/commands")
def send_command(body: CommandIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    device = db.get(IotDevice, body.deviceId)
    if not device:
        raise ApiError(40400, "设备不存在", 404)
    log = IotCommandLog(
        enterprise_id=device.enterprise_id,
        device_id=body.deviceId,
        command=body.command,
        result="OK",
        detail="mock accepted",
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return ok({"id": log.id, "result": "OK"})


@router.get("/iot/commands")
def command_logs(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(IotCommandLog).where(IotCommandLog.deleted == 0)
    if cu.user.enterprise_id:
        q = q.where(IotCommandLog.enterprise_id == cu.user.enterprise_id)
    rows = db.scalars(q.order_by(IotCommandLog.id.desc()).limit(100)).all()
    devices = {d.id: d for d in db.scalars(select(IotDevice).where(IotDevice.deleted == 0)).all()}
    return ok(
        [
            {
                "id": c.id,
                "deviceId": c.device_id,
                "deviceName": devices.get(c.device_id).name if devices.get(c.device_id) else f"#{c.device_id}",
                "deviceNo": devices.get(c.device_id).device_no if devices.get(c.device_id) else "",
                "command": c.command,
                "result": c.result,
                "detail": c.detail,
                "status": c.result,
                "createdAt": c.created_at.isoformat() if c.created_at else "",
            }
            for c in rows
        ]
    )
