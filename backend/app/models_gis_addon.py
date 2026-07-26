"""
数据库模型：BizPond 表 GIS 字段增强
"""
# 在 models.py 的 BizPond 类中添加以下字段：

# GIS 增强字段
geom_wkt: Mapped[Optional[str]] = mapped_column(Text)  # WKT格式，数据库存储
geom_version: Mapped[int] = mapped_column(Integer, default=1)  # 版本控制

# 包围盒（用于空间索引粗筛）
bbox_min_lng: Mapped[Optional[float]] = mapped_column(Float)
bbox_max_lng: Mapped[Optional[float]] = mapped_column(Float)
bbox_min_lat: Mapped[Optional[float]] = mapped_column(Float)
bbox_max_lat: Mapped[Optional[float]] = mapped_column(Float)

# 中心点
center_lng: Mapped[Optional[float]] = mapped_column(Float)
center_lat: Mapped[Optional[float]] = mapped_column(Float)

# 后端计算的面积（校验用）
area_mu_calc: Mapped[Optional[float]] = mapped_column(Numeric(18, 2))
