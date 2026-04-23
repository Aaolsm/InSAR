from pathlib import Path
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent.parent


def classify_deformation_level(row):
    if row["insar_point_count"] == 0 or pd.isna(row["deformation_intensity"]):
        return "no_data"

    v = row["deformation_intensity"]
    if v < row["q33_def"]:
        return "low"
    elif v < row["q66_def"]:
        return "medium"
    else:
        return "high"


def classify_risk(row):
    availability = row["availability_level_robust"]
    deformation = row["deformation_level"]

    if availability == "no_points" or deformation == "no_data":
        return "no_data"

    if deformation == "low":
        return "low"

    if deformation == "medium":
        if availability == "low":
            return "medium_low_confidence"
        return "medium"

    if deformation == "high":
        if availability == "high":
            return "high"
        elif availability == "medium":
            return "medium"
        elif availability == "low":
            return "suspected_high"

    return "unknown"


def make_risk_note(row):
    availability = row["availability_level_robust"]
    deformation = row["deformation_level"]
    risk = row["risk_level"]

    if risk == "no_data":
        return "建筑内无有效InSAR点，当前无法分级"
    if risk == "low":
        return "形变强度低"
    if risk == "medium":
        return "形变中等或形变较高但可用性一般"
    if risk == "medium_low_confidence":
        return "形变中等，但监测可用性偏低，结论置信度有限"
    if risk == "high":
        return "形变强度高，且监测可用性高"
    if risk == "suspected_high":
        return "形变强度高，但监测可用性偏低，建议重点复核"

    return f"availability={availability}, deformation={deformation}"


def main():
    # =========================
    # 1. 路径
    # =========================
    db_path = ROOT / "data" / "processed" / "building_database_v2_robust.gpkg"

    out_dir = ROOT / "data" / "processed"
    fig_dir = ROOT / "outputs" / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)

    # =========================
    # 2. 读取数据
    # =========================
    gdf = gpd.read_file(db_path).copy()

    # =========================
    # 3. 形变强度
    # =========================
    gdf["deformation_intensity"] = gdf["velocity_mean"].abs()

    nonzero = gdf[gdf["insar_point_count"] > 0].copy()

    q33_def = nonzero["deformation_intensity"].quantile(0.33) if len(nonzero) > 0 else np.nan
    q66_def = nonzero["deformation_intensity"].quantile(0.66) if len(nonzero) > 0 else np.nan

    gdf["q33_def"] = q33_def
    gdf["q66_def"] = q66_def

    # =========================
    # 4. 形变等级
    # =========================
    gdf["deformation_level"] = gdf.apply(classify_deformation_level, axis=1)

    # =========================
    # 5. 风险等级
    # =========================
    gdf["risk_level"] = gdf.apply(classify_risk, axis=1)
    gdf["risk_note"] = gdf.apply(make_risk_note, axis=1)

    # =========================
    # 6. 输出
    # =========================
    out_path = out_dir / "building_risk_v1.gpkg"
    gdf.to_file(out_path, driver="GPKG")

    # =========================
    # 7. 打印结果
    # =========================
    print("=== 第一版风险分级完成 ===")
    print("输出文件:", out_path)

    print("\n=== deformation_intensity 统计（有点建筑）===")
    if len(nonzero) > 0:
        print("最小值:", round(float(nonzero["deformation_intensity"].min()), 6))
        print("中位数:", round(float(nonzero["deformation_intensity"].median()), 6))
        print("最大值:", round(float(nonzero["deformation_intensity"].max()), 6))
        print("q33:", round(float(q33_def), 6))
        print("q66:", round(float(q66_def), 6))

    print("\n=== deformation_level 数量 ===")
    print(gdf["deformation_level"].value_counts(dropna=False).to_string())

    print("\n=== risk_level 数量 ===")
    print(gdf["risk_level"].value_counts(dropna=False).to_string())

    top10 = (
        gdf[[
            "building_id",
            "insar_point_count",
            "velocity_mean",
            "deformation_intensity",
            "availability_level_robust",
            "deformation_level",
            "risk_level"
        ]]
        .sort_values(by="deformation_intensity", ascending=False)
        .head(10)
    )

    print("\n=== deformation_intensity 最高的前10栋建筑 ===")
    print(top10.to_string(index=False))

    # =========================
    # 8. 绘图：风险图
    # =========================
    fig, ax = plt.subplots(figsize=(8, 8))
    gdf.plot(
        ax=ax,
        column="risk_level",
        legend=True,
        linewidth=0.5,
        edgecolor="black"
    )
    ax.set_title("Building Risk Level v1")
    plt.tight_layout()
    plt.savefig(fig_dir / "building_risk_level_v1.png", dpi=300)
    plt.show()


if __name__ == "__main__":
    main()