from pathlib import Path
import geopandas as gpd 
import pandas as pd

def main():
    project_root = Path(__file__).resolve().parents[2]
    shp_path = project_root / "data" / "raw" / "los" / "Kowloon_TSX_LOS_tem.shp"
    output_dir = project_root / "outputs" / "tables"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("读取 LOS shp")
    print(f"文件路径{shp_path}")
    if not shp_path.exists():
        print("未找到LOS shp")
        return
    gdf = gpd.read_file(shp_path)    #GeoDataFrame
    print("读取LOS shp完毕")

    print(f"记录数: {len(gdf)}, 坐标系: {gdf.crs}, 几何类型: {gdf.geom_type.unique()}, 边界范围: {gdf.total_bounds}")
    print("字段列表:")
    for col in gdf.columns:
        dtype = "geometry" if col == gdf.geometry.name else str(gdf[col].dtype)     #几何对象/空间位置
        print(f"- {col}: {dtype}")

    print("前五行属性")
    print(gdf.drop(columns="geometry", errors="ignore").head())
    print("前五行几何")
    print(gdf.geometry.head())

if __name__ == "__main__":
    main()



