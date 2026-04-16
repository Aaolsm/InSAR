from pathlib import Path

print("环境测试开始")
project_root = Path(__file__).resolve().parent.parent
print("root :",project_root)

print("检查库")
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd 
import shapely 
import pyproj
print("库导入成功")

try:
    import open3d as o3d
    print("open3d导入成功")
except Exception as e:
    print("open3d导入失败")

print("环境测试完毕")