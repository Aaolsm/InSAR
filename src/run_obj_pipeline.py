from obj_pipeline.filter_matches import run as run_filter_matches
from obj_pipeline.find_candidates import run as run_find_candidates
from obj_pipeline.match_buildings import run as run_match_buildings
from obj_pipeline.merge_metrics import run as run_merge_metrics


def main():
    print("=== 开始运行 OBJ 主流程 ===")

    print("\n[1/4] 筛选研究区候选 obj")
    run_find_candidates()

    print("\n[2/4] obj 与建筑匹配")
    run_match_buildings()

    print("\n[3/4] 清洗 obj-建筑匹配结果")
    run_filter_matches()

    print("\n[4/4] 并入建筑数据库")
    run_merge_metrics()

    print("\n=== OBJ 主流程运行完成 ===")


if __name__ == "__main__":
    main()
