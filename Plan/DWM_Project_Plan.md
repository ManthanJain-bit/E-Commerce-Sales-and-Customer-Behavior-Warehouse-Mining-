# DWM Detailed Project Document

**Project:** E-Commerce Sales and Customer Behavior Warehouse
**Paper:** *Integrating OLAP and Association Rule Mining on a Retail Data Warehouse for Customer Behavior Analysis*
**Subject:** Data Warehousing and Mining (DWM)

> How to use this document: Part A lists every source/tool with alternatives. Part B is the section-wise implementation (do it in order). Part C covers experiments, the report, the paper, and risks. Where results are needed, tables are left blank on purpose: fill them only with numbers from your own runs.

---

# PART A: SOURCES AND ALTERNATIVES

## A1. Datasets

| Role | Dataset | Size | Has real dates? | Has price? | Link |
|---|---|---|---|---|---|
| **Primary** | Instacart Market Basket Analysis | ~3.4M orders, ~32M order-product rows | No (day-of-week, hour, days since prior order only) | No | https://www.kaggle.com/c/instacart-market-basket-analysis/data |
| Primary (original page) | Instacart 2017 grocery dataset | same | No | No | https://www.instacart.com/datasets/grocery-shopping-2017 |
| **Secondary** | Olist Brazilian E-commerce | ~100K orders, 9 tables | Yes (timestamps) | Yes | https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce |

**Alternatives (use if Instacart is a problem or you want real dates at large scale):**

| Alternative | Why consider it | Link |
|---|---|---|
| REES46 eCommerce behavior data (multi-category store) | Hundreds of millions of events with real timestamps, price, brand, category. Very large. | https://www.kaggle.com/datasets/mkechinov/ecommerce-behavior-data-from-multi-category-store |
| Online Retail II (UCI) | ~1M transactions, real dates, price, country. Small but clean. | https://archive.ics.uci.edu/dataset/502/online+retail+ii |
| Dunnhumby "The Complete Journey" | Household-level grocery data over 2 years, with dates and spend. | https://www.dunnhumby.com/source-files/ |
| Amazon Reviews 2023 (McAuley Lab) | Very large product and review data, with timestamps and categories. | https://amazon-reviews-2023.github.io/ |
| TPC-DS (synthetic benchmark) | Scalable retail warehouse generator (any size) with a standard schema and queries. Great for pure performance benchmarking. | https://www.tpc.org/tpcds/ |

> Verify each link and the dataset's license/terms before use (some are non-commercial, research/education only), and cite the source in your report and paper.

**Decision guide**

| If you want... | Use |
|---|---|
| Simplest path that satisfies "large data" + mining | Instacart only (Option B) |
| Large data AND real calendar/geography drill-down | Instacart + Olist (Option A, hybrid galaxy) |
| Large data with real dates in a single dataset | REES46 |
| Pure OLAP performance study at controllable scale | TPC-DS |
| Small, safe fallback | Olist or Online Retail II |

## A2. Tools and Alternatives

| Layer | Primary choice | Alternatives |
|---|---|---|
| Language | Python 3.10+ | R, Java (for Spark/Mondrian) |
| Data loading / ETL | DuckDB + pandas | Polars, PySpark, Dask, Apache Airflow (orchestration), dbt (SQL transformations), SSIS / Talend / Pentaho (GUI ETL tools) |
| Warehouse engine | DuckDB (columnar, no server) | PostgreSQL, ClickHouse, MySQL, SQL Server, SQLite (small only), Spark SQL, Google BigQuery (free tier) |
| Storage format | Parquet | CSV (baseline), native DuckDB tables |
| OLAP | SQL (`ROLLUP`, `CUBE`, `GROUPING SETS`, pivots) | Apache Kylin, Mondrian (Pentaho), Microsoft SSAS, Apache Druid, pandas `pivot_table` |
| Frequent patterns | `mlxtend` (Apriori, FP-Growth) | `efficient-apriori`, PySpark MLlib `FPGrowth`, SPMF (Java), Orange Data Mining, Weka |
| Clustering | scikit-learn (K-Means) | MiniBatchKMeans (for scale), DBSCAN, Hierarchical |
| Dashboard | Streamlit + Plotly | Power BI, Apache Superset, Metabase, Tableau Public, Plotly Dash, Grafana |
| Diagrams | draw.io, Mermaid | dbdiagram.io, Lucidchart, MySQL Workbench |
| Version control | Git + GitHub | GitLab |
| Report / paper | Overleaf (LaTeX, IEEE template) | MS Word, Google Docs |

## A3. Hardware guidance

| Setup | What works |
|---|---|
| 8 GB RAM laptop | DuckDB + Parquet works fine. Mine rules on a sample (e.g., 100K orders, top 200 products). |
| 16 GB RAM | Comfortable for the full warehouse; mine on 200-500K orders. |
| Limited RAM / slow disk | Use Google Colab or Kaggle Notebooks for the mining step; keep Parquet files on Drive. |

## A4. Key references to cite (verify details and add exact citations)

- Agrawal & Srikant (1994), *Fast Algorithms for Mining Association Rules* (Apriori)
- Han, Pei & Yin (2000), *Mining Frequent Patterns without Candidate Generation* (FP-Growth)
- Chaudhuri & Dayal (1997), *An Overview of Data Warehousing and OLAP Technology*
- Kimball & Ross, *The Data Warehouse Toolkit* (dimensional modeling)
- Han, Kamber & Pei, *Data Mining: Concepts and Techniques*
- Instacart dataset page and the Kaggle competition (as data source)
- Documentation of the tools you use (DuckDB, mlxtend, Streamlit)

---

# PART B: SECTION-WISE IMPLEMENTATION

## Section 0: Project setup

**Folder structure**

