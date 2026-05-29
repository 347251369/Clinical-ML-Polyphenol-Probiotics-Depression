Figure 1 — LPS-Induced Pathway Activation Ranking
===================================================

What this figure shows
----------------------
A horizontal bar chart ranking biological pathways by their activation
scores (LPS stimulation minus Control) in the BV2 microglial cell line
reference dataset (GSE103156). Higher scores indicate stronger
upregulation of the pathway under LPS-induced inflammatory conditions.

Data source
-----------
source_data/pathway_activation_GSE103156.csv
  - pathway: pathway name (e.g., NOD-like receptor, Toll-like receptor)
  - activation_score_LPS_vs_Control: differential activation score
    (LPS - Control) computed by gene-set enrichment analysis

Analysis method
---------------
Pathway activation scores were calculated from differential expression
data (LPS vs Control) using gene-set enrichment scoring. Each pathway's
mean gene-set z-score was computed per sample, then averaged within
each group, and the difference (LPS minus Control) was taken as the
activation score.

How to reproduce
----------------
  python run_generate_figure.py

Output: output/01_pathway_activation.png

Dependencies: pandas, matplotlib

Relevance to Prussian Blue study
---------------------------------
This figure establishes the baseline inflammatory pathway landscape in
BV2 microglia, identifying which pathways are most strongly activated
by LPS. These pathways serve as candidate targets for Prussian Blue
nanoparticle intervention studies.
