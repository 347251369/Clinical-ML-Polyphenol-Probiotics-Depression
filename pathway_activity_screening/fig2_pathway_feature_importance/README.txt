Figure 2 — Pathway-Level Machine Learning Feature Importance
=============================================================

What this figure shows
----------------------
A horizontal bar chart displaying random forest feature importance
scores for a pathway-level classifier trained to distinguish
LPS-stimulated vs Control BV2 microglia samples (GSE103156).
Higher importance indicates the pathway is more discriminative
for the inflammatory state.

Data source
-----------
source_data/pathway_feature_importance_GSE103156.csv
  - feature: pathway name
  - random_forest_importance: Gini importance from random forest model

Analysis method
---------------
A random forest classifier was trained using pathway activation scores
as features and treatment group (LPS / Control) as labels. Feature
importance was extracted from the trained model using Gini impurity
decrease. Pathways with higher importance are more predictive of the
LPS-induced inflammatory phenotype.

How to reproduce
----------------
  python run_generate_figure.py

Output: output/02_model_feature_importance.png

Dependencies: pandas, matplotlib

Relevance to Prussian Blue study
---------------------------------
This figure identifies which inflammatory pathways are most informative
for distinguishing LPS-activated vs resting microglia. These pathways
are the most relevant readouts for evaluating Prussian Blue's
anti-inflammatory efficacy.
