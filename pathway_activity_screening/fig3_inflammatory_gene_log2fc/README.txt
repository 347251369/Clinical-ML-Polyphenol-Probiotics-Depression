Figure 3 — Priority Inflammatory Target Gene Changes
======================================================

What this figure shows
----------------------
A bar chart of log2 fold-change (LPS vs Control) for 10 priority
inflammatory genes in the BV2 microglia reference dataset (GSE103156).
Red bars = upregulated in LPS; grey bars = downregulated.
p-values are annotated above each bar.

The 10 genes are: Nos2, Ptgs2, Il1b, Il6, Ccl2, Cxcl10, Irf7,
C1qa, C1qb, C1qc.

Data source
-----------
source_data/DE_LPS_vs_Control_GSE103156.csv
  - gene: gene symbol
  - log2FC_LPS_vs_Control: log2 fold change
  - pvalue: differential expression p-value

Analysis method
---------------
Differential expression analysis (LPS vs Control) was performed on the
GSE103156 microarray dataset. The 10 genes shown are key inflammatory
markers selected a priori based on their relevance to microglial
activation and neuroinflammation.

How to reproduce
----------------
  python run_generate_figure.py

Output: output/03_core_gene_log2fc.png

Dependencies: pandas, matplotlib

Relevance to Prussian Blue study
---------------------------------
These 10 genes represent core inflammatory readouts. Prussian Blue's
anti-inflammatory effect can be evaluated by measuring the reversal
of these LPS-induced gene expression changes upon PB treatment.
