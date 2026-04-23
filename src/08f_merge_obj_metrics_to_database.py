from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent.parent


def safe_ratio(a, b):
    if pd.isna(a) or pd.isna(b) or b == 0:
        return np.nan
    return a / b


def main():
    # =========================
    # 1. 路径
    # =========================
    db_path = ROOT / "data" / "processed" / "building_database_v2_robust.gpkg"
    clean_obj_match_path = ROOT / "data" / "processed" / "obj_building_matched_clean.gpkg"

    out_dir = ROOT / "data" / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)

    # =========================
    # 2. 读取
    # =========================
    db = gpd.read_file(db_path).copy()
    clean = gpd.read_file(clean_obj_match_path).copy()

    # =========================
    # 3. 逐条 obj 匹配记录先算 proxy
    # =========================
    clean["obj_bbox_area"] = clean["bbox_length"] * clean["bbox_width"]
    clean["obj_bbox_volume"] = clean["bbox_length"] * clean["bbox_width"] * clean["height"]
    clean["obj_facade_area_proxy"] = 2 * (clean["bbox_length"] + clean["bbox_width"]) * clean["height"]

    # =========================
    # 4. 汇总到建筑级
    # =========================
    obj_stats = (
        clean.groupby("building_id")
        .agg(
            obj_count_clean=("obj_id", "size"),
            building_height_obj=("height", "max"),
            building_height_obj_mean=("height", "mean"),
            bbox_length_obj=("bbox_length", "max"),
            bbox_width_obj=("bbox_width", "max"),
            bbox_area_sum_obj=("obj_bbox_area", "sum"),
            volume_proxy_obj=("obj_bbox_volume", "sum"),
            facade_area_proxy_obj=("obj_facade_area_proxy", "sum"),
            overlap_area_sum_obj=("overlap_area", "sum"),
        )
        .reset_index()
    )

    # =========================
    # 5. 长宽比
    # =========================
    obj_stats["length_width_ratio_obj"] = obj_stats.apply(
        lambda row: np.nan
        if pd.isna(row["bbox_length_obj"]) or pd.isna(row["bbox_width_obj"]) or min(row["bbox_length_obj"], row["bbox_width_obj"]) == 0
        else max(row["bbox_length_obj"], row["bbox_width_obj"]) / min(row["bbox_length_obj"], row["bbox_width_obj"]),
        axis=1
    )

    # 体量密度代理：体量 / footprint_area
    obj_stats = obj_stats.merge(
        db[["building_id", "footprint_area"]].drop_duplicates(),
        on="building_id",
        how="left"
    )
    obj_stats["volume_per_area_obj"] = obj_stats.apply(
        lambda row: safe_ratio(row["volume_proxy_obj"], row["footprint_area"]),
        axis=1
    )

    # =========================
    # 6. 合并进数据库
    # =========================
    db_v3 = db.merge(
        obj_stats.drop(columns=["footprint_area"]),
        on="building_id",
        how="left"
    )

    db_v3["obj_count_clean"] = db_v3["obj_count_clean"].fillna(0).astype(int)

    # =========================
    # 7. 输出
    # =========================
    out_path = out_dir / "building_database_v3_obj.gpkg"
    db_v3.to_file(out_path, driver="GPKG")

    # =========================
    # 8. 打印结果
    # =========================
    print("=== obj 微观3D指标已并入建筑数据库 ===")
    print("输出文件:", out_path)

    matched_buildings = db_v3[db_v3["obj_count_clean"] > 0].copy()
    print("匹配到 clean obj 的建筑数:", len(matched_buildings))

    if len(matched_buildings) > 0:
        print("\n=== building_height_obj 统计 ===")
        print("最小值:", round(float(matched_buildings["building_height_obj"].min()), 3))
        print("中位数:", round(float(matched_buildings["building_height_obj"].median()), 3))
        print("最大值:", round(float(matched_buildings["building_height_obj"].max()), 3))

        print("\n=== length_width_ratio_obj 统计 ===")
        valid_ratio = matched_buildings["length_width_ratio_obj"].dropna()
        print("最小值:", round(float(valid_ratio.min()), 3))
        print("中位数:", round(float(valid_ratio.median()), 3))
        print("最大值:", round(float(valid_ratio.max()), 3))

        print("\n=== volume_proxy_obj 统计 ===")
        print("最小值:", round(float(matched_buildings["volume_proxy_obj"].min()), 3))
        print("中位数:", round(float(matched_buildings["volume_proxy_obj"].median()), 3))
        print("最大值:", round(float(matched_buildings["volume_proxy_obj"].max()), 3))

        print("\n=== facade_area_proxy_obj 统计 ===")
        print("最小值:", round(float(matched_buildings["facade_area_proxy_obj"].min()), 3))
        print("中位数:", round(float(matched_buildings["facade_area_proxy_obj"].median()), 3))
        print("最大值:", round(float(matched_buildings["facade_area_proxy_obj"].max()), 3))

        top10 = (
            matched_buildings[[
                "building_id",
                "obj_count_clean",
                "building_height_obj",
                "length_width_ratio_obj",
                "volume_proxy_obj",
                "facade_area_proxy_obj"
            ]]
            .sort_values(by="building_height_obj", ascending=False)
            .head(10)
        )

        print("\n=== 建筑高度最高的前10栋 ===")
        print(top10.to_string(index=False))


if __name__ == "__main__":
    main()