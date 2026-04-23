from pathlib import Path
import geopandas as gpd 
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]

#输入 裁剪后矢量
insar_clip_path = ROOT / "data" / "interim" / "insar_clip.gpkg"
building_clip_path = ROOT / "data" / "interim" / "buildings_clip.gpkg"
insar_gdf = gpd.read_file(insar_clip_path)
building_gdf = gpd.read_file(building_clip_path)

#输出
out_dir = ROOT / "data" / "interim"
fig_dir = ROOT / "outputs" / "figures"

#建筑分类
building_gdf["building_id"] = range(1, len(building_gdf)+1)
building_for_join = building_gdf[["building_id", "geometry"]].copy()

#点位判断及统计
joined = gpd.sjoin(insar_gdf, building_for_join, how="left", predicate="within")
inside_points = joined[joined["building_id"].notna()].copy()  #筛选, bool
outside_points = joined[joined["building_id"].isna()].copy()
point_count = inside_points.groupby("building_id").size().reset_index(name="insar_point_count")

#更新gdf
building_stats = building_gdf.merge(point_count, on="building_id", how="left")
building_stats["insar_point_count"] = building_stats["insar_point_count"].fillna(0).astype(int)

#interim
inside_points.to_file(out_dir / "insar_points_inside_buildings.gpkg", driver="GPKG")
outside_points.to_file(out_dir / "insar_points_outside_buildings.gpkg", driver="GPKG")
building_stats.to_file(out_dir / "building_point_count_check.gpkg", driver="GPKG")

#信息展示
print(
    "===点位统计===",
    f"总点位数: {len(joined)}",
    f"点位在建筑内数量: {len(inside_points)}",
    f"点位在建筑外数量: {len(outside_points)}",
    f"建筑内点占比: {round(len(inside_points) / len(joined) * 100, 2)}%",
    sep="\n"
)
print(
    "===建筑统计===",
    f"总建筑数: {len(building_stats)}",
    f"有点建筑数: {(building_stats['insar_point_count'] > 0).sum()}",
    f"无点建筑数: {(building_stats['insar_point_count'] == 0).sum()}",
    sep="\n"
)
nonzero = building_stats.loc[building_stats["insar_point_count"] > 0, "insar_point_count"]
print(
    "===数学统计（建筑内点）===",
    f"平均值: {round(nonzero.mean(), 2)}",
    f"中位数: {nonzero.median()}",
    f"最小值: {nonzero.min()}",
    f"最大值: {nonzero.max()}",
    sep="\n"
)

#
fig, ax = plt.subplots(figsize=(8, 8))
inside_points.plot(ax=ax, markersize=1, color="green", label="inside")
outside_points.plot(ax=ax, markersize=1, color="red", label="outside")
building_gdf.boundary.plot(ax=ax, linewidth=0.8)

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False
plt.title("预览")
plt.xlabel("经度")
plt.ylabel("纬度")
plt.tight_layout()
plt.savefig(fig_dir / "03_建筑内点位check.png", dpi=300)
plt.show()





