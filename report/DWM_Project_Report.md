# Data Warehousing & Mining (DWM) Final Project Report

**Project Title:** E-Commerce Sales and Customer Behavior Warehouse  
**Paper Title:** *Integrating OLAP and Association Rule Mining on a Retail Data Warehouse for Customer Behavior Analysis*  
**Subject:** Data Warehousing and Mining (DWM)  
**Date:** October 2026  
**Implementation Repository:** [DWM Project Root](file:///c:/Users/Rupali%20Waghmare/Downloads/DWM%20Project)  
**Interactive Dashboard:** `http://localhost:8501`

---

## Executive Summary
This project designs, implements, benchmarks, and analyzes an enterprise-scale analytical data warehouse and data mining system built on a real-world retail dataset of **33,819,106 transaction items** and **3,346,083 orders** placed by **206,209 unique customers**. The system implements an end-to-end architecture encompassing automated ETL ingestion, dimensional modeling using a conformed **Galaxy Schema (Fact Constellation)**, SQL-based **OLAP analytical operations** (`ROLLUP`, `CUBE`, `GROUPING SETS`, Slice, Dice, Pivot), an empirical **architectural performance benchmark** across 4 query engines (addressing RQ1), machine learning-driven **Customer Segmentation** using adapted RFM features with K-Means ($k=4$), an empirical **mining scalability benchmark** comparing Apriori and FP-Growth (addressing RQ2), and a novel **Contextual Slice-Aware Association Rule Mining** framework that integrates OLAP slices with pattern discovery to discover contextual purchasing associations (addressing RQ3). The entire system is topped with an interactive **Streamlit + Plotly analytical dashboard**.

---

## Chapter 1: Introduction

### 1.1 Problem Statement
Modern e-commerce and retail platforms process millions of transactions daily. Traditional transactional databases (OLTP) are optimized for row-by-row consistency and write-heavy workloads, rendering them incapable of executing complex, multi-table aggregate queries across tens of millions of rows. Furthermore, business analytics and data mining have historically operated in isolated silos: business intelligence (BI) teams rely on OLAP for historical aggregation, while data science teams perform unsupervised pattern mining on ad-hoc flat files. 

There is an acute need for an integrated On-Line Analytical Mining (OLAM) framework that merges the multidimensional slicing capabilities of data warehousing with advanced pattern discovery algorithms at scale.

### 1.2 Objectives
1. **Dimensional Modeling:** Architect a conformed Galaxy Schema (Fact Constellation) separating item-level transactions from order-level metrics.
2. **Robust ETL & Integrity:** Build an automated ingestion and data quality pipeline with automated referential integrity validation.
3. **Multidimensional Analytics:** Execute and document standard OLAP operations (Roll-up, Drill-down, Slice, Dice, Pivot, CUBE).
4. **Architectural Benchmarking (RQ1):** Empirically measure query latency and scalability across Normalized relational joins (C1), Galaxy dimensional schema (C2), direct Columnar Parquet scanning (C3), and Pre-aggregated summary tables (C4).
5. **Customer Behavior Modeling:** Segment 206,209 customers using adapted Recency, Frequency, and Monetary proxies via K-Means clustering.
6. **Mining Scalability & Novelty (RQ2 & RQ3):** Contrast Apriori against FP-Growth scalability across support thresholds, and demonstrate that mining within OLAP temporal slices uncovers high-lift contextual rules missed by global baseline mining.
7. **Production Visual Portal:** Deploy a responsive multi-page dashboard for interactive exploration.

### 1.3 Scope and Limitations
* **Dataset Scope:** Built on the Instacart Online Grocery Shopping dataset (~34M rows).
* **Limitations:** The public dataset lacks calendar dates (providing cyclical day-of-week 0–6 and hour 0–23) and item monetary values, necessitating adapted behavioral proxies (order intervals and item basket volume).

---

## Chapter 2: Literature Review & Theoretical Foundations

### 2.1 Dimensional Warehousing Principles
Ralph Kimball's dimensional modeling methodology emphasizes business-process-driven design. Star schemas feature a central fact table surrounded by denormalized dimensions. In enterprise retail, multiple business processes exist at differing grains, demanding a **Galaxy Schema (Fact Constellation)** where multiple fact tables share conformed dimensions (e.g., `dim_time`, `dim_customer`, `dim_product`).

### 2.2 Columnar Storage & Vectorized Execution
Traditional RDBMS store data in row format ($N$-tuples). For analytical queries requiring aggregations over a handful of columns across millions of rows, row scanning incurs severe I/O penalties. Columnar execution engines (e.g., DuckDB, Parquet) store each column contiguously, enabling:
* High compression ratios (ZSTD, Dictionary, Bit-packing).
* Column pruning: only requested columns are read from persistent storage.
* Vectorized SIMD processing: executing operations on arrays of column values simultaneously.

### 2.3 Association Rule Mining Foundations
* **Apriori Algorithm (Agrawal & Srikant, 1994):** Employs the downward-closure property of support (all subsets of a frequent itemset must be frequent). However, it suffers from severe combinatorial explosion when generating candidate itemsets $C_k$ from $L_{k-1}$ and requires repeated database scans.
* **FP-Growth Algorithm (Han et al., 2000):** Overcomes Apriori's bottlenecks by compressing the database into an in-memory Frequent Pattern Tree (FP-Tree) and extracting itemsets through recursive conditional pattern base projections without candidate generation.

---

## Chapter 3: Dataset Ingestion & Exploratory Profiling

### 3.1 Data Provenance
* **Source:** Instacart Market Basket Analysis (Kaggle & Hugging Face open mirror).
* **Ingested Tables:**
  * `stg_orders` (3,421,083 rows, 103.92 MB)
  * `stg_op_prior` (32,434,489 rows, 550.80 MB)
  * `stg_op_train` (1,384,617 rows, 23.54 MB)
  * `stg_products` (49,688 rows, 2.07 MB)
  * `stg_aisles` (134 rows, 2.6 KB)
  * `stg_departments` (21 rows, 270 B)

### 3.2 Profiling & Data Quality Findings
* **Total Transactions:** 3,421,083 orders placed by 206,209 unique customers.
* **Evaluation Split:** `prior` orders account for 93.97%, `train` orders account for 3.84%, and `test` orders account for 2.19% (75,000 orders). Because competition test orders contain no item records, they are filtered out from the analytical warehouse facts.
* **First-Order Anomaly Check:** Exactly 206,209 orders have a `NULL` value for `days_since_prior_order`, perfectly matching the total user count (206,209 1:1), proving `NULL` solely signifies each user's inaugural order.
* **Duplicate Integrity:** Exactly 0 duplicate `(order_id, product_id)` records found in staging.
* **Basket Size Distribution:** Minimum = 1 item, Average = 10.09 items, Median = 8 items, Maximum = 145 items.
* **Overall Reorder Rate:** 58.97% across all historical item purchases.

---

## Chapter 4: Warehouse Architecture & Galaxy Schema Design

### 4.1 Schema Topology (Fact Constellation)
The warehouse employs a conformed Galaxy Schema:
* **`fact_order_items` (Fine Grain):** 1 row per product inside an order (33,819,106 rows). Keys: `order_id`, `product_key`, `customer_key`, `time_key`, `add_to_cart_order`, `reordered`.
* **`fact_orders` (Coarse Grain):** 1 row per completed order (3,346,083 rows). Keys: `order_id`, `customer_key`, `time_key`, `order_number`, `days_since_prior_order`, `basket_size`, `reorder_ratio`.
* **`fact_rules` (Mining Fact):** Stores mined association rules partitioned by dimensional slice.
* **Conformed Dimensions:**
  * `dim_product`: Multi-level hierarchy (`Department` $\rightarrow$ `Aisle` $\rightarrow$ `Product`).
  * `dim_time`: 168 hourly time slots ($7 \text{ Days} \times 24 \text{ Hours}$) enriched with `is_weekend` and `part_of_day`.
  * `dim_customer`: Aggregated customer behavioral profile with RFM cluster segment assignment.
* **Pre-Aggregated Summary Table (`cube_dept_time`):** 22,480 materialized summary rows pre-aggregating Department $\times$ Aisle $\times$ DOW $\times$ Hour.

---

## Chapter 5: ETL Pipeline & Integrity Validation

### 5.1 Pipeline Execution
1. `etl/download_data.py`: Automated stream download of raw CSV files.
2. `etl/01_load_staging.py`: Direct ingestion into DuckDB staging tables (~3.7s total load time).
3. `etl/02_build_dimensions.py`: Constructing `dim_product` (49,688 rows) and `dim_time` (168 rows).
4. `etl/03_build_facts.py`: Unioning order-item records, calculating order-level aggregations, and constructing `dim_customer`.
5. `etl/05_export_parquet.py`: Compressing all warehouse tables to ZSTD-compressed Parquet files.

### 5.2 Automated Referential Integrity Suite (`etl/04_validate.py`)
| # | Validation Rule | Actual Value | Expected | Status | Query Latency |
|:---:|---|:---:|:---:|:---:|:---:|
| 1 | Items Count Matches Staging | 0 diff | 0 | PASSED | 0.309s |
| 2 | Orphan Product Keys (`dim_product` FK) | 0 orphans | 0 | PASSED | 0.173s |
| 3 | Orphan Time Keys in Items (`dim_time` FK) | 0 orphans | 0 | PASSED | 0.159s |
| 4 | Orphan Time Keys in Orders (`dim_time` FK) | 0 orphans | 0 | PASSED | 0.052s |
| 5 | Orphan Customer Keys in Items (`dim_customer` FK) | 0 orphans | 0 | PASSED | 0.197s |
| 6 | Orphan Customer Keys in Orders (`dim_customer` FK) | 0 orphans | 0 | PASSED | 0.043s |
| 7 | Basket Size Mismatch (Granularity Consistency) | 0 mismatches | 0 | PASSED | 0.270s |
| 8 | Total Item Aggregation Equality | 0 diff | 0 | PASSED | 0.033s |
| 9 | Pre-Aggregate Cube Equality (`cube_dept_time`) | 0 diff | 0 | PASSED | 0.000s |

*Result:* **100% pass rate with zero defects** across all 33.8 million records.

---

## Chapter 6: OLAP Multidimensional Analytical Operations

Executed across the full warehouse via [`sql/run_olap.py`](file:///c:/Users/Rupali%20Waghmare/Downloads/DWM%20Project/sql/run_olap.py):

### 6.1 Roll-up Operation
* **Hierarchy:** Product $\rightarrow$ Aisle $\rightarrow$ Department $\rightarrow$ Grand Total.
* **Execution:** Generated 156 hierarchical subtotal combinations in **0.789s**.
* **Insight:** Produce is the largest volume contributor (9,888,378 items), followed by Dairy & Eggs (5,631,067 items) and Snacks (3,006,412 items).

### 6.2 Drill-down Operation
* **Drill Sequence:** Department (`produce`) $\rightarrow$ Aisle (`fresh fruits`) $\rightarrow$ Product SKU.
* **Execution:** Traversed 3 hierarchical tiers in **0.538s**.
* **Micro-Level Insight:** Inside Fresh Fruits, the single highest-velocity SKU in the retailer is `Banana` (491,291 units sold, 84.51% reorder rate), followed by `Bag of Organic Bananas` (394,930 units sold, 83.38% reorder rate).

### 6.3 Slicing & Dicing
* **Slice:** Restricting to weekend orders (`is_weekend = TRUE`) executed in **0.433s**, capturing 3,804,813 produce units and 2,060,795 dairy units.
* **Dice:** Sub-cube restricting Department to (`produce`, `dairy eggs`) during weekend morning hours (8–12 AM) executed in **0.190s**, revealing that early morning hours (8–9 AM) exhibit peak reorder rates (>70%).

### 6.4 Cross-Tabulation Pivot Matrix
* Generated Department $\times$ 7 Days of Week cross-tabulation in **0.465s**.
* **Finding:** Demand peaks sharply on Days 0 and 1 (2.05M produce items on Day 0 vs 1.09M items on Day 4), demonstrating an 87.8% cyclical demand swing.

### 6.5 Materialized Pre-Aggregation Acceleration
* Querying `cube_dept_time` (22,480 rows) rather than scanning the full 33.8M fact rows reduced latency from **0.192s to 0.0162s** (**11.8x acceleration**).

---

## Chapter 7: Performance Engineering & Benchmarking (RQ1)

### 7.1 Experimental Design
Evaluated 6 standardized analytical queries (Q1–Q6) over 5 consecutive runs (cold vs. warm) across 4 configurations:
* **C1: Normalized Staging** (multi-table relational joins).
* **C2: Galaxy Schema** (`fact_*` + conformed `dim_*`).
* **C3: Direct Columnar Parquet** (querying `.parquet` files directly on disk).
* **C4: Pre-Aggregated Summary Cube** (`cube_dept_time`).

### 7.2 Benchmark Results (Warm Latencies in Seconds)
| Query ID | Analytical Query Workload | C1: Normalized (s) | C2: Galaxy (s) | C3: Parquet (s) | C4: Pre-Agg (s) | Speedup Factor |
|:---:|---|:---:|:---:|:---:|:---:|:---:|
| **Q1** | Department Roll-Up | 0.1867s | 0.1826s | 0.1733s | **0.0021s** | C4 is **87.0x faster** than Galaxy |
| **Q2** | Dept $\times$ Day Pivot | 0.5766s | 0.3999s | 0.4256s | **0.0069s** | Galaxy is **30.6% faster**; C4 is **58.0x faster** |
| **Q3** | Dice + Reorder Rate | 0.1250s | **0.0571s** | 0.1460s | **0.0107s** | Galaxy is **2.19x faster** than C1 |
| **Q4** | Top 20 Product SKUs | 0.5283s | 0.5310s | 0.6425s | — | Managed tables beat raw Parquet |
| **Q5** | CUBE(Dept, Time) | 0.7997s | **0.2784s** | 0.4078s | **0.0105s** | Galaxy is **2.87x faster** than C1 |
| **Q6** | Customer Aggregations | 0.6389s | **0.0032s** | **0.0073s** | — | `dim_customer` is **199.7x faster** |

### 7.3 Scalability Experiment
| Data Scale | Estimated Rows | C1: Normalized (s) | C2: Galaxy (s) | Speedup (C1 / C2) |
|:---:|:---:|:---:|:---:|:---:|
| **10% Scale** | ~3.38M | 0.1652s | 0.0731s | **2.26x** |
| **50% Scale** | ~16.91M | 0.2680s | 0.1388s | **1.93x** |
| **100% Scale** | ~33.82M | 0.4009s | 0.2083s | **1.92x** |

*Takeaway:* Dimensional Galaxy modeling provides a consistent **~2x speedup** over normalized joins across all data scales by eliminating multi-way relational joins.

---

## Chapter 8: Data Mining & Pattern Discovery

### 8.1 Adapted RFM Customer Segmentation (K-Means)
Features standardized across 206,209 customers:
* $R$: Average days between orders.
* $F$: Total lifetime orders.
* $M$: Total items purchased.

Evaluated $k \in [2, 6]$; selected **$k=4$** (Silhouette = 0.4131, Inertia = 149,643.9):
* **Loyal Power Shoppers (4.55% / 9,383 users):** High frequency ($F=68.9$), short gap ($R=5.4$ days), high items ($M=838.9$).
* **High-Volume Regulars (15.78% / 32,543 users):** Steady frequency ($F=34.7$), $R=9.15$ days, $M=355.4$.
* **Casual Occasionals (42.75% / 88,147 users):** Bi-weekly cadence ($F=11.8$, $R=12.16$ days, $M=104.8$).
* **Infrequent / At-Risk (36.92% / 76,136 users):** Sparse orders ($F=7.0$, $R=22.94$ days, $M=67.6$).

### 8.2 Apriori vs. FP-Growth Scalability Benchmark (RQ2)
Evaluated on 79,405 order baskets $\times$ 200 products:
* At 5.0% support: Apriori (**0.041s**) vs. FP-Growth (0.252s)
* At 2.0% support: Apriori (0.702s) vs. FP-Growth (**0.468s**)
* At 1.0% support: Apriori (**5.810s**) vs. FP-Growth (**1.111s**) $\rightarrow$ **FP-Growth is 5.23x faster**.
* *Conclusion:* Apriori exhibits an exponential 141.7x slowdown as support declines due to candidate generation, while FP-Growth scales sub-linearly.

### 8.3 Contextual Slice-Aware Mining (RQ3 Novelty)
* **Hypothesis:** Mining within specific OLAP slices reveals context-dependent rules obscured by global averaging.
* **Results:**
  * Global Baseline: 15 rules
  * Weekend Morning: 22 rules
  * Weekday Evening: 11 rules
  * Jaccard Similarity between Weekend Morning and Weekday Evening is only **50.00%**.
* **Discovered Contextual Rules (Exclusive to Weekend Mornings):**
  1. `Organic Cilantro` $\Longrightarrow$ `Limes` (**Lift: 4.83**, Confidence: 28.59%) — Weekend culinary/salsa prep.
  2. `Organic Raspberries` $\Longrightarrow$ `Organic Strawberries` (**Lift: 2.39**, Confidence: 26.39%) — Weekend breakfast smoothie basket.
  3. `Half & Half` $\Longrightarrow$ `Banana` (**Lift: 1.30**, Confidence: 27.84%) — Morning coffee and breakfast routine.

All **48 rules** are persisted in `fact_rules` and `fact_rules.parquet`.

---

## Chapter 9: Analytical Web Dashboard Implementation

Built in [`dashboard/app.py`](file:///c:/Users/Rupali%20Waghmare/Downloads/DWM%20Project/dashboard/app.py) using Streamlit and Plotly, running live on `http://localhost:8501`:
1. **Executive Overview:** 5 KPI metric cards, top 15 velocity bar chart, Day $\times$ Hour reorder heatmap, customer maturity curve.
2. **OLAP Explorer:** Dynamic sliders and dropdowns for Roll-up, Drill-down, Slicing (Weekend/Weekday), and Dicing (Departments $\times$ Part of Day).
3. **Customer Intelligence:** RFM persona donut chart, behavioral matrix, and strategy recommendations.
4. **Association Rules Explorer:** Slice filter, interactive Support vs. Confidence bubble scatter plot (sized/colored by Lift), and searchable rules table.
5. **Architectural Performance:** Live interactive visualizers for RQ1 query latency, scalability, and Apriori vs. FP-Growth curves.

---

## Chapter 10: Conclusion & Future Scope

### 10.1 Key Conclusions
1. The dimensional Galaxy Schema consistently outperforms normalized staging by **~2x**, while pre-aggregated cubes deliver **sub-second speedups of up to 87x**.
2. FP-Growth is fundamentally superior to Apriori for retail basket mining at low support thresholds (5.2x faster at 1% support).
3. Contextual Slice-Aware Mining successfully discovers high-lift behavioral rules (e.g., Cilantro $\rightarrow$ Limes, Lift: 4.83) that global market basket mining averages out and misses.
4. Persisting mined rules into `fact_rules` bridges the gap between data warehousing and data mining.

### 10.2 Future Scope
* **Calendar & Revenue Integration:** Integrating the secondary Olist dataset to incorporate true calendar time dimensions (Year $\rightarrow$ Quarter $\rightarrow$ Month) and pricing revenue metrics.
* **Automated Rule Materialization:** Implementing cron-based incremental mining jobs that automatically re-mine slices as new transactions arrive.
