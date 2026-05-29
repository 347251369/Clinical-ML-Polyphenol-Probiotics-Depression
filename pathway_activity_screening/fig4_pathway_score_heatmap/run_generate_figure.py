from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
DATA = BASE / "source_data" / "pathway_scores_GSE103156.csv"
OUT = BASE / "output" / "04_pathway_score_heatmap.png"
OUT.parent.mkdir(exist_ok=True)

scores = pd.read_csv(DATA, index_col=0)
groups = scores.pop("group")
ordered_samples = groups.sort_values().index.tolist()
matrix = scores.loc[ordered_samples].T
vmax = np.nanmax(np.abs(matrix.values))

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 160,
    "savefig.dpi": 300,
})

fig, ax = plt.subplots(figsize=(7.4, 4.8))
im = ax.imshow(matrix.values, aspect="auto", cmap="RdBu_r", vmin=-vmax, vmax=vmax)
ax.set_title("Pathway activity scores across samples", loc="left", pad=12, fontweight="bold")
ax.set_xticks(range(len(matrix.columns)))
ax.set_xticklabels([f"{s}\n{groups.loc[s]}" for s in matrix.columns], rotation=35, ha="right")
ax.set_yticks(range(len(matrix.index)))
ax.set_yticklabels(matrix.index)
cbar = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
cbar.set_label("Mean gene-set z score")
for x, sample in enumerate(matrix.columns):
    ax.add_patch(
        plt.Rectangle(
            (x - 0.5, -0.5),
            1,
            0.18,
            color="#C44536" if groups.loc[sample] == "LPS" else "#2F6C9F",
            clip_on=False,
        )
    )
fig.tight_layout()
fig.savefig(OUT)
print(f"Saved: {OUT}")
