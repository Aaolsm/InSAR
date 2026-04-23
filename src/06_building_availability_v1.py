from pathlib import Path
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

def robust_normalize(series: pd.Series, lower_q=0.05, upper_q=0.95) -> pd.Series:
    s = series.copy()
    q_low = s.quantile(lower_q)
    q_high = s.quantile(upper_q)
    s_clip = s.clip(lower=q_low, upper=q_high)

    vmin = s_clip.dropna().min()
    vmax = s_clip.dropna().max()

    return (s_clip - vmin) / (vmax - vmin)


def classify_availability(row):
    if row["insar_point_count"] == 0:
        return "no_points"

    v = row["availability_raw_robust"]
    if pd.isna(v):
        return "unknown"

    if v < row["q33"]:
        return "low"
    elif v < row["q66"]:
        return "medium"
    else:
        return "high"


def main():
    db_v1_path = ROOT / "data" / "processed" / "building_database_v1.gpkg"
    out_dir = ROOT / "data" / "processed"
    fig_dir = ROOT / "outputs" / "figures"

    gdf = gpd.read_file(db_v1_path).copy()

    gdf["point_density"] = gdf["insar_point_count"] / gdf["footprint_area"]
    # 非零建筑做log(x+1)变换
    gdf["log_point_count"] = np.where(
        gdf["insar_point_count"] > 0,
        np.log1p(gdf["insar_point_count"]),
        np.nan
    )
    gdf["log_point_density"] = np.where(
        gdf["point_density"] > 0,
        np.log1p(gdf["point_density"]),
        np.nan
    )

    # 归一化
    gdf["norm_point_count_robust"] = robust_normalize(gdf["log_point_count"])
    gdf["norm_point_density_robust"] = robust_normalize(gdf["log_point_density"])

    # 计算可用性指标
    gdf["availability_raw_robust"] = 0.5 * gdf["norm_point_count_robust"] + 0.5 * gdf["norm_point_density_robust"]
    gdf.loc[gdf["insar_point_count"] == 0, "availability_raw_robust"] = 0.0

    # 分级
    nonzero = gdf[gdf["insar_point_count"] > 0].copy()
    q33 = nonzero["availability_raw_robust"].quantile(0.33) 
    q66 = nonzero["availability_raw_robust"].quantile(0.66) 

    gdf["q33"] = q33
    gdf["q66"] = q66
    gdf["availability_level_robust"] = gdf.apply(classify_availability, axis=1)

    # 输出
    out_path = out_dir / "building_database_v2_robust.gpkg"
    gdf.to_file(out_path, driver="GPKG")


    print("=== 可用性指标 ===")
    print("最小值:", round(float(gdf["availability_raw_robust"].min()), 6))
    print("中位数:", round(float(gdf["availability_raw_robust"].median()), 6))
    print("最大值:", round(float(gdf["availability_raw_robust"].max()), 6))
    print("\n=== 可用性等级数量 ===")
    print(gdf["availability_level_robust"].value_counts(dropna=False).to_string())

    top10 = (
        gdf[[
            "building_id",
            "insar_point_count",
            "footprint_area",
            "point_density",
            "availability_raw_robust",
            "availability_level_robust"
        ]]
        .sort_values(by="availability_raw_robust", ascending=False)
        .head(10)
    )

    print("\n=== 可用性最高的前10栋建筑 ===")
    print(top10.to_string(index=False))


    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
    plt.rcParams["axes.unicode_minus"] = False
    fig, ax = plt.subplots(figsize=(8, 8))
    gdf.plot(ax=ax, column="availability_raw_robust", legend=True, linewidth=0.5, edgecolor="black")
    ax.set_title("可用性")
    plt.tight_layout()
    plt.savefig(fig_dir / "06_初步可用性.png", dpi=300)
    plt.show()


if __name__ == "__main__":
    main()