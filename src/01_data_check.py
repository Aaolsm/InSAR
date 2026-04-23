from pathlib import Path
import geopandas as gpd

ROOT = Path(__file__).resolve().parent.parent

insar_path = ROOT / "data" / "raw" / "los" / "Kowloon_TSX_LOS_tem.shp"
building_path = ROOT / "data" / "raw" / "buildings" / "ESRI Shapefile_building.shp"

insar_gdf = gpd.read_file(insar_path)
building_gdf = gpd.read_file(building_path)

print("=== InSAR 数据 ===")
print("文件路径:", insar_path)
print("行数:", len(insar_gdf))
print("CRS:", insar_gdf.crs)
print("几何类型:", insar_gdf.geom_type.unique())
print("字段名:", list(insar_gdf.columns))
print("范围:", insar_gdf.total_bounds)

print("\n=== 建筑轮廓数据 ===")
print("文件路径:", building_path)
print("行数:", len(building_gdf))
print("CRS:", building_gdf.crs)
print("几何类型:", building_gdf.geom_type.unique())
print("字段名:", list(building_gdf.columns))
print("范围:", building_gdf.total_bounds)