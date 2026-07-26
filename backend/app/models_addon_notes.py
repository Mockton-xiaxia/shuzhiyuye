# BizPond 模型需要添加的GIS字段说明

# 在现有的 BizPond 类中添加以下字段：

class BizPond(Base, TimestampMixin):
    __tablename__ = "biz_pond"
    
    # ... 原有字段 ...
    
    # === GIS 增强字段 ===
    geom_wkt: Mapped[Optional[str]] = mapped_column(Text)  # WKT格式
    geom_version: Mapped[int] = mapped_column(Integer, default=1)
    
    # 包围盒（空间索引粗筛）
    bbox_min_lng: Mapped[Optional[float]] = mapped_column(Float)
    bbox_max_lng: Mapped[Optional[float]] = mapped_column(Float)
    bbox_min_lat: Mapped[Optional[float]] = mapped_column(Float)
    bbox_max_lat: Mapped[Optional[float]] = mapped_column(Float)
    
    # 中心点
    center_lng: Mapped[Optional[float]] = mapped_column(Float)
    center_lat: Mapped[Optional[float]] = mapped_column(Float)
    
    # 后端计算的面积
    area_mu_calc: Mapped[Optional[float]] = mapped_column(Numeric(18, 2))