```
dwm-ecommerce/
├── data/
│   ├── raw/                 # Kaggle CSVs (git-ignored)
│   └── warehouse/           # dwm.duckdb, parquet exports
├── etl/
│   ├── 01_load_staging.py
│   ├── 02_build_dimensions.py
│   ├── 03_build_facts.py
│   └── 04_validate.py
├── sql/
│   ├── ddl.sql
│   ├── olap_queries.sql
│   └── benchmark_queries.sql
├── mining/
│   ├── basket_mining.py
│   ├── rfm.py
│   └── slice_mining.py
├── benchmark/
│   └── run_benchmark.py
├── dashboard/
│   └── app.py
├── report/
├── requirements.txt
└── README.md
```

**requirements.txt**

```
duckdb
pandas
numpy
scipy
scikit-learn
mlxtend
plotly
streamlit
networkx
pyarrow
```

**Environment**

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**Download data** (Kaggle account needed; accept the competition rules first)

```bash
pip install kaggle
kaggle competitions download -c instacart-market-basket-analysis -p data/raw
unzip data/raw/instacart-market-basket-analysis.zip -d data/raw
# the inner files may also be zipped; unzip each (orders.csv.zip etc.)
```

Alternative: download manually from the Kaggle page and place CSVs in `data/raw/`.

Expected files: `orders.csv`, `order_products__prior.csv`, `order_products__train.csv`, `products.csv`, `aisles.csv`, `departments.csv`.

---

## Section 1: Data understanding and profiling

**Goal:** know the data before modeling; collect facts for the report.

```python
# etl/01_load_staging.py
import duckdb, pathlib
pathlib.Path("data/warehouse").mkdir(parents=True, exist_ok=True)
con = duckdb.connect("data/warehouse/dwm.duckdb")

tables = {
    "stg_orders": "orders.csv",
    "stg_aisles": "aisles.csv",
    "stg_departments": "departments.csv",
    "stg_products": "products.csv",
    "stg_op_prior": "order_products__prior.csv",
    "stg_op_train": "order_products__train.csv",
}
for t, f in tables.items():
    con.execute(f"CREATE OR REPLACE TABLE {t} AS SELECT * FROM read_csv_auto('data/raw/{f}')")
    n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"{t}: {n:,} rows")
```

**Profiling queries to run and record in the report**

```sql
-- overall counts
SELECT COUNT(*) AS orders, COUNT(DISTINCT user_id) AS users FROM stg_orders;

-- orders by eval_set (prior / train / test)
SELECT eval_set, COUNT(*) FROM stg_orders GROUP BY eval_set;

-- null check (days_since_prior_order is NULL for each user's first order)
SELECT COUNT(*) FILTER (WHERE days_since_prior_order IS NULL) AS null_gap FROM stg_orders;

-- basket size distribution
SELECT basket, COUNT(*) AS orders FROM (
  SELECT order_id, COUNT(*) AS basket FROM stg_op_prior GROUP BY order_id
) GROUP BY basket ORDER BY basket;

-- overall reorder rate
SELECT AVG(reordered) FROM stg_op_prior;

-- duplicate check
SELECT COUNT(*) - COUNT(DISTINCT (order_id, product_id)) AS dups FROM stg_op_prior;
```

**Deliverables for this section:** a data-profile table (rows, columns, nulls, duplicates per table), 3 to 4 EDA charts (orders per hour, orders per day-of-week, basket-size histogram, reorder rate).

**Notes**
- `eval_set = 'test'` orders have **no** product rows in the public data. Exclude them from the warehouse.
- `order_dow` meaning is **not documented** by Instacart. Peaks on values 0 and 1 suggest those are the weekend days, so many analyses treat 0/1 as Saturday/Sunday. Treat this as an assumption and state it in the report.

---

## Section 2: Warehouse design

### 2.1 Requirements and business questions (write these in the report)
1. Which departments/aisles/products drive the most sales and reorders?
2. How does demand vary by hour and day?
3. How does reorder behavior vary by department and time?
4. Which products are bought together, and does that change by context?
5. What customer segments exist, and how do they differ?

### 2.2 Grain
- `fact_order_items`: one row per product in an order
- `fact_orders`: one row per order

### 2.3 Galaxy schema (fact constellation)

```
dim_product ──┐                      ┌── dim_customer
              ├── fact_order_items ──┤
dim_time ─────┤                      │
              └── fact_orders ───────┘
dim_time, dim_customer shared by both facts (conformed dimensions)
fact_rules (mining output) links to dim_time slice attributes
```

### 2.4 Tables

**dim_product** (department → aisle → product hierarchy)
| Column | Type |
|---|---|
| product_key (PK) | INTEGER |
| product_name | VARCHAR |
| aisle_id, aisle | INTEGER, VARCHAR |
| department_id, department | INTEGER, VARCHAR |

**dim_time** (168 rows: 7 days × 24 hours)
| Column | Type |
|---|---|
| time_key (PK) = dow*24 + hour | INTEGER |
| order_dow, hour | INTEGER |
| day_label | VARCHAR ('Day 0'...'Day 6' or your assumed names) |
| is_weekend | BOOLEAN (assumption, see Section 1) |
| part_of_day | VARCHAR (Night/Morning/Afternoon/Evening) |

**dim_customer**
| Column | Type |
|---|---|
| customer_key (PK) = user_id | INTEGER |
| total_orders, total_items, avg_basket_size | numeric |
| avg_days_between_orders | DOUBLE |
| rfm_segment | VARCHAR (filled after Section 7) |

**fact_order_items**
| Column | Type |
|---|---|
| order_id | INTEGER |
| product_key (FK) | INTEGER |
| customer_key (FK) | INTEGER |
| time_key (FK) | INTEGER |
| add_to_cart_order | INTEGER |
| reordered | TINYINT (0/1) |

**fact_orders**
| Column | Type |
|---|---|
| order_id (PK) | INTEGER |
| customer_key (FK), time_key (FK) | INTEGER |
| order_number | INTEGER |
| days_since_prior_order | DOUBLE (nullable) |
| basket_size | INTEGER |
| reorder_ratio | DOUBLE |

