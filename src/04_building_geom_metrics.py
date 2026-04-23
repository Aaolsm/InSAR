from pathlib import Path
import math
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Polygon, MultiPolygon

ROOT = Path(__file__).resolve().parents[1]  

def get_orientation_from_mrr(geom):     #mrr：Minimum Rotated Rectangle（最小外接旋转矩形）        用最小外接旋转矩形来计算主方向
    if isinstance(geom, MultiPolygon):
        geom = max(geom.geoms, key=lambda g: g.area)
    mrr = geom.minimum_rotated_rectangle
    coords = list(mrr.exterior.coords)
    edges = []
    for i in range(len(coords) - 1):
        x1, y1 = coords[i]
        x2, y2 = coords[i + 1]
        length = math.hypot(x2 - x1, y2 - y1)
        angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
        edges.append((length, angle))
    longest_edge = max(edges, key=lambda e: e[0])
    angle = longest_edge[1]

    if angle < 0:
        angle += 180
    return angle


def main():
    building_clip_path = ROOT / "data" / "interim" / "buildings_clip.gpkg"
    out_dir = ROOT / "data" / "interim"
    fig_dir = ROOT / "outputs" / "figures"

    buildings = gpd.read_file(building_clip_path)
    buildings["geometry"] = buildings["geometry"].buffer(0) 
    buildings["building_id"] = range(1, len(buildings) + 1)
    buildings_hk80 = buildings.to_crs("EPSG:2326")

    buildings_hk80["footprint_area"] = buildings_hk80["geometry"].area
    buildings_hk80["footprint_perimeter"] = buildings_hk80["geometry"].length
    buildings_hk80["area_perimeter_ratio"] = buildings_hk80["footprint_area"] / buildings_hk80["footprint_perimeter"]
    buildings_hk80["orientation"] = buildings_hk80["geometry"].apply(get_orientation_from_mrr)

    out_path = out_dir / "buildings_geom_metrics.gpkg"
    buildings_hk80.to_file(out_path, driver="GPKG")

    print("===建筑多边形指标===")
    print("建筑数量:", len(buildings_hk80))

    print("面积最小值:", round(buildings_hk80["footprint_area"].min(), 3))
    print("面积中位数:", round(buildings_hk80["footprint_area"].median(), 3))
    print("面积最大值:", round(buildings_hk80["footprint_area"].max(), 3))
    print("周长最小值:", round(buildings_hk80["footprint_perimeter"].min(), 3))
    print("周长中位数:", round(buildings_hk80["footprint_perimeter"].median(), 3))
    print("周长最大值:", round(buildings_hk80["footprint_perimeter"].max(), 3))
    print("面积周长比最小值:", round(buildings_hk80["area_perimeter_ratio"].min(), 3))
    print("面积周长比中位数:", round(buildings_hk80["area_perimeter_ratio"].median(), 3))
    print("面积周长比最大值:", round(buildings_hk80["area_perimeter_ratio"].max(), 3))


    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
    plt.rcParams["axes.unicode_minus"] = False
    fig, ax = plt.subplots(figsize=(8,8))
    buildings_hk80.plot(column="footprint_area", ax=ax, legend=True)
    ax.set_title("面积分布")
    plt.tight_layout()
    plt.savefig(fig_dir / "04_面积分布图", dpi=300)    
    plt.show()


if __name__ == "__main__":
    main()