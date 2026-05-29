from mp_api.client import MPRester
import pandas as pd
import urllib.parse
import urllib.request
import requests
import re
import os
from llm_client import *
from prompts import *
import csv
from neo4j import GraphDatabase

# Neo4j 数据库操作类
class Neo4jFDA:
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="12345678"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def get_is_fda(self, name: str):
        """从 Neo4j 查询是否存在该化学物"""
        with self.driver.session() as session:
            result = session.run(
                "MATCH (c:Chemical {name: $name}) RETURN c.is_fda AS is_fda",
                name=name.lower().strip()
            ).single()
            if result:
                return int(result["is_fda"])
            return None

    def upsert_chemical(self, name: str, is_fda: int):
        """写入或更新 Chemical 节点"""
        with self.driver.session() as session:
            session.run(
                """
                MERGE (c:Chemical {name: $name})
                SET c.is_fda = $is_fda
                """,
                name=name.lower().strip(),
                is_fda=int(is_fda)
            )

# 安全解析 JSON 字符串
def _safe_json(raw):
    try:
        s = (raw or "").strip()
        i, j = s.find("{"), s.rfind("}")
        if i != -1 and j != -1 and j > i:
            import json
            return json.loads(s[i:j+1])
    except Exception:
        pass
    return None

# 从 COD 数据库下载材料数据
def download_cod(
    include_elements=None,
    may_include_elements=None,
    has_toxicity=False,
    output_file="cod.csv"
):
    z_min = 1
    z_max = 8
    zprime_min = 1
    zprime_max = 2
    volume_min = 100
    volume_max = 20000
    distinct_elements_min = 2
    distinct_elements_max = 6
    has_fobs = True

    base_url = "https://www.crystallography.net/cod/result"
    params_base = {"format": "csv"}

    not_elements = ["Pb", "Hg", "Cd", "As"] if not has_toxicity else None
    params_base.update({
        "z_min": z_min,
        "z_max": z_max,
        "zprime_min": zprime_min,
        "zprime_max": zprime_max,
        "vol_min": volume_min,
        "vol_max": volume_max,
        "nel_min": distinct_elements_min,
        "nel_max": distinct_elements_max
    })
    if has_fobs:
        params_base["has_fobs"] = "on"
    if not_elements:
        params_base["elnot"] = ",".join(not_elements)

    all_dfs = []

    def query_cod(extra_elements=None):
        params = params_base.copy()
        idx = 1
        if include_elements:
            for el in include_elements:
                params[f"el{idx}"] = el
                idx += 1
        if extra_elements:
            for el in extra_elements:
                params[f"el{idx}"] = el
                idx += 1

        query_url = f"{base_url}?{urllib.parse.urlencode(params)}"
        print("Query URL:", query_url)

        response = requests.get(query_url, timeout=120)
        if response.status_code != 200:
            print("Request failed:", response.status_code)
            return None

        if len(response.content) < 500:
            print("No data returned")
            print(response.text[:200])
            return None

        from io import StringIO
        df = pd.read_csv(StringIO(response.text), comment="#", skip_blank_lines=True, on_bad_lines="skip")
        df.columns = df.columns.str.strip()
        return df

    df_main = query_cod()
    if df_main is not None:
        all_dfs.append(df_main)

    if may_include_elements:
        for el in may_include_elements:
            df_temp = query_cod(extra_elements=[el])
            if df_temp is not None:
                all_dfs.append(df_temp)

    if not all_dfs:
        print("No data returned")
        return None

    df_all = pd.concat(all_dfs, ignore_index=True).drop_duplicates(subset=["file"], keep="first")
    df_all = df_all.iloc[:, :38]
    df_all.to_csv(output_file, index=False)
    print(f"✅ Saved results: {output_file}, total {len(df_all)} records.")

    return output_file

