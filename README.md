# ⚡ Retail E-Commerce Sales & Customer Behavior Data Warehouse & Mining

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![Database](https://img.shields.io/badge/OLAP%20Engine-DuckDB%201.5.6%20%2B%20Parquet-orange.svg)](https://duckdb.org/)
[![Dashboard](https://img.shields.io/badge/UI-Streamlit%20Executive%20Portal-red.svg)](https://streamlit.io/)
[![Dataset](https://img.shields.io/badge/Dataset-Instacart%2033.8M%20Items-green.svg)](https://huggingface.co/datasets/attik/Instacart-Market-Basket-Analysis)
[![Integrity](https://img.shields.io/badge/Validation-9%2F9%20Tests%20Passed-brightgreen.svg)]()

> **Project Title:** *Integrating OLAP and Association Rule Mining on a Retail Data Warehouse for Customer Behavior Analysis*  
> **Course:** Data Warehousing and Mining (DWM)  
> **Live Analytics Dashboard:** `http://localhost:8501` (Executive Obsidian Dark Glassmorphism UI)

---

## 📋 Comprehensive Changelog & Changes Made Till Now

Below is the complete, chronological record of all engineering changes, optimizations, data pipeline executions, and UI redesigns applied to this project:

### 1. Environment & Dependency Management
- **Installed Missing Core Dependencies:** Installed and verified `duckdb` (v1.5.6) and `mlxtend` (v0.23.4) inside the local Python runtime environment.
- **Dependency Pinning:** Verified all dependencies in `requirements.txt` (`duckdb`, `pandas`, `numpy`, `scipy`, `scikit-learn`, `mlxtend`, `plotly`, `streamlit`, `pyarrow`).

### 2. Full-Scale Dataset Ingestion (~680 MB)
- **Automated Ingestion Script:** Executed [`etl/download_data.py`](file:///c:/Users/Manthan/Desktop/DWM%20prj/E-Commerce-Sales-and-Customer-Behavior-Warehouse-Mining-/etl/download_data.py) to stream all 6 official raw CSV files directly from HuggingFace into `data/raw/`:
  - `aisles.csv` (134 aisles)
  - `departments.csv` (21 departments)
  - `products.csv` (49,688 products)
  - `orders.csv` (3,421,083 orders, 103.9 MB)
  - `order_products__train.csv` (1,384,617 line items, 23.5 MB)
  - `order_products__prior.csv` (32,434,489 line items, 550.8 MB)

### 3. End-to-End ETL Pipeline Execution (Galaxy Constellation Schema)
- **Staging Layer ([`etl/01_load_staging.py`](file:///c:/Users/Manthan/Desktop/DWM%20prj/E-Commerce-Sales-and-Customer-Behavior-Warehouse-Mining-/etl/01_load_staging.py)):**
  - Ingested 33.8M raw records into DuckDB vector tables in 1.8 seconds using `read_csv_auto`.
  - Conducted data profiling: 206,209 unique customers, 58.97% overall reorder rate.
- **Dimension Tables ([`etl/02_build_dimensions.py`](file:///c:/Users/Manthan/Desktop/DWM%20prj/E-Commerce-Sales-and-Customer-Behavior-Warehouse-Mining-/etl/02_build_dimensions.py)):**
  - Generated `dim_product` (49,688 SKUs enriched with Aisle and Department hierarchies).
  - Generated `dim_time` (168 temporal slots: 7 Days of Week $\times$ 24 Hours, with weekend and part-of-day flags).
- **Fact Tables & Aggregations ([`etl/03_build_facts.py`](file:///c:/Users/Manthan/Desktop/DWM%20prj/E-Commerce-Sales-and-Customer-Behavior-Warehouse-Mining-/etl/03_build_facts.py)):**
  - Built `fact_order_items` at item grain (**33,819,106 rows** in 1.12s).
  - Built `fact_orders` at order grain (**3,346,083 orders** in 0.73s).
  - Built `dim_customer` with initial customer purchase profiles (**206,209 accounts** in 0.19s).
  - Built materialized rollup table `cube_dept_time` (**22,480 pre-aggregated cells** in 0.58s).
- **Parquet Columnar Export ([`etl/05_export_parquet.py`](file:///c:/Users/Manthan/Desktop/DWM%20prj/E-Commerce-Sales-and-Customer-Behavior-Warehouse-Mining-/etl/05_export_parquet.py)):**
  - Exported all warehouse tables into ZSTD-compressed Parquet files (175.5 MB total footprint in `data/warehouse/`).

### 4. Automated Data Quality & Referential Integrity Validation
- **Executed Suite ([`etl/04_validate.py`](file:///c:/Users/Manthan/Desktop/DWM%20prj/E-Commerce-Sales-and-Customer-Behavior-Warehouse-Mining-/etl/04_validate.py)):**
  - **100% of 9 referential integrity tests passed with zero defects:**
    1. Items Count Matches Staging: `0 mismatch` (PASSED)
    2. Orphan Product Keys (FK check): `0 orphans` (PASSED)
    3. Orphan Time Keys in Items (FK check): `0 orphans` (PASSED)
    4. Orphan Time Keys in Orders (FK check): `0 orphans` (PASSED)
    5. Orphan Customer Keys in Items (FK check): `0 orphans` (PASSED)
    6. Orphan Customer Keys in Orders (FK check): `0 orphans` (PASSED)
    7. Basket Size Consistency: `0 mismatches` (PASSED)
    8. Total Item Aggregation Equality: `0 mismatch` (PASSED)
    9. Pre-Aggregate Cube Equality: `0 mismatch` (PASSED)

### 5. Advanced Machine Learning & Data Mining
- **Adapted RFM Customer Segmentation ([`mining/rfm.py`](file:///c:/Users/Manthan/Desktop/DWM%20prj/E-Commerce-Sales-and-Customer-Behavior-Warehouse-Mining-/mining/rfm.py)):**
  - Extracted Recency gap days ($R$), Frequency order count ($F$), and Monetary proxy items ($M$).
  - Performed silhouette analysis across $k=2\dots6$ on 20,000 samples; fitted final K-Means with optimal $k=4$ (silhouette: `0.4110`) on all 206,209 customers in 0.47s.
  - Classified customer base into 4 business personas:
    - *Casual Occasionals*: 88,150 customers (42.75%)
    - *Infrequent / At-Risk*: 76,138 customers (36.92%)
    - *High-Volume Regulars*: 32,538 customers (15.78%)
    - *Loyal Power Shoppers*: 9,383 customers (4.55%)
  - Persisted segments into `dim_customer.rfm_segment` in DuckDB and re-exported `dim_customer.parquet`.
- **Market Basket Analysis & RQ2 Benchmark ([`mining/basket_mining.py`](file:///c:/Users/Manthan/Desktop/DWM%20prj/E-Commerce-Sales-and-Customer-Behavior-Warehouse-Mining-/mining/basket_mining.py)):**
  - Evaluated Apriori vs FP-Growth scalability across support thresholds ($5\%, 3\%, 2\%, 1\%$).
  - Discovered 9 high-lift global rules (e.g. *Organic Raspberries $\Longrightarrow$ Organic Strawberries*, Lift: 2.40).
- **Slice-Aware Contextual Mining ([`mining/slice_mining.py`](file:///c:/Users/Manthan/Desktop/DWM%20prj/E-Commerce-Sales-and-Customer-Behavior-Warehouse-Mining-/mining/slice_mining.py)):**
  - Proved that dimensional context matters (Jaccard similarity between Weekend Morning and Weekday Evening is only 47.62%).
  - Discovered 7 novel contextual rules on Weekend Mornings (e.g. *Organic Lemon $\Longrightarrow$ Organic Hass Avocado*, Lift: 3.03) that are diluted and lost in global mining.
  - Persisted 45 mined rules into DuckDB table `fact_rules` and exported `fact_rules.parquet`.

### 6. OLAP Querying & Architectural Benchmarking
- **OLAP Analytical Engine ([`sql/run_olap.py`](file:///c:/Users/Manthan/Desktop/DWM%20prj/E-Commerce-Sales-and-Customer-Behavior-Warehouse-Mining-/sql/run_olap.py)):**
  - Executed Roll-up, Drill-down, Slice, Dice, Pivot, Cube, and Grouping Sets operations.
- **Architectural Benchmark Suite ([`benchmark/run_benchmark.py`](file:///c:/Users/Manthan/Desktop/DWM%20prj/E-Commerce-Sales-and-Customer-Behavior-Warehouse-Mining-/benchmark/run_benchmark.py)):**
  - Benchmarked C1 (Normalized), C2 (Galaxy), C3 (Parquet), and C4 (Pre-Agg Cube) across 6 query templates $\times$ 5 iterations.
  - Demonstrated up to **106x speedup** via pre-aggregated summary cubes and **298x speedup** in customer aggregations.
  - Verified scalability curves across 10%, 50%, and 100% data scales.

### 7. Complete Dashboard UI Redesign ([`dashboard/app.py`](file:///c:/Users/Manthan/Desktop/DWM%20prj/E-Commerce-Sales-and-Customer-Behavior-Warehouse-Mining-/dashboard/app.py))
- **Obsidian Luxury Design System:**
  - Ambient deep obsidian dark canvas (`#070a13`) with subtle multi-color radial gradient glows.
  - Modern typography powered by Google Font **Plus Jakarta Sans**.
  - Animated frosted glass cards (`backdrop-filter: blur(20px)`) with gradient top accent borders and hover elevations.
  - Glowing system status indicators (`🟢 DuckDB Warehouse Online`).
- **5 High-Performance Analytical Modules:**
  1. **Executive Overview:** 5 live KPI cards, Top 15 product velocity bar chart, $7 \times 24$ Day $\times$ Hour reorder heatmap, customer lifecycle maturity area chart, and department market share breakdown.
  2. **OLAP Explorer:** Dynamic multiselects for Department (Dice), Part of Day (Dice), Day Type (Slice), and Hierarchy switcher (Department $\rightarrow$ Aisle $\rightarrow$ SKU) with cross-tabulation pivot table.
  3. **Customer Intelligence:** Persona metric cards, 3D/2D behavioral distributions, order velocity vs gap days chart, and actionable CRM strategy matrix.
  4. **Market Basket Mining:** Interactive slice filter (Global, Weekend Morning, Weekday Evening), dynamic Lift and Confidence sliders, bubble scatter chart, and contextual discovery spotlight.
  5. **Performance Benchmarks:** Latency comparison bar chart across C1-C4, dataset scalability curve, and Apriori vs FP-Growth runtime curves.
- **Code Optimization:** Eliminated deprecated Streamlit parameters, optimized query caching (`@st.cache_data`, `@st.cache_resource`), and ensured zero runtime warnings.

---

## 🏗️ Data Warehouse Architecture (Galaxy Schema)

The warehouse implements a **Fact Constellation (Galaxy Schema)** centered around two primary transactional grains and one analytical fact table:

```
                            ┌─────────────────────┐
                            │     dim_time        │
                            │ (168 Time Slots)    │
                            └──────────┬──────────┘
                                       │
                ┌──────────────────────┴──────────────────────┐
                ▼                                             ▼
     ┌───────────────────────┐                     ┌─────────────────────┐
     │   fact_order_items    │                     │     fact_orders     │
     │   (Fine Grain: Item)  │                     │ (Coarse Grain: Order│
     │   33,819,106 Rows     │                     │   3,346,083 Rows    │
     └──────────┬────────────┘                     └──────────┬──────────┘
                │                                             │
      ┌─────────┴─────────┐                         ┌─────────┴─────────┐
      ▼                   ▼                         ▼                   ▼
┌──────────────┐   ┌──────────────┐           ┌──────────────┐   ┌──────────────┐
│ dim_product  │   │ dim_customer │           │ dim_customer │   │  fact_rules  │
│ 49,688 SKUs  │   │ 206,209 Users│           │ (RFM Segments│   │  (45 Mined   │
└──────────────┘   └──────────────┘           └──────────────┘   │  Assoc Rules)│
                                                                 └──────────────┘
```

---

## 🚀 Quick Start: How to Run the Project

### 1. Prerequisites
- Python 3.10, 3.11, or 3.12
- 4 GB+ RAM available

### 2. Setup Virtual Environment & Install Dependencies
```bash
# Clone or navigate to the project directory
cd "E-Commerce-Sales-and-Customer-Behavior-Warehouse-Mining-"

# Install required packages
pip install -r requirements.txt
```

### 3. Run the Automated Pipeline (If building from scratch)
```bash
# Step 1: Download raw datasets (~680 MB from HuggingFace)
python etl/download_data.py

# Step 2: Run ETL pipeline (Staging -> Dimensions -> Facts -> Validation -> Parquet)
python etl/01_load_staging.py
python etl/02_build_dimensions.py
python etl/03_build_facts.py
python etl/04_validate.py
python etl/05_export_parquet.py

# Step 3: Run Machine Learning & Data Mining Suite
python mining/rfm.py
python mining/basket_mining.py
python mining/slice_mining.py

# Step 4: Run OLAP & Architectural Benchmarking
python sql/run_olap.py
python benchmark/run_benchmark.py
```

### 4. Launch the Interactive Analytics Dashboard
```bash
python -m streamlit run dashboard/app.py
```
Open your browser and navigate to **`http://localhost:8501`**.

---

## 📊 Summary of Research & Empirical Findings

### RQ1: Storage & Modeling Query Latencies (Seconds)
| Query Scenario | C1 Normalized | C2 Galaxy Schema | C3 Parquet | C4 Pre-Agg Cube | Speedup (C1 vs C4) |
|---|:---:|:---:|:---:|:---:|:---:|
| **Q1: Dept Rollup** | 0.089s | 0.090s | 0.109s | **0.0012s** | **74x** |
| **Q2: Dept-Day Pivot** | 0.341s | 0.204s | 0.217s | **0.0032s** | **106x** |
| **Q3: Dice Reorder Rate** | 0.066s | 0.031s | 0.097s | **0.0054s** | **12x** |
| **Q5: Cube Dept $\times$ Time** | 0.464s | 0.148s | 0.200s | **0.0053s** | **88x** |
| **Q6: Customer Profile Agg** | 0.418s | **0.0014s** | 0.0032s | N/A | **298x** |

### RQ2: Apriori vs FP-Growth Algorithmic Scalability
- At **5.0% support**: Apriori (`0.017s`) is slightly faster than FP-Growth (`0.403s`) due to minimal candidate itemsets (11 itemsets).
- At **1.0% support**: Apriori begins to experience exponential candidate generation overhead; FP-Growth leverages its compact in-memory FP-Tree structure to identify 162 itemsets without generating candidate pairs.

### RQ3: Slice-Aware Contextual Mining Novelty
- Global mining produces generic association pairs dominated by high-volume staples (e.g. *Organic Bananas*).
- Dimensional slicing isolates temporal behavior: **Weekend Mornings** unveil fresh culinary preparation rules (*Organic Lemon $\Longrightarrow$ Organic Hass Avocado*, Lift: **3.03**; *Organic Gala Apples $\Longrightarrow$ Bag of Organic Bananas*, Lift: **1.70**) with a Jaccard overlap of only **47.62%** compared to weekday evenings.

---

## 📂 Project Directory Structure

```text
E-Commerce-Sales-and-Customer-Behavior-Warehouse-Mining-/
├── data/
│   ├── raw/                 # 6 raw CSV files (aisles, departments, products, orders, op_prior, op_train)
│   └── warehouse/           # dwm.duckdb (full warehouse database) and *.parquet exports
├── etl/
│   ├── download_data.py     # Automated HuggingFace dataset downloader
│   ├── 01_load_staging.py   # Staging loader with automated schema profiling
│   ├── 02_build_dimensions.py # Dim builders: dim_product, dim_time
│   ├── 03_build_facts.py    # Fact builders: fact_order_items, fact_orders, dim_customer, cube_dept_time
│   ├── 04_validate.py       # 9-point referential integrity and consistency test suite
│   └── 05_export_parquet.py # High-performance columnar Parquet exporter (ZSTD)
├── mining/
│   ├── rfm.py               # K-Means customer segmentation (k=4, silhouette 0.411)
│   ├── basket_mining.py     # Apriori vs FP-Growth benchmarks & rule discovery
│   └── slice_mining.py      # Multi-dimensional contextual slice association mining
├── sql/
│   ├── ddl.sql              # Galaxy Constellation schema DDL
│   ├── olap_queries.sql     # Multi-dimensional analytical SQL queries
│   ├── benchmark_queries.sql # Performance evaluation benchmark SQL
│   └── run_olap.py          # Python OLAP query execution engine
├── benchmark/
│   ├── run_benchmark.py     # C1-C4 architectural latency and scalability tester
│   ├── results.csv          # Empirical latency measurements
│   └── scalability_results.csv # Empirical scale measurements (10%, 50%, 100%)
├── dashboard/
│   └── app.py               # Executive Obsidian Luxury Streamlit analytics portal
├── report/
│   ├── DWM_Project_Report.md # Formal comprehensive academic project report
│   ├── IEEE_Research_Paper.md # Research publication manuscript
│   ├── Viva_Defense_Prep.md  # Viva Voce defense Q&A preparation guide
│   └── *.html / *.csv        # Interactive Plotly standalone reports & benchmarks
├── requirements.txt         # Pinned Python package dependencies
└── README.md                # Master documentation and complete project changelog
```

---

## 👥 Contributors & Academic Context
- **Course:** Data Warehousing & Mining (DWM)
- **Dataset:** Instacart Market Basket Analysis (Public Research Dataset)
- **Engine:** DuckDB In-Process Analytical DBMS
