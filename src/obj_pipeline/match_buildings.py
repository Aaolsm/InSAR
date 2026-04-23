from pathlib import Path
import sys

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd


if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import ROOT


def main():
    # =========================
    # 1. 路径
    # =========================
    obj_path = ROOT / "data" / "interim" / "obj_candidates_in_study_area.gpkg"
    bld_path = ROOT / "data" / "processed" / "buildings_geom_metrics.gpkg"

    out_dir = ROOT / "data" / "processed"
    fig_dir = ROOT / "outputs" / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)

    # =========================
    # 2. 读取数据
    # =========================
    obj_gdf = gpd.read_file(obj_path)
    bld_gdf = gpd.read_file(bld_path)

    if obj_gdf.crs != bld_gdf.crs:
        obj_gdf = obj_gdf.to_crs(bld_gdf.crs)

    # 只保留需要字段
    obj_cols = [
        "obj_name", "obj_stem", "vertex_count",
        "minx", "miny", "minz", "maxx", "maxy", "maxz",
        "bbox_length", "bbox_width", "height", "geometry"
    ]
    obj_gdf = obj_gdf[obj_cols].copy()

    bld_cols = [
        "building_id", "footprint_area", "footprint_perimeter",
        "area_perimeter_ratio", "orientation", "geometry"
    ]
    bld_gdf = bld_gdf[bld_cols].copy()

    # 给 obj 一个唯一 id
    obj_gdf["obj_id"] = range(1, len(obj_gdf) + 1)

    # 估算 obj bbox 面积和体量
    obj_gdf["obj_bbox_area"] = obj_gdf["bbox_length"] * obj_gdf["bbox_width"]
    obj_gdf["obj_bbox_volume"] = obj_gdf["bbox_length"] * obj_gdf["bbox_width"] * obj_gdf["height"]

    # =========================
    # 3. 先做相交筛选
    # =========================
    joined = gpd.sjoin(
        obj_gdf,
        bld_gdf[["building_id", "geometry"]],
        how="left",
        predicate="intersects"
    )

    intersected = joined[joined["building_id"].notna()].copy()
    unmatched_obj = joined[joined["building_id"].isna()].copy()

    if len(intersected) == 0:
        print("=== 未找到任何 obj 与建筑相交 ===")
        return

    # =========================
    # 4. 用 overlay 计算真实重叠面积
    #    再为每个 obj 选 overlap_area 最大的 building_id
    # =========================
    obj_for_overlay = obj_gdf.copy()
    bld_for_overlay = bld_gdf.copy()

    intersections = gpd.overlay(obj_for_overlay, bld_for_overlay, how="intersection")
    intersections["overlap_area"] = intersections.geometry.area

    # 每个 obj 只保留 overlap_area 最大的建筑
    best_match = (
        intersections.sort_values(["obj_id", "overlap_area"], ascending=[True, False])
        .drop_duplicates(subset="obj_id", keep="first")
        .copy()
    )

    # =========================
    # 5. 生成 obj -> building 匹配表
    # =========================
    matched_obj = obj_gdf.merge(
        best_match[["obj_id", "building_id", "overlap_area"]],
        on="obj_id",
        how="left"
    )

    matched_only = matched_obj[matched_obj["building_id"].notna()].copy()
    unmatched_only = matched_obj[matched_obj["building_id"].isna()].copy()

    # =========================
    # 6. 汇总到建筑级
    # =========================
    building_obj_stats = (
        matched_only.groupby("building_id")
        .agg(
            obj_count=("obj_id", "size"),
            obj_height_max=("height", "max"),
            obj_height_mean=("height", "mean"),
            obj_height_median=("height", "median"),
            obj_bbox_length_max=("bbox_length", "max"),
            obj_bbox_width_max=("bbox_width", "max"),
            obj_bbox_area_sum=("obj_bbox_area", "sum"),
            obj_bbox_volume_sum=("obj_bbox_volume", "sum"),
            obj_overlap_area_sum=("overlap_area", "sum"),
        )
        .reset_index()
    )

    building_with_obj = bld_gdf.merge(building_obj_stats, on="building_id", how="left")
    building_with_obj["obj_count"] = building_with_obj["obj_count"].fillna(0).astype(int)

    # =========================
    # 7. 输出
    # =========================
    matched_obj_out = out_dir / "obj_building_matched.gpkg"
    unmatched_obj_out = out_dir / "obj_building_unmatched.gpkg"
    building_obj_out = out_dir / "building_obj_metrics_v1.gpkg"

    matched_only.to_file(matched_obj_out, driver="GPKG")
    unmatched_only.to_file(unmatched_obj_out, driver="GPKG")
    building_with_obj.to_file(building_obj_out, driver="GPKG")

    # =========================
    # 8. 打印结果
    # =========================
    print("=== obj 与建筑匹配完成 ===")
    print("候选 obj 总数:", len(obj_gdf))
    print("与建筑有相交关系的 obj 数:", matched_only['obj_id'].nunique())
    print("未匹配 obj 数:", len(unmatched_only))
    print("匹配到 obj 的建筑数:", (building_with_obj["obj_count"] > 0).sum())

    multi_obj_buildings = (building_with_obj["obj_count"] > 1).sum()
    print("匹配到多个 obj 的建筑数:", int(multi_obj_buildings))

    nonzero = building_with_obj[building_with_obj["obj_count"] > 0].copy()
    if len(nonzero) > 0:
        print("\n=== 建筑级 obj_count 统计 ===")
        print("最小值:", int(nonzero["obj_count"].min()))
        print("中位数:", float(nonzero["obj_count"].median()))
        print("平均值:", round(float(nonzero["obj_count"].mean()), 2))
        print("最大值:", int(nonzero["obj_count"].max()))

        print("\n=== 建筑级 obj_height_max 统计 ===")
        print("最小值:", round(float(nonzero["obj_height_max"].min()), 3))
        print("中位数:", round(float(nonzero["obj_height_max"].median()), 3))
        print("最大值:", round(float(nonzero["obj_height_max"].max()), 3))

    top10 = (
        building_with_obj[[
            "building_id", "obj_count", "obj_height_max",
            "obj_bbox_area_sum", "obj_bbox_volume_sum"
        ]]
        .sort_values(by="obj_count", ascending=False)
        .head(10)
    )

    print("\n=== obj_count 最高的前10栋建筑 ===")
    print(top10.to_string(index=False))

    # =========================
    # 9. 画图
    # =========================
    fig, ax = plt.subplots(figsize=(8, 8))
    bld_gdf.boundary.plot(ax=ax, linewidth=0.8, edgecolor="black")

    if len(unmatched_only) > 0:
        unmatched_only.boundary.plot(ax=ax, linewidth=1.0, edgecolor="red", label="obj_unmatched")
    if len(matched_only) > 0:
        matched_only.boundary.plot(ax=ax, linewidth=1.0, edgecolor="blue", label="obj_matched")

    ax.set_title("OBJ-Building Match Result")
    handles, labels = ax.get_legend_handles_labels()
    if labels:
        ax.legend()

    plt.tight_layout()
    plt.savefig(fig_dir / "obj_building_match_result.png", dpi=300)
    plt.show()


def run():
    main()


if __name__ == "__main__":
    run()
