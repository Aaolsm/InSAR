from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import box


ROOT = Path(__file__).resolve().parent.parent


def read_obj_bbox_fast(obj_path: Path):
    """
    只解析 obj 顶点行: v x y z
    比 open3d 更适合做全量 bbox 扫描
    """
    minx = miny = minz = np.inf
    maxx = maxy = maxz = -np.inf
    vertex_count = 0

    with open(obj_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if not line.startswith("v "):
                continue

            parts = line.strip().split()
            if len(parts) < 4:
                continue

            try:
                x = float(parts[1])
                y = float(parts[2])
                z = float(parts[3])
            except ValueError:
                continue

            vertex_count += 1
            if x < minx: minx = x
            if y < miny: miny = y
            if z < minz: minz = z
            if x > maxx: maxx = x
            if y > maxy: maxy = y
            if z > maxz: maxz = z

    if vertex_count == 0:
        return None

    return {
        "obj_name": obj_path.name,
        "obj_stem": obj_path.stem,
        "vertex_count": int(vertex_count),
        "minx": float(minx),
        "miny": float(miny),
        "minz": float(minz),
        "maxx": float(maxx),
        "maxy": float(maxy),
        "maxz": float(maxz),
        "bbox_length": float(maxx - minx),
        "bbox_width": float(maxy - miny),
        "height": float(maxz - minz),
        "geometry": box(minx, miny, maxx, maxy),
    }


def main():
    obj_dir = ROOT / "data" / "raw" / "obj" / "obj"
    buildings_geom_path = ROOT / "data" / "processed" / "buildings_geom_metrics.gpkg"

    out_dir = ROOT / "data" / "interim"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 研究区建筑范围（HK80）
    bld_gdf = gpd.read_file(buildings_geom_path)
    minx, miny, maxx, maxy = bld_gdf.total_bounds

    # 给一点余量，避免 bbox 边缘误差
    buffer_dist = 50  # 米
    search_minx = minx - buffer_dist
    search_miny = miny - buffer_dist
    search_maxx = maxx + buffer_dist
    search_maxy = maxy + buffer_dist

    obj_files = sorted(obj_dir.glob("*.obj"))
    total_files = len(obj_files)

    records = []
    failed = []
    scanned = 0

    print("=== 开始全量扫描 obj bbox ===")
    print("obj 总数:", total_files)
    print("研究区搜索范围:", (search_minx, search_miny, search_maxx, search_maxy))

    for obj_path in obj_files:
        scanned += 1

        try:
            result = read_obj_bbox_fast(obj_path)
            if result is None:
                failed.append(obj_path.name)
                continue

            # bbox 与研究区范围是否相交
            if not (
                result["maxx"] < search_minx or
                result["minx"] > search_maxx or
                result["maxy"] < search_miny or
                result["miny"] > search_maxy
            ):
                records.append(result)

        except Exception as e:
            failed.append(f"{obj_path.name} | {repr(e)}")

        if scanned % 5000 == 0:
            print(f"已扫描 {scanned}/{total_files}，当前候选数: {len(records)}")

    if len(records) == 0:
        print("\n=== 扫描完成，但未找到研究区候选 obj ===")
        print("这通常意味着：")
        print("1. 当前 obj 数据不覆盖该研究区；或")
        print("2. obj 坐标解释仍有问题；或")
        print("3. 研究区与 obj 不是同一批数据。")
        return

    gdf = gpd.GeoDataFrame(records, geometry="geometry", crs="EPSG:2326")

    out_path = out_dir / "obj_candidates_in_study_area.gpkg"
    gdf.to_file(out_path, driver="GPKG")

    print("\n=== 扫描完成 ===")
    print("总扫描 obj 数:", total_files)
    print("候选 obj 数:", len(gdf))
    print("失败数:", len(failed))
    print("输出文件:", out_path)

    print("\n=== 候选 obj 高度统计 ===")
    print("height 最小值:", round(float(gdf["height"].min()), 3))
    print("height 中位数:", round(float(gdf["height"].median()), 3))
    print("height 最大值:", round(float(gdf["height"].max()), 3))

    preview = gdf[[
        "obj_name", "vertex_count", "minx", "miny", "maxx", "maxy", "height"
    ]].head(20)

    print("\n=== 候选 obj 前20个 ===")
    print(preview.to_string(index=False))

    if failed:
        print("\n=== 失败样本前10个 ===")
        for item in failed[:10]:
            print(item)


if __name__ == "__main__":
    main()