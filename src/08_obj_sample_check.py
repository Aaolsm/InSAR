from pathlib import Path

import geopandas as gpd
import numpy as np
import open3d as o3d
import pandas as pd
from shapely.geometry import box


ROOT = Path(__file__).resolve().parent.parent


def read_obj_bbox(obj_path: Path):
    """
    读取单个 obj，返回包围盒和基础几何信息
    """
    mesh = o3d.io.read_triangle_mesh(str(obj_path))

    if mesh is None:
        return None

    vertices = np.asarray(mesh.vertices)
    triangles = np.asarray(mesh.triangles)

    if vertices.size == 0:
        return None

    min_xyz = vertices.min(axis=0)
    max_xyz = vertices.max(axis=0)

    minx, miny, minz = min_xyz
    maxx, maxy, maxz = max_xyz

    length = maxx - minx
    width = maxy - miny
    height = maxz - minz
    bbox_area = length * width
    bbox_volume = length * width * height

    # 2D bbox polygon（XY 平面）
    geom = box(minx, miny, maxx, maxy)

    return {
        "obj_name": obj_path.name,
        "obj_stem": obj_path.stem,
        "vertex_count": int(len(vertices)),
        "triangle_count": int(len(triangles)),
        "minx": float(minx),
        "miny": float(miny),
        "minz": float(minz),
        "maxx": float(maxx),
        "maxy": float(maxy),
        "maxz": float(maxz),
        "bbox_length": float(length),
        "bbox_width": float(width),
        "height": float(height),
        "bbox_area": float(bbox_area),
        "bbox_volume": float(bbox_volume),
        "geometry": geom,
    }


def main():
    # =========================
    # 1. 路径
    # =========================
    obj_dir = ROOT / "data" / "raw" / "obj" / "obj"
    out_dir = ROOT / "data" / "interim"
    out_dir.mkdir(parents=True, exist_ok=True)

    # =========================
    # 2. 抽样数量
    # 先不要太大，先测 20 个
    # =========================
    sample_n = 20
    obj_files = sorted(obj_dir.glob("*.obj"))[:sample_n]

    if len(obj_files) == 0:
        raise FileNotFoundError(f"未在目录中找到 obj 文件: {obj_dir}")

    # =========================
    # 3. 逐个读取
    # =========================
    records = []
    failed = []

    for obj_path in obj_files:
        try:
            result = read_obj_bbox(obj_path)
            if result is None:
                failed.append(obj_path.name)
            else:
                records.append(result)
        except Exception as e:
            failed.append(f"{obj_path.name} | {repr(e)}")

    if len(records) == 0:
        raise RuntimeError("抽样 obj 全部读取失败，请检查 open3d 或 obj 数据。")

    # =========================
    # 4. 转成 GeoDataFrame
    # 注意：此处假定 obj 坐标系是 HK80 / EPSG:2326
    # =========================
    gdf = gpd.GeoDataFrame(records, geometry="geometry", crs="EPSG:2326")

    out_path = out_dir / "obj_sample_bbox_check.gpkg"
    gdf.to_file(out_path, driver="GPKG")

    # =========================
    # 5. 打印汇总
    # =========================
    print("=== obj 抽样读取检查完成 ===")
    print("obj 目录:", obj_dir)
    print("抽样数量:", len(obj_files))
    print("成功读取:", len(records))
    print("读取失败:", len(failed))
    print("输出文件:", out_path)

    print("\n=== 坐标范围统计 ===")
    print("minx 范围:", round(float(gdf["minx"].min()), 3), "~", round(float(gdf["minx"].max()), 3))
    print("miny 范围:", round(float(gdf["miny"].min()), 3), "~", round(float(gdf["miny"].max()), 3))
    print("minz 范围:", round(float(gdf["minz"].min()), 3), "~", round(float(gdf["minz"].max()), 3))
    print("maxx 范围:", round(float(gdf["maxx"].min()), 3), "~", round(float(gdf["maxx"].max()), 3))
    print("maxy 范围:", round(float(gdf["maxy"].min()), 3), "~", round(float(gdf["maxy"].max()), 3))
    print("maxz 范围:", round(float(gdf["maxz"].min()), 3), "~", round(float(gdf["maxz"].max()), 3))

    print("\n=== 高度统计 ===")
    print("height 最小值:", round(float(gdf["height"].min()), 3))
    print("height 中位数:", round(float(gdf["height"].median()), 3))
    print("height 最大值:", round(float(gdf["height"].max()), 3))

    print("\n=== bbox 长宽统计 ===")
    print("bbox_length 中位数:", round(float(gdf["bbox_length"].median()), 3))
    print("bbox_width 中位数:", round(float(gdf["bbox_width"].median()), 3))

    print("\n=== 前10个样本 ===")
    preview_cols = [
        "obj_name",
        "vertex_count",
        "triangle_count",
        "minx",
        "miny",
        "minz",
        "maxx",
        "maxy",
        "maxz",
        "height",
        "bbox_length",
        "bbox_width",
    ]
    print(gdf[preview_cols].head(10).to_string(index=False))

    if failed:
        print("\n=== 失败样本 ===")
        for item in failed[:10]:
            print(item)


if __name__ == "__main__":
    main()