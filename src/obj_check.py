from pathlib import Path

ROOT = Path(r"E:\Graduation project\InSAR")
obj_dir = ROOT / "data" / "raw" / "obj" / "obj"

obj_files = list(obj_dir.glob("*.obj"))
mtl_files = list(obj_dir.glob("*.mtl"))

total_size_gb = sum(f.stat().st_size for f in obj_files) / 1024**3

print("obj 数量:", len(obj_files))
print("mtl 数量:", len(mtl_files))
print("obj 总体积(GB):", round(total_size_gb, 3))
print("前5个 obj 文件:")
for f in obj_files[:5]:
    print(" -", f.name)