**fact_rules** (mining output, created in Section 8)
| Column | Type |
|---|---|
| slice_name, antecedent, consequent | VARCHAR |
| support, confidence, lift | DOUBLE |

### 2.5 Deliverables
Schema diagram (draw.io/Mermaid), data dictionary, grain statement, hierarchy diagram.

---

## Section 3: ETL implementation

### 3.1 Build dimensions

```python
# etl/02_build_dimensions.py
import duckdb
con = duckdb.connect("data/warehouse/dwm.duckdb")

con.execute("""
CREATE OR REPLACE TABLE dim_product AS
SELECT p.product_id AS product_key, p.product_name,
       a.aisle_id, a.aisle, d.department_id, d.department
FROM stg_products p
JOIN stg_aisles a USING (aisle_id)
JOIN stg_departments d USING (department_id)
""")

con.execute("""
CREATE OR REPLACE TABLE dim_time AS
SELECT d.dow * 24 + h.hr AS time_key,
       d.dow AS order_dow,
       h.hr  AS hour,
       'Day ' || d.dow AS day_label,
       d.dow IN (0, 1) AS is_weekend,            -- ASSUMPTION: see Section 1
       CASE WHEN h.hr BETWEEN 5  AND 11 THEN 'Morning'
            WHEN h.hr BETWEEN 12 AND 16 THEN 'Afternoon'
            WHEN h.hr BETWEEN 17 AND 21 THEN 'Evening'
            ELSE 'Night' END AS part_of_day
FROM range(0, 7) AS d(dow), range(0, 24) AS h(hr)
""")
```

### 3.2 Build facts

```python
# etl/03_build_facts.py
import duckdb
con = duckdb.connect("data/warehouse/dwm.duckdb")

# union of all order-product rows that exist
con.execute("""
CREATE OR REPLACE VIEW stg_op AS
SELECT * FROM stg_op_prior
UNION ALL
SELECT * FROM stg_op_train
""")

con.execute("""
CREATE OR REPLACE TABLE fact_order_items AS
SELECT op.order_id,
       op.product_id AS product_key,
       o.user_id AS customer_key,
       o.order_dow * 24 + o.order_hour_of_day AS time_key,
       op.add_to_cart_order,
       op.reordered
FROM stg_op op
JOIN stg_orders o USING (order_id)
""")

con.execute("""
CREATE OR REPLACE TABLE fact_orders AS
SELECT o.order_id,
       o.user_id AS customer_key,
       o.order_dow * 24 + o.order_hour_of_day AS time_key,
       o.order_number,
       o.days_since_prior_order,
       COUNT(op.product_id) AS basket_size,
       AVG(op.reordered)    AS reorder_ratio
FROM stg_orders o
JOIN stg_op op USING (order_id)        -- inner join drops 'test' orders (no items)
GROUP BY o.order_id, o.user_id, o.order_dow, o.order_hour_of_day,
         o.order_number, o.days_since_prior_order
""")

con.execute("""
CREATE OR REPLACE TABLE dim_customer AS
SELECT customer_key,
       COUNT(*) AS total_orders,
       SUM(basket_size) AS total_items,
       AVG(basket_size) AS avg_basket_size,
       AVG(days_since_prior_order) AS avg_days_between_orders,
       CAST(NULL AS VARCHAR) AS rfm_segment
FROM fact_orders
GROUP BY customer_key
""")
```

### 3.3 Validation (record results in the report)

```python
# etl/04_validate.py
import duckdb
con = duckdb.connect("data/warehouse/dwm.duckdb")
checks = {
 "items match staging":
   "SELECT (SELECT COUNT(*) FROM fact_order_items) - (SELECT COUNT(*) FROM stg_op o JOIN stg_orders s USING(order_id))",
 "orphan products":
   "SELECT COUNT(*) FROM fact_order_items f LEFT JOIN dim_product p ON f.product_key=p.product_key WHERE p.product_key IS NULL",
 "orphan time keys":
   "SELECT COUNT(*) FROM fact_order_items f LEFT JOIN dim_time t ON f.time_key=t.time_key WHERE t.time_key IS NULL",
 "orphan customers":
   "SELECT COUNT(*) FROM fact_order_items f LEFT JOIN dim_customer c ON f.customer_key=c.customer_key WHERE c.customer_key IS NULL",
 "basket size mismatch":
   "SELECT COUNT(*) FROM fact_orders o JOIN (SELECT order_id, COUNT(*) n FROM fact_order_items GROUP BY 1) i USING(order_id) WHERE o.basket_size <> i.n",
}
for name, q in checks.items():
    print(f"{name}: {con.execute(q).fetchone()[0]}")   # expect 0 for all
```

### 3.4 Export to Parquet (needed for the benchmark)

```python
con.execute("COPY fact_order_items TO 'data/warehouse/fact_order_items.parquet' (FORMAT PARQUET)")
con.execute("COPY fact_orders TO 'data/warehouse/fact_orders.parquet' (FORMAT PARQUET)")
```

### 3.5 Alternative: PostgreSQL version
Use `CREATE TABLE` DDL with primary/foreign keys, load with `COPY ... FROM '/path/file.csv' CSV HEADER`, then build the same tables with the SQL above (replace `range(...)` with `generate_series(...)`). Add indexes in Section 6.

---

## Section 4: OLAP implementation

Run these in `sql/olap_queries.sql`, save outputs as tables/charts for the report. Each query demonstrates one operation.

### 4.1 Roll-up (product → aisle → department)

```sql
SELECT p.department, p.aisle, COUNT(*) AS items_sold
FROM fact_order_items f
JOIN dim_product p ON f.product_key = p.product_key
GROUP BY ROLLUP (p.department, p.aisle)
ORDER BY p.department, p.aisle;
-- NULL aisle = department subtotal; both NULL = grand total
```

### 4.2 Drill-down (department → aisle → product)

