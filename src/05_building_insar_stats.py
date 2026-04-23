from pathlib import Path
import geopandas as gpd
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

def main():
    inside_points_path = ROOT / "data" / "interim" / "insar_points_inside_buildings.gpkg"
    buildings_geom_path = ROOT / "data" / "processed" / "buildings_geom_metrics.gpkg"
    out_dir = ROOT / "data" / "processed"

    inside_points = gpd.read_file(inside_points_path)
    buildings_geom = gpd.read_file(buildings_geom_path)

    stats = (
        inside_points.groupby("building_id").agg(
            insar_point_count=("building_id", "size"),
            velocity_mean=("dv(mm/y)", "mean"),
            velocity_median=("dv(mm/y)", "median"),
            velocity_std=("dv(mm/y)", "std"),
            velocity_min=("dv(mm/y)", "min"),
            velocity_max=("dv(mm/y)", "max"),
            height_mean=("height", "mean"),
            t_mean=("t(mm/c)", "mean"),
        )
        .reset_index()
    )
    building_database_v1 = buildings_geom.merge(stats, on="building_id", how="left")
    building_database_v1["insar_point_count"] = building_database_v1["insar_point_count"].fillna(0).astype(int)


    stats_out = out_dir / "building_insar_stats.gpkg"
    db_out = out_dir / "building_database_v1.gpkg"
    stats_gdf = buildings_geom[["building_id", "geometry"]].merge(stats, on="building_id", how="left")
    stats_gdf.to_file(stats_out, driver="GPKG")
    building_database_v1.to_file(db_out, driver="GPKG")


    print("=== 建筑级 InSAR 统计完成 ===")
    print("inside 点数:", len(inside_points))
    print("有统计结果的建筑数:", len(stats))
    print("输出文件1:", stats_out)
    print("输出文件2:", db_out)

    nonzero = building_database_v1[building_database_v1["insar_point_count"] > 0].copy()
    print("\n=== 形变速率统计 ===")
    print("velocity_mean 最小值:", round(float(nonzero["velocity_mean"].min()), 4))
    print("velocity_mean 中位数:", round(float(nonzero["velocity_mean"].median()), 4))
    print("velocity_mean 最大值:", round(float(nonzero["velocity_mean"].max()), 4))

    # 点数最多的前10栋建筑
    top10 = (
        building_database_v1[["building_id", "insar_point_count", "footprint_area", "velocity_mean"]]
        .sort_values(by="insar_point_count", ascending=False)
        .head(10)
    )
    print(top10.to_string(index=False))


if __name__ == "__main__":
    main()