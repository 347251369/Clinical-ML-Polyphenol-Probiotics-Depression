Figure 4 — Sample-Level Pathway Activity Heatmap
==================================================

What this figure shows
----------------------
A heatmap of pathway activity scores across individual BV2 microglia
samples from GSE103156. Each column = one sample, each row = one
pathway. Red = pathway upregulated, blue = pathway downregulated.
The color bar above the heatmap indicates sample group:
red = LPS, blue = Control.

Data source
-----------
source_data/pathway_scores_GSE103156.csv
  - index: sample ID
  - group: LPS or Control
  - remaining columns: pathway names, values are mean gene-set z-scores

Analysis method
---------------
For each sample, pathway activity was scored as the mean z-score of
all genes in the pathway's gene set. This produces a per-sample ×
per-pathway matrix. The heatmap visualizes the full matrix with
RdBu_r colormap centered at zero.

How to reproduce
----------------
  python run_generate_figure.py

Output: output/04_pathway_score_heatmap.png

Dependencies: pandas, matplotlib, numpy

Relevance to Prussian Blue study
---------------------------------
This heatmap provides a comprehensive overview of the pathway
activation landscape at single-sample resolution. It allows visual
inspection of concordance within groups and variation across samples,
serving as a quality-control view for the pathway scoring pipeline.
