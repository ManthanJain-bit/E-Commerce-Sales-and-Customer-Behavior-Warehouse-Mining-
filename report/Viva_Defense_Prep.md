# Comprehensive Viva Defense & Demo Preparation Guide

**Project Title:** E-Commerce Sales and Customer Behavior Warehouse  
**Paper Title:** *Integrating OLAP and Association Rule Mining on a Retail Data Warehouse for Customer Behavior Analysis*  
**Subject:** Data Warehousing and Mining (DWM)  
**Live Dashboard URL:** `http://localhost:8501`

---

## 🎯 Part 1: 5-Minute Live Presentation & Demo Script

When presenting to your professors, examiners, or project review panel, follow this concise, structured 5-minute flow:

### Minute 1: Problem, Objective & Dataset Scale
> *"Good morning, respected examiners. Our DWM project bridges the gap between classical Data Warehousing and Advanced Data Mining on a massive real-world retail dataset comprising **33.8 million item purchases**, **3.35 million orders**, and **206,209 customers**.*  
> *Historically, companies run OLAP for aggregate reports and Data Mining on flat files in separate silos. Our project integrates both into an end-to-end On-Line Analytical Mining (OLAM) framework."*

### Minute 2: Schema Architecture & Grain Defense
> *"We designed a **Galaxy Schema (Fact Constellation)** with two conformed fact tables:  
> 1. `fact_order_items` at the item level (33.8M rows) tracking cart order and reorders.  
> 2. `fact_orders` at the order level (3.35M rows) tracking basket size and intervals.  
> They share conformed dimensions: `dim_product` with a 3-tier hierarchy (Department $\rightarrow$ Aisle $\rightarrow$ Product), `dim_time` (168 hourly combinations), and `dim_customer`. All 9 automated referential integrity checks passed with **0 orphan keys**."*

### Minute 3: OLAP Multidimensional Operations & RQ1 Benchmark
> *"We executed all core OLAP operations in SQL: Roll-up, Drill-down, Slice, Dice, Pivot, and CUBE across 33.8M rows.  
> In addressing **Research Question 1 (RQ1)**, we benchmarked 4 architectures:  
> - Galaxy Schema consistently outperformed normalized relational joins by **~2x across all data scales**.  
> - For recurrent aggregations, our pre-aggregated summary table (`cube_dept_time`) delivered **sub-second speedups of up to 87x** (0.0021s vs 0.1826s)."*

### Minute 4: Machine Learning & Contextual Rule Mining (RQ2 & RQ3)
> *"For Data Mining, we achieved two major findings:  
> 1. **RQ2 (Apriori vs FP-Growth):** As support drops to 1%, Apriori's runtime exploded by **141.7x** due to combinatorial candidate generation, while FP-Growth scaled smoothly and ran **5.23x faster**.  
> 2. **RQ3 (Novelty - Slice-Aware Mining):** By mining within specific OLAP slices, we discovered that Weekend Morning baskets have only a **50% overlap** with Weekday Evening baskets. We uncovered **8 high-lift rules exclusive to weekend mornings** (e.g., Organic Cilantro $\Longrightarrow$ Limes, Lift = 4.83) that global market basket mining averages out and misses. We wrote these rules back into the warehouse inside the `fact_rules` table."*

### Minute 5: Live Dashboard Walkthrough
> *(Open `http://localhost:8501` on screen)*  
> *"Finally, we deployed a live Streamlit + Plotly analytical dashboard:  
> - Page 1 displays real-time KPIs and the Day-Hour reorder heatmap.  
> - Page 2 allows dynamic multidimensional slicing, dicing, and drill-downs.  
> - Page 3 visualizes our 4 K-Means customer personas.  
> - Page 4 allows filtering our mined association rules by context slice with interactive lift sliders.  
> Thank you, we welcome your questions!"*

---

## ❓ Part 2: Top 15 Technical Viva Questions & Model Answers

