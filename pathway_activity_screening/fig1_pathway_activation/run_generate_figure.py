from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

BASE = Path(__file__).resolve().parent
DATA = BASE / "source_data" / "pathway_activation_GSE103156.csv"
OUT = BASE / "output" / "01_pathway_activation.png"
OUT.parent.mkdir(exist_ok=True)

df = pd.read_csv(DATA).sort_values("activation_score_LPS_vs_Control", ascending=True)

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 160,
    "savefig.dpi": 300,
})

fig, ax = plt.subplots(figsize=(7.2, 4.8))
ax.barh(df["pathway"], df["activation_score_LPS_vs_Control"], color="#2F6C9F", edgecolor="white", linewidth=0.8)
ax.set_title("LPS-induced pathway activation in BV2 reference dataset", loc="left", pad=12, fontweight="bold")
ax.set_xlabel("Activation score: LPS minus Control")
ax.grid(axis="x", color="#CFD8DC", linewidth=0.7, alpha=0.7)
ax.set_axisbelow(True)
max_value = df["activation_score_LPS_vs_Control"].max()
for i, v in enumerate(df["activation_score_LPS_vs_Control"]):
    ax.text(v + max_value * 0.015, i, f"{v:.2f}", va="center", fontsize=8, color="#263238")
fig.tight_layout()
fig.savefig(OUT)
print(f"Saved: {OUT}")
