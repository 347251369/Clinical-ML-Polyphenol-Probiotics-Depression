from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

BASE = Path(__file__).resolve().parent
DATA = BASE / "source_data" / "DE_LPS_vs_Control_GSE103156.csv"
OUT = BASE / "output" / "03_core_gene_log2fc.png"
OUT.parent.mkdir(exist_ok=True)

focus = ["Nos2", "Ptgs2", "Il1b", "Il6", "Ccl2", "Cxcl10", "Irf7", "C1qa", "C1qb", "C1qc"]
df = pd.read_csv(DATA)
df = df[df["gene"].isin(focus)].copy()
df["gene"] = pd.Categorical(df["gene"], categories=focus, ordered=True)
df = df.sort_values("gene")
colors = ["#C44536" if v >= 0 else "#78909C" for v in df["log2FC_LPS_vs_Control"]]

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 160,
    "savefig.dpi": 300,
})

fig, ax = plt.subplots(figsize=(7.2, 4.2))
ax.axhline(0, color="#90A4AE", linewidth=0.8)
ax.bar(df["gene"].astype(str), df["log2FC_LPS_vs_Control"], color=colors, edgecolor="white", linewidth=0.8)
ax.set_title("Priority inflammatory genes in GSE103156", loc="left", pad=12, fontweight="bold")
ax.set_ylabel("log2FC: LPS vs Control")
ax.tick_params(axis="x", rotation=35)
ax.grid(axis="y", color="#CFD8DC", linewidth=0.7, alpha=0.7)
ax.set_axisbelow(True)
for _, row in df.iterrows():
    v = row["log2FC_LPS_vs_Control"]
    label = f"p={row['pvalue']:.1e}" if row["pvalue"] < 0.01 else f"p={row['pvalue']:.2f}"
    ax.text(str(row["gene"]), v + (0.16 if v >= 0 else -0.22), label,
            ha="center", va="bottom" if v >= 0 else "top", fontsize=7)
fig.tight_layout()
fig.savefig(OUT)
print(f"Saved: {OUT}")
