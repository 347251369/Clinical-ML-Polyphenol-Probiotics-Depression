import os
from typing import Dict, Any

import pandas as pd
from pymatgen.core import Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

def build_row_from_cif_for_cod(cif_path: str) -> Dict[str, Any]:
    """
    从 CIF 构建一行数据，列名与原 MP 抽取代码严格一致：
        "Material ID",
        "Formula",
        "Crystal System",
        "Space Group Symbol",
        "Space Group Number",
        "Sites",
        "Energy Above Hull",
        "Formation Energy",
        "Predicted Stable",
        "Volume",
        "Density",
        "Band Gap",
        "Is Gap Direct",
        "Is Metal",
        "Magnetic Ordering",
        "Total Magnetization",
        "CBM",
        "VBM"

    约定：
    - Material ID = "cod_" + cif 文件名(不含扩展名)，例如 4343748.cif -> "cod_4343748"
    - Formula 使用 CIF 解析出的 reduced_formula（如 Fe7 C18 N18 O14）
    - 仅填充可从 CIF 计算的列，所有 DFT 相关列填 None。
    """
    # 1) 从文件路径中提取编码：xxx.cif -> xxx
    basename = os.path.basename(cif_path)          # e.g. "4343748.cif"
    cod_code = os.path.splitext(basename)[0]       # e.g. "4343748"
    material_id = f"cod_{cod_code}"                # e.g. "cod_4343748"

    # 2) 读取结构
    structure = Structure.from_file(cif_path)

    # 3) 化学式：用 reduced_formula（机器学习也很好用）
    formula = structure.composition.reduced_formula

    # 4) 原子数 / 体积 / 密度
    n_sites = len(structure.sites)
    volume = structure.lattice.volume
    density = structure.density

    # 5) 空间群 / 晶系
    sga = SpacegroupAnalyzer(structure, symprec=1e-3)
    sg_symbol = sga.get_space_group_symbol()       # e.g. "Fm-3m"
    sg_number = sga.get_space_group_number()       # e.g. 225
    crystal_system = sga.get_crystal_system()      # e.g. "cubic"

    # 6) 构造与原表头一致的一行字典
    row = {
        "Material ID": material_id,
        "Formula": formula,
        "Crystal System": crystal_system,
        "Space Group Symbol": sg_symbol,
        "Space Group Number": sg_number,
        "Sites": n_sites,

        # 以下 DFT 相关全部设为 None
        "Energy Above Hull": None,
        "Formation Energy": None,
        "Predicted Stable": None,
        "Volume": round(volume, 5) if isinstance(volume, (int, float)) else None,
        "Density": round(density, 5) if isinstance(density, (int, float)) else None,
        "Band Gap": None,
        "Is Gap Direct": None,
        "Is Metal": None,
        "Magnetic Ordering": None,
        "Total Magnetization": None,
        "CBM": None,
        "VBM": None,
    }

    return row

if __name__ == "__main__":
    # 示例：你的 CIF 文件，比如 4343748.cif（普鲁士蓝）
    cif_file = "4002253.cif"

    pb_row = build_row_from_cif_for_cod(cif_file)

    # 打印检查
    for k, v in pb_row.items():
        print(f"{k}: {v}")

    # 输出到一个 CSV 文件中
    df = pd.DataFrame([pb_row])
    out_name = "1.csv"   # 你可以改成任何你想要的文件名
    df.to_csv(out_name, index=False)
    print(f"\n已保存为: {out_name}")