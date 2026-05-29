# Clinical-ML-Polyphenol-Probiotics-Depression — Integrated Research Pipeline

This repository contains two complementary research modules for inorganic materials screening and biological pathway analysis in the context of polyphenol/probiotic interventions for depression:

1. **Filtering Agent** — LLM-driven inorganic materials screening pipeline with band gap prediction
2. **Pathway Activity Screening** — BV2 microglial inflammatory pathway analysis and visualization

---

# Part 1: Filtering Agent

An LLM-driven materials screening pipeline that downloads, filters, and predicts band gap properties for inorganic materials. The pipeline automates four sequential steps: database retrieval, FDA approval screening, nano-form identification, and ML-based CBM/VBM prediction.

## Project Structure

```
material_filter agent/
├── code/
│   ├── driver.py              # Gradio web UI entry point
│   ├── brain.py               # Pipeline state machine (4-step controller)
│   ├── function.py            # Core functions (COD/MP download, FDA, nano, prediction)
│   ├── llm_client.py          # OpenAI-compatible LLM API client
│   ├── page_functions.py      # Gradio page callbacks
│   ├── prompts.py             # LLM prompt templates
│   ├── requirements.txt       # Python dependencies
│   ├── models/                # ML models & training scripts
│   │   ├── cif.py             # CIF file parser for COD structures
│   │   ├── process.py         # Data preprocessing
│   │   ├── trian.py           # XGBoost training with academic plots
│   │   ├── xgb_optimized.pkl  # Trained XGBoost model (CBM/VBM prediction)
│   │   ├── xgb_academic_opt.pkl
│   │   └── xgb_optimized_no_formula.pkl
│   ├── cache/                 # Runtime cache (auto-created)
│   │   ├── nano_cache.csv     # LLM nano-classification cache
│   │   └── cif_cache/         # Downloaded CIF files cache
│   ├── data/                  # Intermediate outputs per query (auto-created)
│   │   └── fe/                # Example output: Fe-containing stable materials
│   └── result/                # Final prediction results (auto-created)
├── datasets/
│   ├── neo4j.dump             # Neo4j FDA chemical database dump
│   └── DATASET_CONFIG.md      # Neo4j database setup guide
├── .env.example               # LLM API configuration template
└── readmec.md                 # Chinese documentation
```

## Prerequisites

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.10+ | Runtime |
| Neo4j | 2025.x | FDA chemical graph database |
| Java | 21 | Required by Neo4j |
| LLM API key | OpenAI-compatible | Drives pipeline decisions (DeepSeek, OpenAI, etc.) |

## Environment Setup

### Step 1 — Install Python

Download and install Python 3.10+ from https://www.python.org/downloads/

Verify:

```bash
python --version
# Python 3.10.x or higher
```

### Step 2 — Create a Virtual Environment

Choose one of the following methods.

**Option A: conda (recommended for scientific computing)**

```bash
conda create -n material_filter python=3.10
conda activate material_filter
```

**Option B: venv (Python built-in)**

```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# Linux / Mac:
source venv/bin/activate
```

Verify your environment is active — you should see `(material_filter)` or `(venv)` in your terminal prompt.

### Step 3 — Install Dependencies

The project dependencies are listed in `code/requirements.txt`:

```
gradio          # Web UI framework
requests        # HTTP client for COD API
pandas          # Data manipulation
mp-api          # Materials Project API client
neo4j           # Neo4j graph database driver
pymatgen        # CIF structure parsing
joblib          # Model serialization
scikit-learn    # ML preprocessing & metrics
xgboost         # Band gap prediction model
matplotlib      # Training visualization
seaborn         # Statistical plots
scipy           # Scientific computing
python-dotenv   # .env file loader
openpyxl        # Excel export (training scripts)
```

Install all dependencies:

```bash
cd "material_filter agent/code"
pip install -r requirements.txt
```

Verify key packages:

```bash
python -c "import gradio; import xgboost; import neo4j; import pymatgen; import dotenv; print('All packages OK')"
```

### Step 4 — Configure LLM API

The application uses an OpenAI-compatible LLM to drive pipeline decisions. Configure your API credentials in a `.env` file.

```bash
# Still in the code/ directory
cp .env.example .env
```

Open `.env` and fill in your own values:

```env
API_BASE=https://api.deepseek.com/v1
API_KEY=sk-your-api-key-here
BRAIN_MODEL=deepseek-v4-flash
```

| Variable | Description |
|----------|-------------|
| `API_BASE` | API endpoint URL |
| `API_KEY` | Your API key (must start with `sk-`) |
| `BRAIN_MODEL` | Model name to use for decision-making |