```sql
-- Level 1
SELECT department, COUNT(*) items FROM fact_order_items f
JOIN dim_product p USING (product_key) GROUP BY department ORDER BY items DESC;

-- Level 2: drill into one department
SELECT aisle, COUNT(*) items FROM fact_order_items f
JOIN dim_product p USING (product_key)
WHERE department = 'produce' GROUP BY aisle ORDER BY items DESC;

-- Level 3: drill into one aisle
SELECT product_name, COUNT(*) items FROM fact_order_items f
JOIN dim_product p USING (product_key)
WHERE aisle = 'fresh fruits' GROUP BY product_name ORDER BY items DESC LIMIT 20;
```

Time drill-down: part_of_day → hour (and day → hour).

```sql
SELECT t.part_of_day, t.hour, COUNT(*) AS orders
FROM fact_orders o JOIN dim_time t USING (time_key)
GROUP BY ROLLUP (t.part_of_day, t.hour);
```

### 4.3 Slice (fix one dimension value)

```sql
SELECT p.department, COUNT(*) AS items, AVG(f.reordered) AS reorder_rate
FROM fact_order_items f
JOIN dim_product p USING (product_key)
JOIN dim_time t USING (time_key)
WHERE t.is_weekend = TRUE
GROUP BY p.department ORDER BY items DESC;
```

### 4.4 Dice (restrict several dimensions)

```sql
SELECT p.department, t.part_of_day, COUNT(*) AS items, AVG(f.reordered) AS reorder_rate
FROM fact_order_items f
JOIN dim_product p USING (product_key)
JOIN dim_time t USING (time_key)
WHERE p.department IN ('produce', 'dairy eggs')
  AND t.is_weekend = TRUE
  AND t.hour BETWEEN 8 AND 12
GROUP BY p.department, t.part_of_day;
```

### 4.5 Pivot (department × day)

```sql
PIVOT (
  SELECT p.department, t.order_dow, COUNT(*) AS items
  FROM fact_order_items f
  JOIN dim_product p USING (product_key)
  JOIN dim_time t USING (time_key)
  GROUP BY p.department, t.order_dow
)
ON order_dow USING SUM(items)
ORDER BY department;
```

*Portable alternative (works in PostgreSQL/MySQL too):*

```sql
SELECT p.department,
  SUM(CASE WHEN t.order_dow=0 THEN 1 ELSE 0 END) AS d0,
  SUM(CASE WHEN t.order_dow=1 THEN 1 ELSE 0 END) AS d1,
  SUM(CASE WHEN t.order_dow=2 THEN 1 ELSE 0 END) AS d2,
  SUM(CASE WHEN t.order_dow=3 THEN 1 ELSE 0 END) AS d3,
  SUM(CASE WHEN t.order_dow=4 THEN 1 ELSE 0 END) AS d4,
  SUM(CASE WHEN t.order_dow=5 THEN 1 ELSE 0 END) AS d5,
  SUM(CASE WHEN t.order_dow=6 THEN 1 ELSE 0 END) AS d6
FROM fact_order_items f
JOIN dim_product p USING (product_key)
JOIN dim_time t USING (time_key)
GROUP BY p.department;
```

### 4.6 CUBE and GROUPING SETS

```sql
SELECT p.department, t.part_of_day, COUNT(*) AS items
FROM fact_order_items f
JOIN dim_product p USING (product_key)
JOIN dim_time t USING (time_key)
GROUP BY CUBE (p.department, t.part_of_day);

SELECT p.department, t.is_weekend, COUNT(*) AS items
FROM fact_order_items f
JOIN dim_product p USING (product_key)
JOIN dim_time t USING (time_key)
GROUP BY GROUPING SETS ((p.department, t.is_weekend), (p.department), (t.is_weekend), ());
```

### 4.7 Pre-aggregated cube table (used for performance in Section 6)

```sql
CREATE OR REPLACE TABLE cube_dept_time AS
SELECT p.department, p.aisle, t.order_dow, t.hour,
       COUNT(*) AS items, SUM(f.reordered) AS reordered_items
FROM fact_order_items f
JOIN dim_product p USING (product_key)
JOIN dim_time t USING (time_key)
GROUP BY p.department, p.aisle, t.order_dow, t.hour;
```
Roll-ups then run on this small table (a few hundred thousand rows at most) instead of 32M rows. Reorder rate = `SUM(reordered_items)/SUM(items)`.

### 4.8 Deliverables
One table/chart per operation, plus a short "business insight" sentence from each. Write insights from **your actual output**, not assumptions.

---

## Section 5: Dashboard-ready analytics (KPIs)

Queries that feed the dashboard (Section 9):

```sql
-- KPIs
SELECT COUNT(*) AS orders, COUNT(DISTINCT customer_key) AS customers,
       AVG(basket_size) AS avg_basket, AVG(reorder_ratio) AS avg_reorder
FROM fact_orders;

-- Top 20 products
SELECT p.product_name, COUNT(*) AS items, AVG(f.reordered) AS reorder_rate
FROM fact_order_items f JOIN dim_product p USING (product_key)
GROUP BY 1 ORDER BY items DESC LIMIT 20;

-- Reorder rate heatmap (day × hour)
SELECT t.order_dow, t.hour, AVG(f.reordered) AS reorder_rate
FROM fact_order_items f JOIN dim_time t USING (time_key)
GROUP BY 1, 2;

-- Basket size trend by order_number (customer maturity)
SELECT order_number, AVG(basket_size) AS avg_basket
FROM fact_orders WHERE order_number <= 50 GROUP BY 1 ORDER BY 1;
```