### Q1: What is the difference between Star, Snowflake, and Galaxy schemas? Why did you choose Galaxy?
* **Star Schema:** Single fact table surrounded by completely denormalized dimension tables.
* **Snowflake Schema:** Single fact table where dimensions are normalized into sub-tables (e.g., separating Department from Aisle).
* **Galaxy Schema (Fact Constellation):** Multiple fact tables sharing conformed dimensions.
* **Why Galaxy here:** Retail orders operate at two distinct grains: order-level attributes (basket size, reorder ratio, gap days) and item-level attributes (cart order, reordered flag, SKU). Forcing them into a single fact table causes severe data redundancy. A Galaxy schema cleanly models both business processes while sharing `dim_product`, `dim_time`, and `dim_customer`.

### Q2: What is the grain of your fact tables?
* `fact_order_items`: One row per product inside an order (fine grain, 33.8M rows).
* `fact_orders`: One row per completed transaction (coarse grain, 3.35M rows).
* `fact_rules`: One row per mined association rule per dimensional slice (48 rows).

### Q3: What is a conformed dimension?
* A conformed dimension is a dimension table that has the exact same meaning, primary key, and attributes across multiple fact tables. In our project, `dim_time` and `dim_customer` are conformed dimensions because both `fact_order_items` and `fact_orders` join to them consistently.

### Q4: Explain the difference between Roll-up and Drill-down with examples from your project.
* **Roll-up:** Summarizes data by climbing up a dimensional hierarchy (increasing aggregation, decreasing detail).  
  * *Example:* Moving from Product SKU $\rightarrow$ Aisle (`fresh fruits`) $\rightarrow$ Department (`produce`) $\rightarrow$ Grand Total using SQL `ROLLUP`.
* **Drill-down:** Deconstructs summary data by stepping down a hierarchy (increasing detail).  
  * *Example:* Clicking on Department `produce` to view top Aisles, then drilling into `fresh fruits` to reveal top SKUs (`Banana`, 491,291 units).

### Q5: What is the difference between Slicing and Dicing?
* **Slice:** Fixing **one dimension** to a single value to obtain a 2D sub-plane.  
  * *Example:* Filtering orders where `is_weekend = TRUE`.
* **Dice:** Restricting **two or more dimensions** simultaneously to define a sub-cube.  
  * *Example:* Department $\in$ (`produce`, `dairy eggs`) AND `is_weekend = TRUE` AND `hour BETWEEN 8 AND 12`.

### Q6: What is the difference between `ROLLUP`, `CUBE`, and `GROUPING SETS` in SQL?
* **`ROLLUP(A, B)`:** Generates hierarchical aggregations along a specific order: $(A, B)$, $(A)$, and $()$ [grand total]. ($N+1$ groupings).
* **`CUBE(A, B)`:** Generates all possible $2^N$ cross-combinations of dimensions: $(A, B)$, $(A)$, $(B)$, and $()$.
* **`GROUPING SETS`:** Allows you to selectively specify exact grouping combinations to compute in a single pass without computing unnecessary power sets.

### Q7: What is an OLAP Cube and how did your pre-aggregated cube accelerate queries?
* An OLAP cube is a multidimensional data structure that pre-computes and materializes summary aggregations along dimensional axes.
* In our project, `cube_dept_time` pre-computed item counts across Department, Aisle, DOW, and Hour (22,480 rows). Querying this summary table instead of scanning the full 33.8 million item rows reduced query latency from **0.192s to 0.0162s** (an **11.8x to 87x speedup**).

### Q8: What is the difference between OLTP and OLAP?
| Feature | OLTP (Online Transaction Processing) | OLAP (Online Analytical Processing) |
|---|---|---|
| **Purpose** | Day-to-day operations & order intake | Historical decision support & analytics |
| **Data Format** | Row-oriented, 3NF normalized | Columnar, Star/Galaxy dimensional schemas |
| **Workload** | Fast, frequent ACID writes/updates | Complex read-heavy aggregations (`SUM`, `AVG`) |
| **Example** | MySQL, PostgreSQL | DuckDB, Snowflake, BigQuery |

