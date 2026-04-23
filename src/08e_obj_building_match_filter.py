from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent.parent


def main():
    # =========================
    # 1. 路径
    # =========================
    matched_path = ROOT / "data" / "processed" / "obj_building_matched.gpkg"
    buildings_path = ROOT / "data" / "processed" / "buildings_geom_metrics.gpkg"

    out_dir = ROOT / "data" / "processed"
    fig_dir = ROOT / "outputs" / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)

    # =========================
    # 2. 读取
    # =========================
    matched = gpd.read_file(matched_path).copy()
    buildings = gpd.read_file(buildings_path)[
        ["building_id", "footprint_area", "geometry"]
    ].copy()

    # 合并建筑面积，保险起见
    if "footprint_area" not in matched.columns:
        matched = matched.merge(
            buildings.drop(columns="geometry"),
            on="building_id",
            how="left"
        )

    # 保险：重算 obj bbox 面积 / 体量
    if "obj_bbox_area" not in matched.columns:
        matched["obj_bbox_area"] = matched["bbox_length"] * matched["bbox_width"]
    if "obj_bbox_volume" not in matched.columns:
        matched["obj_bbox_volume"] = matched["bbox_length"] * matched["bbox_width"] * matched["height"]

    # =========================
    # 3. 构造筛选指标
    # =========================
    matched["area_ratio"] = matched["obj_bbox_area"] / matched["footprint_area"]
    matched["overlap_ratio_obj"] = matched["overlap_area"] / matched["obj_bbox_area"]
    matched["overlap_ratio_bld"] = matched["overlap_area"] / matched["footprint_area"]

    # =========================
    # 4. 清洗规则（第一版）
    # =========================
    clean = matched[
        (matched["height"] > 1) &
        (matched["height"] < 300) &
        (matched["area_ratio"] <= 5) &
        (matched["overlap_ratio_obj"] >= 0.2) &
        (matched["overlap_ratio_bld"] >= 0.2)
    ].copy()

    removed = matched.loc[~matched.index.isin(clean.index)].copy()

    # =========================
    # 5. 如果一个 obj 仍对应多个建筑，只保留 overlap_area 最大的
    # =========================
    clean = (
        clean.sort_values(["obj_id", "overlap_area"], ascending=[True, False])
        .drop_duplicates(subset="obj_id", keep="first")
        .copy()
    )

    # =========================
    # 6. 汇总到建筑级
    # =========================
    building_obj_clean = (
        clean.groupby("building_id")
        .agg(
            obj_count_clean=("obj_id", "size"),
            obj_height_max_clean=("height", "max"),
            obj_height_mean_clean=("height", "mean"),
            obj_height_median_clean=("height", "median"),
            obj_bbox_length_max_clean=("bbox_length", "max"),
            obj_bbox_width_max_clean=("bbox_width", "max"),
            obj_bbox_area_sum_clean=("obj_bbox_area", "sum"),
            obj_bbox_volume_sum_clean=("obj_bbox_volume", "sum"),
            obj_overlap_area_sum_clean=("overlap_area", "sum"),
            area_ratio_median_clean=("area_ratio", "median"),
            overlap_ratio_obj_median_clean=("overlap_ratio_obj", "median"),
            overlap_ratio_bld_median_clean=("overlap_ratio_bld", "median"),
        )
        .reset_index()
    )

    building_clean = buildings.merge(building_obj_clean, on="building_id", how="left")
    building_clean["obj_count_clean"] = building_clean["obj_count_clean"].fillna(0).astype(int)

    # =========================
    # 7. 输出
    # =========================
    clean_out = out_dir / "obj_building_matched_clean.gpkg"
    removed_out = out_dir / "obj_building_removed_by_filter.gpkg"
    building_out = out_dir / "building_obj_metrics_clean_v1.gpkg"

    clean.to_file(clean_out, driver="GPKG")
    removed.to_file(removed_out, driver="GPKG")
    building_clean.to_file(building_out, driver="GPKG")

    # =========================
    # 8. 打印结果
    # =========================
    print("=== obj 匹配结果清洗完成 ===")
    print("原始匹配 obj 数:", matched['obj_id'].nunique())
    print("清洗后 obj 数:", clean['obj_id'].nunique())
    print("被剔除 obj 数:", matched['obj_id'].nunique() - clean['obj_id'].nunique())
    print("匹配到 clean obj 的建筑数:", int((building_clean["obj_count_clean"] > 0).sum()))

    if len(clean) > 0:
        print("\n=== 清洗后 area_ratio 统计 ===")
        print("最小值:", round(float(clean["area_ratio"].min()), 4))
        print("中位数:", round(float(clean["area_ratio"].median()), 4))
        print("最大值:", round(float(clean["area_ratio"].max()), 4))

        print("\n=== 清洗后 overlap_ratio_obj 统计 ===")
        print("最小值:", round(float(clean["overlap_ratio_obj"].min()), 4))
        print("中位数:", round(float(clean["overlap_ratio_obj"].median()), 4))
        print("最大值:", round(float(clean["overlap_ratio_obj"].max()), 4))

        print("\n=== 清洗后 obj_height_max_clean 统计 ===")
        nonzero = building_clean[building_clean["obj_count_clean"] > 0]
        print("最小值:", round(float(nonzero["obj_height_max_clean"].min()), 3))
        print("中位数:", round(float(nonzero["obj_height_max_clean"].median()), 3))
        print("最大值:", round(float(nonzero["obj_height_max_clean"].max()), 3))

        top10 = (
            building_clean[[
                "building_id",
                "obj_count_clean",
                "obj_height_max_clean",
                "obj_bbox_area_sum_clean",
                "obj_bbox_volume_sum_clean"
            ]]
            .sort_values(by="obj_count_clean", ascending=False)
            .head(10)
        )

        print("\n=== 清洗后 obj_count 最高的前10栋建筑 ===")
        print(top10.to_string(index=False))

    # =========================
    # 9. 画图
    # =========================
    fig, ax = plt.subplots(figsize=(8, 8))
    buildings.boundary.plot(ax=ax, linewidth=0.8, edgecolor="black")
    if len(removed) > 0:
        removed.boundary.plot(ax=ax, linewidth=1.0, edgecolor="red", label="removed")
    if len(clean) > 0:
        clean.boundary.plot(ax=ax, linewidth=1.0, edgecolor="blue", label="clean")

    ax.set_title("OBJ Match Filter Result")
    handles, labels = ax.get_legend_handles_labels()
    if labels:
        ax.legend()

    plt.tight_layout()
    plt.savefig(fig_dir / "obj_match_filter_result.png", dpi=300)
    plt.show()


if __name__ == "__main__":
    main()