Note: Instacart has no calendar, so "trend over time" is by `order_number` (a customer's n-th order) or day/hour pattern, not by month. Say this explicitly.

---

## Section 6: Performance engineering and benchmarking

This section creates the paper's measurable contribution.

### 6.1 Experimental configurations

| Config | Description |
|---|---|
| **C1: Normalized** | Query staging tables directly (`stg_orders`, `stg_op`, `stg_products`, `stg_aisles`, `stg_departments`), multi-join |
| **C2: Star/Galaxy** | Query `fact_*` + `dim_*` tables |
| **C3: Columnar files** | Query the Parquet files directly, optionally partitioned by `time_key`/`department` |
| **C4: Pre-aggregated** | Query `cube_dept_time` |
| **C5 (optional): PostgreSQL** | Same queries on PostgreSQL with indexes (and a materialized view) |

PostgreSQL index/MV examples (for C5):

```sql
CREATE INDEX idx_foi_product ON fact_order_items(product_key);
CREATE INDEX idx_foi_time    ON fact_order_items(time_key);
CREATE MATERIALIZED VIEW mv_dept_time AS
  SELECT p.department, t.order_dow, t.hour, COUNT(*) items
  FROM fact_order_items f JOIN dim_product p USING(product_key) JOIN dim_time t USING(time_key)
  GROUP BY 1,2,3;
REFRESH MATERIALIZED VIEW mv_dept_time;
```

### 6.2 Benchmark queries (define 5 to 6)
- Q1: items by department (roll-up)
- Q2: department × day pivot
- Q3: reorder rate for a dice (dept + part_of_day + weekend)
- Q4: top 20 products
- Q5: CUBE(department, part_of_day)
- Q6: customer-level aggregation (orders and items per user)

Write each query in versions for C1 to C4.

### 6.3 Benchmark harness

```python
# benchmark/run_benchmark.py
import duckdb, time, statistics, csv

con = duckdb.connect("data/warehouse/dwm.duckdb", read_only=True)

# dict: {query_name: {config_name: sql}}
QUERIES = {
  "Q1_dept_rollup": {
    "C1_normalized": """SELECT d.department, COUNT(*) FROM stg_op op
                        JOIN stg_products p ON op.product_id=p.product_id
                        JOIN stg_departments d ON p.department_id=d.department_id
                        GROUP BY d.department""",
    "C2_galaxy": """SELECT p.department, COUNT(*) FROM fact_order_items f
                    JOIN dim_product p USING(product_key) GROUP BY p.department""",
    "C4_preagg": """SELECT department, SUM(items) FROM cube_dept_time GROUP BY department""",
  },
  # add Q2..Q6 similarly
}

RUNS = 5
rows = []
for qname, cfgs in QUERIES.items():
    for cfg, sql in cfgs.items():
        times = []
        for _ in range(RUNS):
            t0 = time.perf_counter()
            con.execute(sql).fetchall()
            times.append(time.perf_counter() - t0)
        rows.append([qname, cfg, round(times[0], 3),
                     round(statistics.mean(times[1:]), 3),
                     round(statistics.stdev(times[1:]), 3)])
        print(rows[-1])

with open("benchmark/results.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["query", "config", "first_run_s", "mean_warm_s", "std_warm_s"])
    w.writerows(rows)
```

**Good practice:** report first (cold) vs warm runs separately; close other heavy apps; note hardware, RAM, and library versions; same machine for all configs.

### 6.4 Scalability test
Create 10%, 50%, 100% subsets (e.g., filter by `order_id % 10 < 1`, `< 5`, `< 10`), rebuild or filter facts, and re-run the benchmark. Plot time vs data size per config.

### 6.5 Results template (fill with YOUR measurements)

| Query | C1 Normalized (s) | C2 Galaxy (s) | C3 Parquet (s) | C4 Pre-agg (s) |
|---|---|---|---|---|
| Q1 | | | | |
| Q2 | | | | |
| Q3 | | | | |
| Q4 | | | | |
| Q5 | | | | |
| Q6 | | | | |

---

## Section 7: Customer segmentation (RFM, adapted)

Instacart has no calendar dates and no prices, so classic RFM must be adapted. State this in the paper.

| Component | Adapted definition |
|---|---|
| Recency-like (R) | Average days between orders (lower = more engaged) |
| Frequency (F) | Total number of orders |
| Monetary-like (M) | Total items bought (a proxy, not revenue) |

*(If you include Olist, use true recency and payment value there.)*

```python
# mining/rfm.py
import duckdb, pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

con = duckdb.connect("data/warehouse/dwm.duckdb")
df = con.execute("""
  SELECT customer_key, avg_days_between_orders AS R, total_orders AS F, total_items AS M
  FROM dim_customer WHERE avg_days_between_orders IS NOT NULL
""").df()

X = StandardScaler().fit_transform(df[["R", "F", "M"]])

# choose k with elbow + silhouette (use a sample for silhouette to save time)
sample = pd.DataFrame(X).sample(20000, random_state=42)
for k in range(2, 8):
    km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(X)
    s = silhouette_score(sample, km.predict(sample))
    print(k, round(km.inertia_, 1), round(s, 3))

K = 4   # set after inspecting the elbow/silhouette output
df["cluster"] = KMeans(n_clusters=K, n_init=10, random_state=42).fit_predict(X)

profile = df.groupby("cluster")[["R", "F", "M"]].mean().round(2)
profile["size"] = df.groupby("cluster").size()
print(profile)
```

**Labeling:** after seeing the cluster profile, assign names yourself (e.g., "frequent heavy buyers", "occasional light buyers") based on the actual R/F/M means. Then write back:

```python
labels = {0: "Segment A", 1: "Segment B", 2: "Segment C", 3: "Segment D"}  # replace with your own names
df["rfm_segment"] = df["cluster"].map(labels)
con.register("seg", df[["customer_key", "rfm_segment"]])
con.execute("""
  UPDATE dim_customer SET rfm_segment = seg.rfm_segment
  FROM seg WHERE dim_customer.customer_key = seg.customer_key
""")
```

**Alternative:** quintile scoring (1-5 per R/F/M via `pd.qcut`) and combine into a score; simpler to explain in a viva.

---

## Section 8: Association rule mining

### 8.1 Prepare the basket matrix

```python
# mining/basket_mining.py
import duckdb, pandas as pd, time
from mlxtend.frequent_patterns import apriori, fpgrowth, association_rules

con = duckdb.connect("data/warehouse/dwm.duckdb", read_only=True)

TOP_N = 200          # frequent products to keep
N_ORDERS = 100_000   # sample size (raise if RAM allows)

df = con.execute(f"""
  WITH top AS (
    SELECT product_key FROM fact_order_items
    GROUP BY product_key ORDER BY COUNT(*) DESC LIMIT {TOP_N}
  ),
  sample AS (
    SELECT order_id FROM fact_orders USING SAMPLE {N_ORDERS} ROWS
  )
  SELECT f.order_id, p.product_name
  FROM fact_order_items f
  JOIN top USING (product_key)
  JOIN sample USING (order_id)
  JOIN dim_product p USING (product_key)
""").df()

basket = pd.crosstab(df["order_id"], df["product_name"]).astype(bool)
print(basket.shape)
```

Why restrict: with 50K products and millions of orders the full matrix will not fit in memory, and rare items add little signal. State TOP_N and sample size in the paper.

### 8.2 Run Apriori and FP-Growth, compare

```python
results = []
for min_sup in [0.05, 0.03, 0.02, 0.01]:
    for name, algo in [("apriori", apriori), ("fpgrowth", fpgrowth)]:
        t0 = time.perf_counter()
        fi = algo(basket, min_support=min_sup, use_colnames=True)
        dt = time.perf_counter() - t0
        results.append((name, min_sup, len(fi), round(dt, 2)))
        print(results[-1])
# note: Apriori may be very slow at low support; stop at a threshold your machine handles
```

### 8.3 Generate rules

```python
fi = fpgrowth(basket, min_support=0.01, use_colnames=True)
rules = association_rules(fi, metric="lift", min_threshold=1.2)
rules = rules[rules["confidence"] >= 0.3].sort_values("lift", ascending=False)
print(rules[["antecedents", "consequents", "support", "confidence", "lift"]].head(20))
```

**Metrics to explain:**
- Support = P(A ∪ B)
- Confidence = P(B | A)
- Lift = confidence / P(B). Lift > 1 means positive association.

**Caveat to state:** many top rules will be among common items (e.g., fruits/vegetables) simply because they are popular. Use lift and per-slice comparison to show where the association is meaningful.

### 8.4 Slice-aware mining (your novelty)

```python
# mining/slice_mining.py
SLICES = {
  "weekend_morning":  "t.is_weekend AND t.part_of_day = 'Morning'",
  "weekday_evening":  "NOT t.is_weekend AND t.part_of_day = 'Evening'",
  "dept_produce_orders": None,   # example of a department-based slice (see note)
}

def mine_slice(con, where_sql, top_n=200, n_orders=100_000, min_sup=0.01):
    df = con.execute(f"""
      WITH top AS (
        SELECT product_key FROM fact_order_items
        GROUP BY product_key ORDER BY COUNT(*) DESC LIMIT {top_n}
      ),
      sl AS (
        SELECT o.order_id FROM fact_orders o JOIN dim_time t USING (time_key)
        WHERE {where_sql}
      ),
      sample AS (SELECT order_id FROM sl USING SAMPLE {n_orders} ROWS)
      SELECT f.order_id, p.product_name
      FROM fact_order_items f
      JOIN top USING (product_key)
      JOIN sample USING (order_id)
      JOIN dim_product p USING (product_key)
    """).df()
    basket = pd.crosstab(df["order_id"], df["product_name"]).astype(bool)
    fi = fpgrowth(basket, min_support=min_sup, use_colnames=True)
    rules = association_rules(fi, metric="lift", min_threshold=1.2)
    return rules
```

**What to compare (the contribution):**
- Rules found in a slice but **not** in the global rule set (or with much higher lift in the slice)
- Overlap between slices (Jaccard index of rule sets)
- Number of rules per slice vs global

Keep the same TOP_N, sample size and thresholds across slices so the comparison is fair. For department-based slices, filter orders that contain an item from that department.

### 8.5 Store rules back into the warehouse

```python
def to_str(fs): return ", ".join(sorted(fs))

out = rules.copy()
out["antecedent"] = out["antecedents"].apply(to_str)
out["consequent"] = out["consequents"].apply(to_str)
out["slice_name"] = "weekend_morning"      # set per slice
out = out[["slice_name", "antecedent", "consequent", "support", "confidence", "lift"]]

wcon = duckdb.connect("data/warehouse/dwm.duckdb")   # writable connection
wcon.execute("CREATE TABLE IF NOT EXISTS fact_rules (slice_name VARCHAR, antecedent VARCHAR, consequent VARCHAR, support DOUBLE, confidence DOUBLE, lift DOUBLE)")
wcon.register("out_df", out)
wcon.execute("INSERT INTO fact_rules SELECT * FROM out_df")
```

---

## Section 9: Dashboard implementation (Streamlit)

```python
# dashboard/app.py
import duckdb, pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Retail DWM Dashboard", layout="wide")
DB = "data/warehouse/dwm.duckdb"

@st.cache_resource
def get_con():
    return duckdb.connect(DB, read_only=True)

@st.cache_data
def q(sql: str) -> pd.DataFrame:
    return get_con().execute(sql).df()

page = st.sidebar.radio("Page", ["Overview", "OLAP Explorer", "Customers (RFM)", "Association Rules"])

if page == "Overview":
    k = q("""SELECT COUNT(*) orders, COUNT(DISTINCT customer_key) customers,
                    AVG(basket_size) basket, AVG(reorder_ratio) reorder FROM fact_orders""").iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Orders", f"{int(k.orders):,}")
    c2.metric("Customers", f"{int(k.customers):,}")
    c3.metric("Avg basket size", f"{k.basket:.1f}")
    c4.metric("Avg reorder ratio", f"{k.reorder:.2%}")

    top = q("""SELECT p.product_name, COUNT(*) items FROM fact_order_items f
               JOIN dim_product p USING(product_key) GROUP BY 1 ORDER BY items DESC LIMIT 20""")
    st.plotly_chart(px.bar(top, x="items", y="product_name", orientation="h",
                           title="Top 20 products").update_yaxes(autorange="reversed"),
                    use_container_width=True)

    heat = q("""SELECT t.order_dow, t.hour, AVG(f.reordered) reorder_rate
                FROM fact_order_items f JOIN dim_time t USING(time_key) GROUP BY 1,2""")
    st.plotly_chart(px.density_heatmap(heat, x="hour", y="order_dow", z="reorder_rate",
                    histfunc="avg", title="Reorder rate by day and hour"),
                    use_container_width=True)

elif page == "OLAP Explorer":
    depts = q("SELECT DISTINCT department FROM dim_product ORDER BY 1")["department"].tolist()
    parts = ["Night", "Morning", "Afternoon", "Evening"]
    sel_d = st.sidebar.multiselect("Department (dice)", depts, default=depts[:3])
    sel_p = st.sidebar.multiselect("Part of day", parts, default=parts)
    wk = st.sidebar.selectbox("Weekend filter (slice)", ["All", "Weekend only", "Weekday only"])
    level = st.sidebar.radio("Level (roll-up / drill-down)", ["department", "aisle", "product_name"])

    if not sel_d or not sel_p:
        st.warning("Select at least one department and one part of day.")
        st.stop()
    d_list = ",".join("'" + d.replace("'", "''") + "'" for d in sel_d)
    p_list = ",".join("'" + p + "'" for p in sel_p)
    wk_sql = {"All": "TRUE", "Weekend only": "t.is_weekend", "Weekday only": "NOT t.is_weekend"}[wk]

    df = q(f"""
      SELECT p.{level} AS grp, COUNT(*) items, AVG(f.reordered) reorder_rate
      FROM fact_order_items f
      JOIN dim_product p USING(product_key) JOIN dim_time t USING(time_key)
      WHERE p.department IN ({d_list}) AND t.part_of_day IN ({p_list}) AND {wk_sql}
      GROUP BY 1 ORDER BY items DESC LIMIT 30""")
    st.plotly_chart(px.bar(df, x="grp", y="items", color="reorder_rate",
                           title=f"Items by {level}"), use_container_width=True)
    st.dataframe(df)

elif page == "Customers (RFM)":
    seg = q("""SELECT rfm_segment, COUNT(*) customers, AVG(total_orders) avg_orders,
                      AVG(total_items) avg_items, AVG(avg_days_between_orders) avg_gap
               FROM dim_customer WHERE rfm_segment IS NOT NULL GROUP BY 1""")
    st.plotly_chart(px.pie(seg, names="rfm_segment", values="customers",
                           title="Customer segments"), use_container_width=True)
    st.dataframe(seg)

else:
    rules = q("SELECT * FROM fact_rules")
    sl = st.sidebar.selectbox("Slice", sorted(rules["slice_name"].unique()))
    min_lift = st.sidebar.slider("Min lift", 1.0, 10.0, 1.5)
    r = rules[(rules.slice_name == sl) & (rules.lift >= min_lift)].sort_values("lift", ascending=False)
    st.dataframe(r.head(50))
    st.plotly_chart(px.scatter(r, x="support", y="confidence", color="lift",
                               hover_data=["antecedent", "consequent"],
                               title="Rules: support vs confidence"), use_container_width=True)
```

Run:

```bash
streamlit run dashboard/app.py
```

**Notes**
- Close any writable DuckDB connection before opening the dashboard (DuckDB allows one writer; many read-only readers only when no writer is active).
- For a nicer rule view, add a `networkx` graph of antecedent → consequent.
- Dashboard alternatives: export the aggregated tables to CSV/Parquet and build the same pages in Power BI or Tableau Public; or use Superset connected to PostgreSQL.
- Deploy (optional): Streamlit Community Cloud with a small pre-aggregated Parquet (the full DB is too big to host).

---

## Section 10: Optional extension: Olist as a second fact (true galaxy schema)

Adds real dates, geography, price, and payment, giving real roll-up/drill-down on time and location.

**Olist tables used:** `olist_orders_dataset`, `olist_order_items_dataset`, `olist_customers_dataset`, `olist_products_dataset`, `product_category_name_translation`, `olist_order_payments_dataset`.

**New tables**
- `dim_date` (date_key, date, day, month, quarter, year, weekday, is_weekend, month_name)
- `dim_geography` (geo_key, city, state)
- `dim_olist_product` (product_id, category (English), ...)
- `fact_olist_sales`: one row per order item: `order_id`, `order_item_id`, `date_key`, `customer_geo_key`, `product_id`, `price`, `freight_value`

```sql
CREATE TABLE dim_date AS
SELECT CAST(strftime(d, '%Y%m%d') AS INTEGER) AS date_key, d AS date,
       year(d) AS year, quarter(d) AS quarter, month(d) AS month,
       monthname(d) AS month_name, day(d) AS day,
       dayofweek(d) AS dow, dayofweek(d) IN (0, 6) AS is_weekend
FROM (SELECT CAST(x AS DATE) AS d
      FROM generate_series(DATE '2016-09-01', DATE '2018-10-31', INTERVAL 1 DAY) t(x));
```

Then the real calendar OLAP:

```sql
SELECT year, quarter, month, SUM(price) AS revenue
FROM fact_olist_sales f JOIN dim_date USING (date_key)
GROUP BY ROLLUP (year, quarter, month);
```

Check the actual date range of your Olist copy before generating `dim_date` (adjust the bounds). Cross-state OLAP: revenue by `state → city`. Also true RFM: recency from `order_purchase_timestamp`, monetary from `price`.

Because Olist and Instacart are different businesses, do **not** join them on product or customer; keep them as two fact tables sharing only the *concept* of a time dimension. Say this explicitly in the paper.

---

## Section 11: Testing and quality checks

| Check | How |
|---|---|
| Row counts | staging vs fact tables (Section 3.3) |
| Referential integrity | zero orphan keys |
| Aggregation consistency | `SUM(items)` by department equals total rows; roll-up subtotal = sum of children |
| Pre-aggregate equality | results from `cube_dept_time` equal results from the fact table |
| Reproducibility | fixed seeds (`random_state=42`, `USING SAMPLE ... (reservoir, 42)` if you need deterministic samples), pinned versions |
| Dashboard | spot-check 3 numbers against SQL results |

---

# PART C: EXPERIMENTS, REPORT, PAPER, RISKS

## C1. Experiment checklist for the paper

1. **E1: Query performance** across C1 to C4 (Section 6)
2. **E2: Scalability** at 10/50/100% data
3. **E3: Algorithm comparison**, Apriori vs FP-Growth: runtime and number of itemsets vs min_support
4. **E4: Global vs slice-aware rules**: counts, lift differences, overlap
5. **E5: Segmentation**: silhouette, cluster profiles
6. **E6 (optional):** DuckDB vs PostgreSQL

Record for each: hardware, software versions, parameters, number of runs.

## C2. Final report structure and what to put in each chapter

| Chapter | Content | Comes from |
|---|---|---|
| 1. Introduction | Problem, objectives, scope | Plan |
| 2. Literature review | Warehousing, OLAP, Apriori/FP-Growth, RFM | Part A4 refs |
| 3. Dataset | Source, tables, limitations | Section 1 |
| 4. Requirements and design | Business questions, galaxy schema, data dictionary | Section 2 |
| 5. ETL | Pipeline, transformations, validation | Section 3 |
| 6. OLAP | Each operation, SQL, output, insight | Section 4 |
| 7. Performance evaluation | Benchmark design and results | Section 6 |
| 8. Mining | RFM, Apriori vs FP-Growth, slice-aware rules | Sections 7 and 8 |
| 9. Dashboard | Screenshots, how it answers the business questions | Section 9 |
| 10. Results and discussion | Key findings, limitations | All |
| 11. Conclusion and future scope | Summary, extensions | All |
| Appendix | Code, extra queries, environment | repo |

## C3. Research paper skeleton (IEEE-style, 6 to 8 pages)

1. **Abstract** (150 to 200 words): problem, approach (galaxy schema + slice-aware mining), dataset scale, main findings (use your real numbers), contribution
2. **Introduction:** motivation, gap (OLAP and mining usually separate), research questions, contributions
3. **Related work:** warehousing/OLAP, association mining in retail, OLAP-mining integration (OLAM)
4. **Dataset and preprocessing**
5. **Architecture and warehouse design**
6. **Methodology:** OLAP operations, benchmark design, mining pipeline, slice-aware method
7. **Experimental setup**
8. **Results and discussion** (E1 to E5)
9. **Limitations:** no calendar dates or prices in Instacart, proxy RFM, undocumented day encoding, sampled mining, single machine
10. **Conclusion and future work**
11. **References**

**Research questions (restated):**
- RQ1: How do schema design and pre-aggregation affect OLAP query time at 30M+ rows?
- RQ2: How do Apriori and FP-Growth compare in runtime as support decreases?
- RQ3: Does mining within OLAP slices reveal rules that global mining misses?

**Writing honesty tips**
- Report only measured numbers; keep raw logs/CSVs to back them
- Label anything that is an assumption or proxy
- If a result is not significant or a comparison is inconclusive, say so

## C4. Viva / demo preparation

**5-minute demo flow:** architecture slide → schema diagram → one roll-up and one pivot live → one slice-specific rule vs global → dashboard walk-through → benchmark chart.

**Likely questions**
- Star vs snowflake vs galaxy schema? Why galaxy here?
- What is the grain of each fact table?
- Fact vs dimension; conformed dimension; surrogate key
- Roll-up vs drill-down; slice vs dice; what is a pivot
- ROLLUP vs CUBE vs GROUPING SETS
- OLAP vs OLTP; ETL vs ELT
- Apriori vs FP-Growth; support, confidence, lift
- Why only top-N products? What are the limitations?
- Why DuckDB? Why Parquet?
- How did you validate the ETL?

## C5. Risks and fixes

| Risk | Fix |
|---|---|
| Out of memory in mining | Lower TOP_N, sample fewer orders, raise min_support, use FP-Growth, or use Colab |
| Apriori too slow | Raise min_support; report that as a finding |
| Kaggle download blocked | Manual download; or use the Instacart original page |
| No real dates | Use Option A (add Olist) or REES46 |
| Dashboard slow | Query pre-aggregated tables, cache with `st.cache_data` |
| DuckDB lock error | Only one writer; use `read_only=True` in the dashboard |
| Rules look trivial | Use lift thresholds, compare slices, drop ultra-popular items |

## C6. Suggested timeline (7 weeks)

| Week | Work |
|---|---|
| 1 | Setup, download, profiling (Sections 0 to 1) |
| 2 | Schema design + ETL (Sections 2 to 3) |
| 3 | OLAP queries + pre-aggregation (Section 4 to 5) |
| 4 | Benchmarking (Section 6) |
| 5 | RFM + rule mining + slice mining (Sections 7 to 8) |
| 6 | Dashboard (Section 9), optional Olist extension (Section 10) |
| 7 | Report, paper, demo, viva prep (Part C) |

## C7. Final deliverables checklist

- [ ] GitHub repo with README and run instructions
- [ ] Warehouse (DuckDB/Parquet) and schema diagram
- [ ] ETL scripts + validation output
- [ ] OLAP SQL file with outputs for all 5 operations (+ CUBE/ROLLUP)
- [ ] Benchmark CSV + charts
- [ ] Mining notebooks + `fact_rules`
- [ ] Working dashboard + screenshots
- [ ] Project report
- [ ] Research paper (PDF + source)
- [ ] Presentation slides