Supported providers:
- DeepSeek: `API_BASE=https://api.deepseek.com/v1`
- OpenAI: `API_BASE=https://api.openai.com/v1`
- Self-hosted vLLM / Ollama: `API_BASE=http://localhost:8000/v1`

> **Note:** The `.env` file is git-ignored and will NOT be uploaded to GitHub.

### Step 5 — Install & Configure Neo4j Database

The FDA screening step queries a Neo4j graph database. We provide a pre-built database dump with FDA-approved chemical records.

#### 5.1 Install Neo4j Desktop

Download from https://neo4j.com/download/
Install and launch Neo4j Desktop.

#### 5.2 Create a Local DBMS

1. In Neo4j Desktop, click **New** → **Create project** (name it e.g. "Material Filter")
2. Click **Add** → **Local DBMS**
3. Choose version **2025.x**
4. Set password: `12345678`
5. **Do NOT start the database yet**

#### 5.3 Restore the Database Dump

Open a terminal in the Neo4j DBMS directory, or use Neo4j Desktop's built-in Terminal (select your DBMS → **Terminal**).

```bash
# Navigate to your DBMS bin directory, or use the built-in Terminal
neo4j-admin database load neo4j \
  --from-path="<project-root>/material_filter agent/datasets/neo4j.dump" \
  --overwrite-destination=true
```

Replace `<project-root>` with the actual path to this repository.

#### 5.4 Start and Verify

1. In Neo4j Desktop, **Start** the DBMS
2. Open **Neo4j Browser** (the blue "Open" button)
3. Run this Cypher query to verify:

```cypher
MATCH (c:Chemical) RETURN count(c) AS Total_Chemicals;
```

You should see a non-zero count.

#### 5.5 Connection Settings

The application connects with these defaults (in `code/function.py` line ~109):

```python
Neo4jFDA(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="12345678"
)
```

If you used a different password, update it in `code/function.py`.

> For more details, see [material_filter agent/datasets/DATASET_CONFIG.md](material_filter%20agent/datasets/DATASET_CONFIG.md).

### Step 6 — (Optional) Configure Materials Project API Key

