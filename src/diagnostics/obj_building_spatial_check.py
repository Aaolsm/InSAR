from pathlib import Path
import sys

import geopandas as gpd
import matplotlib.pyplot as plt


if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import ROOT


def main():
    # =========================
    # 1. 路径
    # =========================
    obj_sample_path = ROOT / "data" / "interim" / "obj_sample_bbox_check.gpkg"
    buildings_geom_path = ROOT / "data" / "processed" / "buildings_geom_metrics.gpkg"

    out_dir = ROOT / "data" / "interim"
    fig_dir = ROOT / "outputs" / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)

    # =========================
    # 2. 读取数据
    # =========================
    obj_gdf = gpd.read_file(obj_sample_path)
    bld_gdf = gpd.read_file(buildings_geom_path)

    # CRS 保险
    if obj_gdf.crs != bld_gdf.crs:
        obj_gdf = obj_gdf.to_crs(bld_gdf.crs)

    # =========================
    # 3. 研究区内 obj 样本筛选
    # 用建筑整体范围做一个包络框
    # =========================
    study_bounds = bld_gdf.total_bounds
    minx, miny, maxx, maxy = study_bounds

    obj_in_study = obj_gdf.cx[minx:maxx, miny:maxy].copy()

    # =========================
    # 4. 空间相交检查
    # =========================
    if len(obj_in_study) > 0:
        join_intersects = gpd.sjoin(
            obj_in_study,
            bld_gdf[["building_id", "geometry"]],
            how="left",
            predicate="intersects"
        )

        matched = join_intersects[join_intersects["building_id"].notna()].copy()
        unmatched = join_intersects[join_intersects["building_id"].isna()].copy()
    else:
        matched = obj_in_study.copy()
        matched["building_id"] = None
        unmatched = obj_in_study.copy()

    # =========================
    # 5. 输出
    # =========================
    obj_in_study.to_file(out_dir / "obj_sample_in_study_area.gpkg", driver="GPKG")
    if len(obj_in_study) > 0:
        matched.to_file(out_dir / "obj_sample_matched_buildings.gpkg", driver="GPKG")
        unmatched.to_file(out_dir / "obj_sample_unmatched_buildings.gpkg", driver="GPKG")

    # =========================
    # 6. 打印
    # =========================
    print("=== obj 与研究区建筑空间对位检查完成 ===")
    print("研究区建筑数量:", len(bld_gdf))
    print("obj 抽样总数:", len(obj_gdf))
    print("落入研究区范围的 obj 数:", len(obj_in_study))

    if len(obj_in_study) > 0:
        print("与建筑相交的 obj 数:", len(matched))
        print("未与建筑相交的 obj 数:", len(unmatched))

        if len(matched) > 0:
            preview = matched[[
                "obj_name", "building_id", "height", "bbox_length", "bbox_width"
            ]].head(10)
            print("\n=== 匹配成功样本前10个 ===")
            print(preview.to_string(index=False))

    # =========================
    # 7. 绘图
    # =========================
    fig, ax = plt.subplots(figsize=(8, 8))

    bld_gdf.boundary.plot(ax=ax, linewidth=0.8, edgecolor="black")

    if len(obj_in_study) > 0:
        if len(unmatched) > 0:
            unmatched.boundary.plot(ax=ax, linewidth=1.0, edgecolor="red", label="obj_unmatched")
        if len(matched) > 0:
            matched.boundary.plot(ax=ax, linewidth=1.0, edgecolor="blue", label="obj_matched")

    ax.set_title("OBJ vs Building Footprint Spatial Check")
    ax.legend()
    plt.tight_layout()
    plt.savefig(fig_dir / "obj_building_spatial_check.png", dpi=300)
    plt.show()


if __name__ == "__main__":
    main()
