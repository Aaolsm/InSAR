from pathlib import Path
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[1]
#输入 原矢量
insar_path = ROOT / "data" / "raw" / "los" / "Kowloon_TSX_LOS_tem.shp"
building_path = ROOT / "data" / "raw" / "buildings" / "ESRI Shapefile_building.shp"
insar_gdf = gpd.read_file(insar_path)
building_gdf = gpd.read_file(building_path)

#输出
interim_dir = ROOT / "data" / "interim"
fig_dir = ROOT / "outputs" / "figures"

#范围
minx = 114.1226400
miny = 22.3573086
maxx = 114.1293529
maxy = 22.3631452
study_area_geom =  box(minx, miny, maxx, maxy)
study_area = gpd.GeoDataFrame(
    {"name" : ["研究区域"]},
    geometry=[study_area_geom],
    crs="EPSG:4326"
)
insar_bbox = insar_gdf.cx[minx:maxx, miny:maxy]    #极速粗筛,building已为固定范围

#范围对齐
insar_clip = gpd.clip(insar_bbox, study_area)
building_clip = gpd.clip(building_gdf, study_area)

#输出中转暂存
study_area.to_file(interim_dir / "study_area.geojson", driver="GeoJSON")
insar_clip.to_file(interim_dir / "insar_clip.gpkg", driver="GPKG")
building_clip.to_file(interim_dir / "buildings_clip.gpkg", driver="GPKG")

#信息展示
print("研究范围: ",study_area.total_bounds, "\nCRS: ", insar_clip.crs)
print(f"InSAR点位信息结果\n点量: {len(insar_clip)}")
print("建筑信息结果\n数量: ", len(building_clip))

#图览
fig, ax = plt.subplots(figsize=(8, 8))
building_clip.plot(ax=ax, facecolor="none", edgecolor="black", linewidth=0.8)
insar_clip.plot(ax=ax, markersize=1)
study_area.boundary.plot(ax=ax, linewidth=1.2)
          
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False
plt.title("预览")
plt.xlabel("经度")
plt.ylabel("纬度")
plt.tight_layout()
plt.savefig(fig_dir / "02_裁剪预览图.png", dpi=300)
plt.show()