# 从 Materials Project 下载材料数据
def get_materials_data(
    api_key="VDf8uPu9uEYdjVQtXghUSrDNs3cPaVet",
    elements_include=None,
    elements_exclude=None,
    is_stable=None,
    output_file="filtered_materials.csv"
):
    from mp_api.client import MPRester
    import pandas as pd

    with MPRester(api_key) as mpr:
        search_kwargs = {
            "is_stable": is_stable,
            "fields": [
                "material_id",
                "formula_pretty",
                "symmetry",
                "energy_above_hull",
                "formation_energy_per_atom",
                "volume",
                "density",
                "band_gap",
                "is_gap_direct",
                "is_metal",
                "ordering",
                "total_magnetization",
                "is_stable",
                "nsites",
                "elements",
                "cbm",      
                "vbm",     
            ],
        }

        if elements_include:
            search_kwargs["elements"] = elements_include

        docs = mpr.materials.summary.search(**search_kwargs)

    data = []
    for doc in docs:
        if elements_exclude and any(e in doc.elements for e in elements_exclude):
            continue

        data.append({
            "Material ID": doc.material_id,
            "Formula": doc.formula_pretty,
            "Crystal System": getattr(doc.symmetry, "crystal_system", None),
            "Space Group Symbol": getattr(doc.symmetry, "symbol", None),
            "Space Group Number": getattr(doc.symmetry, "number", None),
            "Sites": doc.nsites,
            "Energy Above Hull": round(doc.energy_above_hull, 5) if isinstance(doc.energy_above_hull, (int, float)) else None,
            "Formation Energy": round(doc.formation_energy_per_atom, 5) if isinstance(doc.formation_energy_per_atom, (int, float)) else None,
            "Predicted Stable": doc.is_stable,
            "Volume": round(doc.volume, 5) if isinstance(doc.volume, (int, float)) else None,
            "Density": round(doc.density, 5) if isinstance(doc.density, (int, float)) else None,
            "Band Gap": round(doc.band_gap, 5) if isinstance(doc.band_gap, (int, float)) else None,
            "Is Gap Direct": doc.is_gap_direct,
            "Is Metal": doc.is_metal,
            "Magnetic Ordering": doc.ordering,
            "Total Magnetization": round(doc.total_magnetization, 5) if isinstance(doc.total_magnetization, (int, float)) else None,
            "CBM": round(doc.cbm, 5) if isinstance(doc.cbm, (int, float)) else None,   
            "VBM": round(doc.vbm, 5) if isinstance(doc.vbm, (int, float)) else None,   
        })

    df = pd.DataFrame(data)
    df.to_csv(output_file, index=False, encoding="utf-8-sig")

    print(f"✅ A total of {len(df)} materials were filtered and saved as '{output_file}'")

    return df

# 判断化学式是否合法
def is_valid_chemical_formula(chemname):
    CHINESE_RE = re.compile(r'[\u4e00-\u9fff]')
    VALID_CHAR_RE = re.compile(r'^[A-Za-z0-9 \(\)\[\]\.\,\+\-\:\/]+$')
    if not isinstance(chemname, str):
        return False

    s = chemname.strip()
    if s == "":
        return False

    if CHINESE_RE.search(s):
        return False

    if '<' in s or '>' in s:
        return False

    if not VALID_CHAR_RE.match(s):
        return False

    compact = s.replace(" ", "")
    if not re.search(r'[A-Z]', compact):
        return False
    
    if re.search(r'[a-z]{3,}', s):
        return False
    return True

# 处理 COD 和 MJ 文件，筛选 FDA 物质
def process_files(cod_file, mj_file, client=None, neo4j_db=None):
    try:
        if neo4j_db is None:
            raise ValueError("必须传入 Neo4jFDA 实例")

        # === 1) 定义检查并更新 FDA 状态的函数 ===
        def check_and_update_fda(msg):
            msg_lower = str(msg).lower().strip()

            is_fda = neo4j_db.get_is_fda(msg_lower)
            if is_fda is not None:
                return is_fda == 1
            #智能体调用
            '''
            prompt = prompt_fda(msg)
            print(f"➡️ 智能体输入:\n{prompt}\n")
            answer = client.chat(prompt)
            print(f"⬅️ 智能体输出:\n{answer}\n")
            data = _safe_json(answer)

            if isinstance(data, dict) and data.get("answer", "").lower() == "yes":
                is_fda = 1
            else:
                is_fda = 0

            print(f"➕ 未在 Neo4j 中找到，写入新节点: {msg_lower} (is_fda={is_fda})")
            neo4j_db.upsert_chemical(msg_lower, is_fda)
            '''
            is_fda = 0  # 临时默认全部非 FDA,测试用
            
            return is_fda == 1
        
        # === 2) 处理 COD 文件 ===
        cod_outfile = None
        if cod_file and os.path.exists(cod_file):
            print(f"🔹 Processing COD file: {cod_file}")
            df_cod = pd.read_csv(cod_file)
            if 'chemname' not in df_cod.columns:
                raise ValueError("cod_file 中未找到 'chemname' 列")

            df_cod_filtered = df_cod[df_cod['chemname'].apply(is_valid_chemical_formula)].copy()
            cod_keep_rows = []

            for _, row in df_cod_filtered.iterrows():
                msg = row['chemname']
                try:
                    if check_and_update_fda(msg):
                        cod_keep_rows.append(row)
                except Exception as e:
                    print(f"处理 {msg} 时出错: {e}")

            df_cod_final = pd.DataFrame(cod_keep_rows)
            base, ext = os.path.splitext(cod_file)
            cod_outfile = f"{base}_fda{ext}"
            df_cod_final.to_csv(cod_outfile, index=False, encoding='utf-8-sig')
            print(f"✅ COD 文件筛选完成: {cod_outfile}（{len(df_cod_final)} 条记录）")

        # === 3) 处理 MJ 文件 ===
        mj_outfile = None
        if mj_file and os.path.exists(mj_file):
            print(f"🔹 处理 MJ 文件: {mj_file}")
            df_mj = pd.read_csv(mj_file)
            if 'Formula' not in df_mj.columns:
                raise ValueError("mj_file 中未找到 'Formula' 列")

            mj_keep_rows = []

            for _, row in df_mj.iterrows():
                msg = row['Formula']
                try:
                    if check_and_update_fda(msg):
                        mj_keep_rows.append(row)
                except Exception as e:
                    print(f"处理 {msg} 时出错: {e}")

            df_mj_final = pd.DataFrame(mj_keep_rows)
            base, ext = os.path.splitext(mj_file)
            mj_outfile = f"{base}_fda{ext}"
            df_mj_final.to_csv(mj_outfile, index=False, encoding='utf-8-sig')
            print(f"✅ MJ 文件筛选完成: {mj_outfile}（{len(df_mj_final)} 条记录）")

        return cod_outfile, mj_outfile

    except Exception as e:
        print(f"处理文件时出错: {e}")
        return None, None
    