### Q9: Why did you use DuckDB and Parquet instead of MySQL or MongoDB?
1. **Columnar Vectorized Execution:** DuckDB reads only the requested columns in binary chunks, allowing it to scan and aggregate 33.8M rows in tenths of a second.
2. **Parquet Compression:** Columnar compression (ZSTD) shrank the dataset from ~680 MB to 146 MB on disk.
3. **Embedded / Serverless:** Operates locally inside Python with zero server overhead, perfect for reproducible benchmarking without cloud network latency.

### Q10: How did you validate that your ETL didn't lose or corrupt data?
We implemented [`etl/04_validate.py`](file:///c:/Users/Rupali%20Waghmare/Downloads/DWM%20Project/etl/04_validate.py) with 9 automated SQL assertion tests:
* Row count of `fact_order_items` exactly matched staging records in valid orders.
* Zero orphan keys (100% referential integrity with `dim_product`, `dim_time`, and `dim_customer`).
* Consistency checks between `fact_orders.basket_size` and items count in `fact_order_items`.
* **All 9 checks passed with 0 defects.**

### Q11: How does Apriori work, and why did its runtime explode at low support?
* Apriori uses the downward-closure property: if an itemset is frequent, all its subsets must be frequent.
* **Why it exploded (RQ2):** To find frequent $k$-itemsets, Apriori generates candidate combinations $C_k$ from $L_{k-1}$ and repeatedly scans the dataset to count support. As minimum support decreased from 5% to 1%, the number of candidate itemsets exploded exponentially, increasing runtime from **0.041s to 5.810s (a 141.7x slowdown)**.

### Q12: How does FP-Growth avoid candidate generation?
* FP-Growth constructs a compact in-memory Frequent Pattern Tree (FP-Tree) by reading the dataset in two passes.
* It compresses identical transaction prefixes and recursively projects conditional pattern bases to extract frequent patterns directly without ever generating candidate combinations. Hence, it ran **5.23x faster than Apriori at 1% support**.

### Q13: Define Support, Confidence, and Lift.
* **Support:** Proportion of transactions containing both $A$ and $B$: $P(A \cup B)$.
* **Confidence:** Probability that $B$ is purchased given that $A$ is purchased: $P(B \mid A) = \frac{\text{Support}(A \cup B)}{\text{Support}(A)}$.
* **Lift:** Ratio of observed joint probability to expected probability if $A$ and $B$ were independent: $\text{Lift} = \frac{P(B \mid A)}{P(B)}$. A Lift $> 1$ indicates a true positive association.

### Q14: What is the novelty of your Contextual Slice-Aware Mining (RQ3)?
* Standard market basket mining runs globally across all transactions, which averages out context.
* We integrated OLAP slicing with FP-Growth: by mining within specific temporal slices (Weekend Mornings vs. Weekday Evenings), we discovered that rule overlap was only **50%**.
* We uncovered **8 high-lift rules exclusive to weekend mornings** (e.g., `Organic Cilantro` $\Longrightarrow$ `Limes`, Lift: 4.83) that global mining completely missed.

### Q15: How did you adapt RFM analysis for this dataset?
* Since the Instacart dataset lacks calendar timestamps and product pricing, we adapted the three RFM components:
  * **Recency:** Average gap days between consecutive orders (lower gap = higher engagement).
  * **Frequency:** Total lifetime orders placed.
  * **Monetary:** Total items purchased across lifetime orders.
* We applied StandardScaler and K-Means ($k=4$, Silhouette = 0.4131) to categorize customers into: **Loyal Power Shoppers** (4.55%), **High-Volume Regulars** (15.78%), **Casual Occasionals** (42.75%), and **Infrequent/At-Risk** (36.92%).
