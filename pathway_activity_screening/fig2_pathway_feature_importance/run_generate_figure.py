from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

BASE = Path(__file__).resolve().parent
DATA = BASE / "source_data" / "pathway_feature_importance_GSE103156.csv"
OUT = BASE / "output" / "02_model_feature_importance.png"
OUT.parent.mkdir(exist_ok=True)

df = pd.read_csv(DATA).sort_values("random_forest_importance", ascending=True)

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 160,
    "savefig.dpi": 300,
})

fig, ax = plt.subplots(figsize=(7.2, 4.8))
ax.barh(df["feature"], df["random_forest_importance"], color="#1B998B", edgecolor="white", linewidth=0.8)
ax.set_title("Pathway-level classifier feature importance", loc="left", pad=12, fontweight="bold")
ax.set_xlabel("Random forest importance")
ax.grid(axis="x", color="#CFD8DC", linewidth=0.7, alpha=0.7)
ax.set_axisbelow(True)
max_value = df["random_forest_importance"].max()
for i, v in enumerate(df["random_forest_importance"]):
    ax.text(v + max_value * 0.015, i, f"{v:.3f}", va="center", fontsize=8, color="#263238")
fig.tight_layout()
fig.savefig(OUT)
print(f"Saved: {OUT}")