The pipeline queries the [Materials Project](https://next-gen.materialsproject.org/) API. A default key is embedded in the code, but it may be rate-limited. For reliable use, register your own:

1. Go to https://next-gen.materialsproject.org/api
2. Register and generate an API key
3. Update `code/brain.py` line ~62:

```python
get_materials_data(
    api_key="your-mp-api-key",
    ...
)
```

## Configuration Checklist

Before running, make sure:

- [ ] Python 3.10+ installed
- [ ] Virtual environment created and activated
- [ ] Dependencies installed via `pip install -r requirements.txt`
- [ ] `.env` file created from `.env.example` with your LLM API credentials
- [ ] Neo4j Desktop installed, DBMS created (password `12345678`)
- [ ] `neo4j.dump` restored to the DBMS and database is running
- [ ] (Optional) Materials Project API key registered and updated

## Run

```bash
cd "material_filter agent/code"
python driver.py
```

Open http://localhost:8080 in your browser. The Gradio chat interface will appear.

## Pipeline Flow

The pipeline has 4 steps, each gated by an LLM-powered confirmation:

```
Step 1 (_FILTER)    → Download materials from COD & Materials Project
Step 2 (_FDA)       → Filter by FDA approval status (Neo4j lookup + LLM judgment)
Step 3 (_NANO)      → Identify nano-form materials (LLM classification)
Step 4 (_PREDICT)   → Predict CBM/VBM band gaps (XGBoost model)
```

After Step 4, you can enter a new query to start a fresh screening without restarting.

## Example Conversation

This example shows a complete run searching for Fe-containing stable materials:

```
User:
  Download stable materials containing Fe from COD and Materials Project databases.

Agent:
  ✅ Step 1/4 — Database download complete.
  Downloaded materials from COD and Materials Project:
    • COD: data/fe/filtered_materials_cod.csv
    • Materials Project: data/fe/filtered_materials_mj.csv

  Next: FDA screening — filter materials by FDA approval status.
  Proceed with FDA screening? (yes / no)

User:
  yes

Agent:
  ✅ Step 2/4 — FDA screening complete.
  Filtered results (FDA-approved only):
    • COD: data/fe/filtered_materials_cod_fda.csv
    • Materials Project: data/fe/filtered_materials_mj_fda.csv

  Next: Nano screening — identify materials with plausible nano forms.
  Proceed with nano screening? (yes / no)

User:
  yes

Agent:
  ✅ Step 3/4 — Nano screening complete.
  Filtered results (nano-materials only):
    • COD: data/fe/filtered_materials_cod_fda_nano.csv
    • Materials Project: data/fe/filtered_materials_mj_fda_nano.csv

  Next: Band gap prediction — use ML model to predict CBM/VBM.
  Proceed with band gap prediction? (yes / no)

User:
  yes

Agent:
  ✅ Step 4/4 — Band gap prediction complete.
  Merged result (MJ priority for duplicate formulas):
    • result/fe_predicted_results.csv

  All 4 steps finished. Download the result file above.
  To start a new screening, enter new database download requirements.
```

At each step, the LLM interprets user intent flexibly — "sure", "go ahead", "continue", "ok" all mean Yes; "stop", "cancel", "skip" mean No.

## Output Description

| Step | Output Files | Description |
|------|-------------|-------------|
| 1 | `data/{elements}/*_cod.csv`, `*_mj.csv` | Raw downloads from COD and Materials Project |
| 2 | `data/{elements}/*_fda.csv` | FDA-approved subset |
| 3 | `data/{elements}/*_nano.csv` | Nano-form subset |
| 4 | `result/{elements}_predicted_results.csv` | Final result with predicted CBM/VBM |

For multi-element queries (e.g., Fe + Mn), the directory is `data/fe_mn/` and the result is `result/fe_mn_predicted_results.csv`.

## Troubleshooting

| Symptom | Solution |
|---------|----------|
| `No module named 'xgboost'` | Run `pip install xgboost` in your environment |
| `No module named 'dotenv'` | Run `pip install python-dotenv` |
| `API_KEY is not set` | Copy `.env.example` to `.env` and fill in your credentials |
| `API_KEY need begin with 'sk-'` | Ensure your API key starts with `sk-` |
| Neo4j connection refused (`bolt://localhost:7687`) | Ensure the Neo4j DBMS is **started** in Neo4j Desktop |
| Neo4j authentication error | Verify password matches `12345678` (or update `code/function.py`) |
| Materials Project rate limit | Register your own API key at https://next-gen.materialsproject.org/api |
| COD query returns no data | COD server may be slow; check your network and retry |
| Gradio port 8080 already in use | Change the port in `driver.py` line ~57: `server_port=8080` |

## Notes

- `cache/nano_cache.csv` persists LLM nano-classification results to reduce API calls across runs.
- COD CIF files are cached in `cache/cif_cache/` to avoid re-downloading.
- The XGBoost models in `models/` predict CBM (Conduction Band Minimum) and VBM (Valence Band Maximum) in eV.
- You can run a new screening after Step 4 completes by simply entering new requirements — no restart needed.

---

# Part 2: Pathway Activity Screening

Inflammatory pathway activity analysis in BV2 microglial cells using the GSE103156 reference dataset (LPS vs Control). This module produces four publication-quality figures characterizing the inflammatory pathway landscape.

## Project Structure

```
pathway_activity_screening/
├── fig1_pathway_activation/
│   ├── run_generate_figure.py                     # Figure generation script
│   ├── source_data/
│   │   └── pathway_activation_GSE103156.csv       # Pathway activation scores
│   ├── output/
│   │   └── 01_pathway_activation.png              # Generated figure
│   ├── final_plot_data_fig1_pathway_activation.xlsx
│   └── README.txt                                 # Figure documentation
├── fig2_pathway_feature_importance/
│   ├── run_generate_figure.py
│   ├── source_data/
│   │   └── pathway_feature_importance_GSE103156.csv
│   ├── output/
│   │   └── 02_model_feature_importance.png
│   ├── final_plot_data_fig2_pathway_feature_importance.xlsx
│   └── README.txt
├── fig3_inflammatory_gene_log2fc/
│   ├── run_generate_figure.py
│   ├── source_data/
│   │   └── DE_LPS_vs_Control_GSE103156.csv
│   ├── output/
│   │   └── 03_core_gene_log2fc.png
│   ├── final_plot_data_fig3_inflammatory_gene_log2fc.xlsx
│   └── README.txt
└── fig4_pathway_score_heatmap/
    ├── run_generate_figure.py
    ├── source_data/
    │   └── pathway_scores_GSE103156.csv
    ├── output/
    │   └── 04_pathway_score_heatmap.png
    ├── final_plot_data_fig4_pathway_score_heatmap.xlsx
    └── README.txt
```

## Dataset

All figures are based on **GSE103156**, a public microarray dataset from the GEO database profiling BV2 mouse microglial cells under LPS stimulation vs Control conditions.

## Figures Overview

### Figure 1 — LPS-Induced Pathway Activation Ranking

Horizontal bar chart of pathway activation scores (LPS minus Control) ranked from highest to lowest. Identifies which biological pathways are most strongly upregulated upon LPS stimulation.

- **Script:** `fig1_pathway_activation/run_generate_figure.py`
- **Output:** `01_pathway_activation.png`
- **Details:** [fig1_pathway_activation/README.txt](pathway_activity_screening/fig1_pathway_activation/README.txt)

### Figure 2 — Pathway-Level Machine Learning Feature Importance

Random forest feature importance for a pathway-level classifier distinguishing LPS vs Control. Higher importance = pathway is more discriminative for the inflammatory state.

- **Script:** `fig2_pathway_feature_importance/run_generate_figure.py`
- **Output:** `02_model_feature_importance.png`
- **Details:** [fig2_pathway_feature_importance/README.txt](pathway_activity_screening/fig2_pathway_feature_importance/README.txt)

### Figure 3 — Priority Inflammatory Target Gene Changes

Log2 fold-change bar chart for 10 key inflammatory genes (Nos2, Ptgs2, Il1b, Il6, Ccl2, Cxcl10, Irf7, C1qa, C1qb, C1qc) with p-value annotations.

- **Script:** `fig3_inflammatory_gene_log2fc/run_generate_figure.py`
- **Output:** `03_core_gene_log2fc.png`
- **Details:** [fig3_inflammatory_gene_log2fc/README.txt](pathway_activity_screening/fig3_inflammatory_gene_log2fc/README.txt)

### Figure 4 — Sample-Level Pathway Activity Heatmap

Heatmap of pathway activity z-scores across all individual BV2 samples, grouped by LPS vs Control. Red/blue colormap centered at zero.

- **Script:** `fig4_pathway_score_heatmap/run_generate_figure.py`
- **Output:** `04_pathway_score_heatmap.png`
- **Details:** [fig4_pathway_score_heatmap/README.txt](pathway_activity_screening/fig4_pathway_score_heatmap/README.txt)

## Reproduce All Figures

```bash
# Navigate to each figure folder and run the script
cd "pathway_activity_screening/fig1_pathway_activation"
python run_generate_figure.py

cd "../fig2_pathway_feature_importance"
python run_generate_figure.py

cd "../fig3_inflammatory_gene_log2fc"
python run_generate_figure.py

cd "../fig4_pathway_score_heatmap"
python run_generate_figure.py
```

Dependencies: `pandas`, `matplotlib`, `numpy`

## Relevance to Candidate Material Validation

The pathway screening module provides the baseline inflammatory landscape in BV2 microglia for evaluating material candidates (e.g., Prussian Blue) discovered by Part 1:

1. **Figure 1** identifies which pathways are activated by LPS — candidate intervention targets.
2. **Figure 2** identifies which pathways best discriminate inflammatory vs resting states — the most informative readouts.
3. **Figure 3** provides specific gene-level targets for qPCR validation of a candidate's anti-inflammatory effect.
4. **Figure 4** provides sample-level quality control for the pathway scoring pipeline.

Together, these analyses provide the biological rationale for selecting inflammatory readouts when evaluating candidate material efficacy in microglial inflammation models.

---

# Repository Overview

```
Clinical-ML-Polyphenol-Probiotics-Depression/
├── README.md                           # This file
├── material_filter agent/              # Part 1: Materials screening pipeline
│   ├── code/
│   ├── datasets/
│   ├── .env.example
│   └── readmec.md                      # Chinese documentation
└── pathway_activity_screening/         # Part 2: Pathway activity analysis
    ├── fig1_pathway_activation/
    ├── fig2_pathway_feature_importance/
    ├── fig3_inflammatory_gene_log2fc/
    └── fig4_pathway_score_heatmap/
```

## Research Context

This project investigates the gut-brain axis in depression, focusing on polyphenol and probiotic interventions. The repository supports two key aspects of the research:

1. **Material discovery** (Part 1): Broadly screen inorganic materials from public crystallography databases (COD, Materials Project), filter by FDA approval status and nano-form feasibility, and predict electronic band structure (CBM/VBM) using machine learning. Prussian Blue emerged as a candidate nanozyme from this pipeline.

2. **Biological characterization** (Part 2): Characterize the inflammatory pathway activation landscape in BV2 microglia, establishing baseline readouts for evaluating candidate material efficacy in subsequent in vitro experiments.