def _is_single_element(formula):
    """判断化学式是否为单质（只含一种元素），如 C, Si, O2, Fe 等"""
    elements = set(re.findall(r'[A-Z][a-z]?', str(formula)))
    return len(elements) == 1


NANO_CACHE_FILE = "cache/nano_cache.csv"


def _load_nano_cache():
    """加载 nano_cache.csv 到 dict，不存在则返回空 dict"""
    cache = {}
    if os.path.exists(NANO_CACHE_FILE):
        with open(NANO_CACHE_FILE, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for row in reader:
                if len(row) >= 2:
                    cache[row[0].strip()] = row[1].strip().lower() == "yes"
    return cache


def _save_nano_cache(cache):
    """将 cache dict 写回 nano_cache.csv"""
    with open(NANO_CACHE_FILE, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["formula", "is_nano"])
        for formula, is_nano in cache.items():
            writer.writerow([formula, "yes" if is_nano else "no"])


def process_nano(cod_file, mj_file, client=None):
    try:
        nano_cache = _load_nano_cache()

        def check_nano(msg):
            msg = str(msg).strip()
            if not msg:
                return False

            # 单质直接返回 False
            if _is_single_element(msg):
                nano_cache[msg] = False
                return False

            # 命中缓存
            if msg in nano_cache:
                return nano_cache[msg]

            # 缓存未命中，询问智能体
            prompt = prompt_nano(msg)
            answer = client.chat(prompt)
            data = _safe_json(answer)
            is_nano = isinstance(data, dict) and data.get("answer", "").lower() == "yes"
            nano_cache[msg] = is_nano
            return is_nano

        cod_outfile, mj_outfile = None, None

        # --- COD ---
        if cod_file and os.path.exists(cod_file):
            df = pd.read_csv(cod_file)
            keep_rows = []
            for _, row in df.iterrows():
                try:
                    if check_nano(row['chemname']):
                        keep_rows.append(row)
                except:
                    pass
            out_df = pd.DataFrame(keep_rows)
            base, ext = os.path.splitext(cod_file)
            cod_outfile = f"{base}_nano{ext}"
            out_df.to_csv(cod_outfile, index=False, encoding='utf-8-sig')
            print(f"COD 完成: {cod_outfile} ({len(out_df)} 条)")

        # --- MJ ---
        if mj_file and os.path.exists(mj_file):
            df = pd.read_csv(mj_file)
            keep_rows = []
            for _, row in df.iterrows():
                try:
                    if check_nano(row['Formula']):
                        keep_rows.append(row)
                except:
                    pass
            out_df = pd.DataFrame(keep_rows)
            base, ext = os.path.splitext(mj_file)
            mj_outfile = f"{base}_nano{ext}"
            out_df.to_csv(mj_outfile, index=False, encoding='utf-8-sig')
            print(f"MJ 完成: {mj_outfile} ({len(out_df)} 条)")

        # 处理完成后保存缓存
        _save_nano_cache(nano_cache)

        return cod_outfile, mj_outfile

    except Exception as e:
        print("处理失败:", e)
        return None, None


def run_prediction(cod_nano_file=None, mj_nano_file=None,
                   model_path="models/xgb_optimized.pkl",
                   cif_cache_dir="cache/cif_cache",
                   merged_output=None):
    """
    对 nano 筛选后的 COD / MJ 材料做 band gap (CBM/VBM) 预测。

    - 已有 CBM/VBM 值的材料不再预测，直接沿用。
    - MJ 与 COD 合并为一个文件，相同 Formula 时优先保留 MJ。
    """
    import joblib
    from models.cif import build_row_from_cif_for_cod

    if merged_output is None:
        out_dir = os.path.dirname(cod_nano_file or mj_nano_file or "")
        if not out_dir:
            out_dir = "data"
        project_name = os.path.basename(out_dir)
        os.makedirs("result", exist_ok=True)
        merged_output = f"result/{project_name}_predicted_results.csv"

    model = joblib.load(model_path)
    feature_cols = [
        "Crystal System", "Space Group Symbol", "Space Group Number",
        "Sites", "Volume", "Density",
    ]

    frames = []

    # ==================== MJ ====================
    if mj_nano_file and os.path.exists(mj_nano_file):
        print(f"🔹 Processing MJ: {mj_nano_file}")
        df_mj = pd.read_csv(mj_nano_file)
        missing = [c for c in feature_cols if c not in df_mj.columns]
        if missing:
            print(f"⚠️ MJ 数据缺少列: {missing}, 跳过")
        else:
            has_cbm = "CBM" in df_mj.columns and "VBM" in df_mj.columns
            if has_cbm:
                mask_existing = df_mj["CBM"].notna() & df_mj["VBM"].notna()
                n_exist = mask_existing.sum()
                n_pred = (~mask_existing).sum()
                print(f"  MJ: {n_exist} entries already have CBM/VBM (left empty), {n_pred} need prediction")

                df_mj["CBM_pred"] = None
                df_mj["VBM_pred"] = None

                if n_pred > 0:
                    X = df_mj.loc[~mask_existing, feature_cols]
                    p = model.predict(X)
                    df_mj.loc[~mask_existing, "CBM_pred"] = p[:, 0]
                    df_mj.loc[~mask_existing, "VBM_pred"] = p[:, 1]
            else:
                X = df_mj[feature_cols]
                preds = model.predict(X)
                df_mj["CBM_pred"] = preds[:, 0]
                df_mj["VBM_pred"] = preds[:, 1]

            print(f"✅ MJ 预测完成 ({len(df_mj)} 条)")
            frames.append(df_mj)

    # ==================== COD ====================
    if cod_nano_file and os.path.exists(cod_nano_file):
        print(f"🔹 Processing COD: {cod_nano_file}")
        df_cod = pd.read_csv(cod_nano_file)

        if "file" not in df_cod.columns:
            print("⚠️ COD 数据缺少 'file' 列, 跳过")
        else:
            os.makedirs(cif_cache_dir, exist_ok=True)
            rows = []
            file_ids = df_cod["file"].astype(str).str.strip()

            for file_id in file_ids:
                cif_path = os.path.join(cif_cache_dir, f"{file_id}.cif")

                if not os.path.exists(cif_path):
                    url = f"https://www.crystallography.net/cod/{file_id}.cif"
                    try:
                        urllib.request.urlretrieve(url, cif_path)
                    except Exception as e:
                        print(f"  ⚠️ 下载失败 {file_id}.cif: {e}")
                        continue

                try:
                    struct_row = build_row_from_cif_for_cod(cif_path)
                    rows.append(struct_row)
                except Exception as e:
                    print(f"  ⚠️ 解析失败 {file_id}.cif: {e}")
                    continue

            if rows:
                df_struct = pd.DataFrame(rows)
                X = df_struct[feature_cols]
                preds = model.predict(X)
                df_struct["CBM_pred"] = preds[:, 0]
                df_struct["VBM_pred"] = preds[:, 1]
                print(f"✅ COD 预测完成 ({len(df_struct)} 条)")
                frames.append(df_struct)
            else:
                print("⚠️ 没有 COD CIF 成功解析")

    if not frames:
        print("⚠️ 无数据可合并")
        return None

    # ==================== Merge ====================
    # MJ 在前、COD 在后，按 Formula 去重，保留第一条（即 MJ）
    df_merged = pd.concat(frames, ignore_index=True)
    if "Formula" in df_merged.columns:
        n_before = len(df_merged)
        df_merged = df_merged.drop_duplicates(subset="Formula", keep="first")
        n_dup = n_before - len(df_merged)
        if n_dup > 0:
            print(f"  去除 {n_dup} 条重复 Formula（优先保留 MJ）")

    df_merged.to_csv(merged_output, index=False, encoding="utf-8-sig")
    print(f"✅ 合并结果已保存: {merged_output} ({len(df_merged)} 条)")
    return merged_output
