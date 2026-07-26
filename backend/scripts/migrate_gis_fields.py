"""
数据库迁移：添加 GIS 增强字段
执行方式：cd backend && uv run python scripts/migrate_gis_fields.py
"""
import sys
sys.path.insert(0, '.')

from sqlalchemy import text
from app.db import SessionLocal


def migrate():
    """添加 GIS 增强字段到 biz_pond 表"""
    
    db = SessionLocal()
    
    try:
        # 检查字段是否已存在
        result = db.execute(text("PRAGMA table_info(biz_pond)")).fetchall()
        columns = [row[1] for row in result]
        
        print("当前 biz_pond 表字段：", columns)
        
        # 需要添加的字段
        new_columns = [
            ("geom_wkt", "TEXT"),
            ("geom_version", "INTEGER DEFAULT 1"),
            ("bbox_min_lng", "FLOAT"),
            ("bbox_max_lng", "FLOAT"),
            ("bbox_min_lat", "FLOAT"),
            ("bbox_max_lat", "FLOAT"),
            ("center_lng", "FLOAT"),
            ("center_lat", "FLOAT"),
            ("area_mu_calc", "NUMERIC(18,2)"),
        ]
        
        # 逐个添加字段
        for col_name, col_type in new_columns:
            if col_name not in columns:
                print(f"添加字段：{col_name} {col_type}")
                db.execute(text(f"ALTER TABLE biz_pond ADD COLUMN {col_name} {col_type}"))
            else:
                print(f"字段已存在：{col_name}")
        
        db.commit()
        print("数据库迁移完成！")
        
    except Exception as e:
        print(f"迁移失败：{str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate()
