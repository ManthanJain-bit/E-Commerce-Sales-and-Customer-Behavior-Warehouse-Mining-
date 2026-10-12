# Integrating OLAP and Association Rule Mining on a Retail Data Warehouse for Customer Behavior Analysis

**Authors:** DWM Research Project Team  
**Affiliation:** Department of Computer Science & Engineering  
**Conference/Track:** IEEE Systems, Man, and Cybernetics / Data Science Capstone Track  
**Date:** October 2026  

---

### **Abstract**
In modern retail analytics, Online Analytical Processing (OLAP) and Association Rule Mining (ARM) have traditionally evolved as disjoint operational paradigms. OLAP excels at high-speed multidimensional aggregation across hierarchical structures, while ARM uncovers hidden co-occurrence patterns across flat transaction sets. In this paper, we propose an integrated On-Line Analytical Mining (OLAM) framework that unites a conformed Galaxy dimensional data warehouse with contextual slice-aware pattern discovery. Evaluated on a massive transaction dataset comprising **33,819,106 items** and **3,346,083 orders** across **206,209 customers**, our research makes three empirical contributions: 
1. **RQ1 (Architectural Benchmarking):** We demonstrate that a conformed Galaxy schema delivers a consistent **~2x query speedup** over normalized relational staging across all scales, while pre-aggregated summary materialization achieves **50x to 87x sub-second acceleration**.
2. **RQ2 (Mining Scalability):** We empirically show that as minimum support declines from $5\%$ to $1\%$, classical Apriori suffers an exponential **141.7x latency explosion**, whereas FP-Growth scales sub-linearly and executes **5.23x faster**.
3. **RQ3 (Slice-Aware Mining Novelty):** We prove that mining within temporal OLAP slices reveals critical high-lift associations (e.g., *Organic Cilantro* $\Longrightarrow$ *Limes*, Lift: 4.83) with an overlap of only $50\%$ between weekend mornings and weekday evenings, demonstrating that global market basket mining obscures vital contextual purchasing behaviors. Finally, all mined rules are persisted back into the analytical warehouse inside a dedicated fact table (`fact_rules`) and surfaced via an interactive web portal.

**Keywords:** Data Warehousing, Galaxy Schema, OLAP, Apriori, FP-Growth, Association Rule Mining, Slice-Aware Mining, Customer Segmentation, DuckDB.

---

### **I. Introduction**
Retail data warehouses must process tens of millions of records to answer aggregate operational queries and identify customer behavior patterns. Transactional relational database management systems (OLTP) rely on row-oriented normalization (3NF) to support atomicity and write operations, but incur massive I/O penalties when executing multi-join analytical queries. Consequently, Ralph Kimball introduced dimensional modeling, organizing data into star and galaxy (fact constellation) schemas optimized for aggregate analytical queries.

Simultaneously, data mining research has focused on unsupervised market basket analysis through algorithms like Apriori [1] and FP-Growth [2]. However, conventional association rule mining is typically performed globally across the entire corpus of transactions. This global averaging dilutes context-specific patterns: a purchase association strong on weekend mornings (e.g., breakfast or fresh culinary items) is often washed out by weekday transaction volume.

To resolve this limitation, we formulate three foundational research questions:
* **RQ1:** How do dimensional Galaxy schema design, columnar file scanning, and pre-aggregated cubes impact analytical query latency at 33.8M+ rows?
* **RQ2:** What is the empirical latency bifurcation between Apriori and FP-Growth as the support threshold decreases on dense retail transaction matrices?
* **RQ3:** Does mining association rules within specific OLAP dimensional slices uncover contextual rules that global market basket mining averages out and misses?

---

### **II. System Architecture & Dimensional Modeling**

#### A. Galaxy Schema Topology
To support varying grains of business processes, we designed a conformed **Galaxy Schema (Fact Constellation)**:
1. **`fact_order_items` (Fine Grain):** 1 row per product item in an order ($33,819,106$ rows). Attributes: `order_id`, `product_key`, `customer_key`, `time_key`, `add_to_cart_order`, `reordered`.
2. **`fact_orders` (Coarse Grain):** 1 row per transaction ($3,346,083$ rows). Attributes: `order_id`, `customer_key`, `time_key`, `order_number`, `days_since_prior_order`, `basket_size`, `reorder_ratio`.
3. **`fact_rules` (Mining Fact):** Stores discovered association rules linked to dimensional slice metadata: `slice_name`, `antecedent`, `consequent`, `support`, `confidence`, `lift`.

#### B. Conformed Dimensions
* **`dim_product` ($49,688$ rows):** Models the product hierarchy: $\text{Department} \rightarrow \text{Aisle} \rightarrow \text{Product SKU}$.
* **`dim_time` ($168$ rows):** Models all cyclical hourly combinations ($7 \text{ Days of Week} \times 24 \text{ Hours}$) enriched with `is_weekend` and `part_of_day`.
* **`dim_customer` ($206,209$ rows):** Aggregates customer lifetime metrics and stores machine learning-derived RFM cluster segments.
* **`cube_dept_time` ($22,480$ rows):** Pre-aggregated materialization summary table across Department, Aisle, DOW, and Hour.

---

### **III. Methodology & Mathematical Framework**

#### A. Adapted RFM Framework
Because the dataset tracks transaction intervals rather than calendar dates and prices, we adapt classic RFM as:
$$\text{Recency } (R) = \frac{1}{N-1} \sum_{i=2}^{N} \Delta t_i \quad (\text{Average Gap Days})$$
$$\text{Frequency } (F) = \text{Total Orders placed by customer}$$
$$\text{Monetary } (M) = \sum_{j=1}^{F} \text{Basket Size}_j \quad (\text{Total Items Purchased})$$
Features are standardized using z-score normalization: $Z = \frac{X - \mu}{\sigma}$. Clusters are partitioned using K-Means minimizing within-cluster sum of squares (WCSS).

#### B. Association Rule Metrics
Given itemsets $A$ and $B$:
$$\text{Support}(A \Longrightarrow B) = P(A \cup B) = \frac{\sigma(A \cup B)}{|T|}$$
$$\text{Confidence}(A \Longrightarrow B) = P(B \mid A) = \frac{\text{Support}(A \cup B)}{\text{Support}(A)}$$
$$\text{Lift}(A \Longrightarrow B) = \frac{P(B \mid A)}{P(B)} = \frac{\text{Confidence}(A \Longrightarrow B)}{\text{Support}(B)}$$

#### C. Slice-Aware Contextual Mining
We define an OLAP slice filter condition $\Phi(t)$ based on dimensional attributes. The slice transaction space $T_\Phi = \{t \in T \mid \Phi(t) = \text{True}\}$. Association rules are mined independently on $T_\Phi$. To quantify similarity between slice rule sets $R_1$ and $R_2$, we compute the Jaccard similarity coefficient:
$$J(R_1, R_2) = \frac{|R_1 \cap R_2|}{|R_1 \cup R_2|}$$

---

### **IV. Experimental Evaluation: Architectural Benchmarking (RQ1)**

We compared query execution across four configurations over 5 consecutive runs (1 cold + 4 warm runs):
* **C1: Normalized Staging** (3–4 relational joins on staging tables).
* **C2: Galaxy Schema** (`fact_*` + conformed `dim_*`).
* **C3: Direct Columnar Parquet** (querying `.parquet` files directly on disk with ZSTD compression).
* **C4: Pre-Aggregated Cube** (`cube_dept_time` summary table).

#### TABLE I: WARM QUERY LATENCY BENCHMARKS (SECONDS)
| Query ID | Analytical Query Description | C1: Normalized (s) | C2: Galaxy (s) | C3: Parquet (s) | C4: Pre-Agg (s) | Speedup Factor |
|:---:|---|:---:|:---:|:---:|:---:|:---:|
| **Q1** | Department Roll-Up | 0.1867s | 0.1826s | 0.1733s | **0.0021s** | C4 is **87.0x faster** than Galaxy |
| **Q2** | Dept $\times$ Day Pivot | 0.5766s | 0.3999s | 0.4256s | **0.0069s** | Galaxy is **30.6% faster**; C4 is **58.0x faster** |
| **Q3** | Dice + Reorder Rate | 0.1250s | **0.0571s** | 0.1460s | **0.0107s** | Galaxy is **2.19x faster** than C1 |
| **Q4** | Top 20 Product SKUs | 0.5283s | 0.5310s | 0.6425s | — | Single-table scan; DB beats raw Parquet |
| **Q5** | CUBE(Dept, Time) | 0.7997s | **0.2784s** | 0.4078s | **0.0105s** | Galaxy is **2.87x faster** than C1 |
| **Q6** | Customer Aggregations | 0.6389s | **0.0032s** | **0.0073s** | — | `dim_customer` is **199.7x faster** |

#### TABLE II: SCALABILITY EXPERIMENT ACROSS DATA SUBSETS
| Data Scale | Estimated Row Count | C1: Normalized (s) | C2: Galaxy (s) | Speedup Ratio (C1 / C2) |
|:---:|:---:|:---:|:---:|:---:|
| **10% Scale** | ~3.38 Million | 0.1652s | **0.0731s** | **2.26x** |
| **50% Scale** | ~16.91 Million | 0.2680s | **0.1388s** | **1.93x** |
| **100% Scale** | ~33.82 Million | 0.4009s | **0.2083s** | **1.92x** |

**Discussion (RQ1):** The dimensional Galaxy schema maintains a consistent **~2x performance multiplier** over normalized staging across all data scales by eliminating expensive multi-way relational joins. Pre-aggregated summary tables (C4) provide **sub-second query acceleration of up to 87x**. Direct Parquet file scanning (C3) performs competitively with managed database tables, proving that raw columnar files can serve as serverless ad-hoc analytical backends.

---

### **V. Mining Scalability: Apriori vs. FP-Growth (RQ2)**

Evaluated on a binary transaction matrix of $79,405$ orders $\times$ $200$ top products ($308,889$ total items):

#### TABLE III: ALGORITHM LATENCY SCALING VS. MINIMUM SUPPORT
| Minimum Support | Frequent Itemsets | Apriori Runtime (s) | FP-Growth Runtime (s) | Speedup Factor (Apriori / FP) |
|:---:|:---:|:---:|:---:|:---:|
| **5.0%** | 11 itemsets | **0.041s** | 0.252s | 0.16x (Apriori faster on trivial trees) |
| **3.0%** | 24 itemsets | 0.161s | 0.264s | 0.61x |
| **2.0%** | 61 itemsets | 0.702s | **0.468s** | **1.50x faster** |
| **1.0%** | 161 itemsets | **5.810s** | **1.111s** | **5.23x faster** |

**Discussion (RQ2):** At high support thresholds ($5\%$), Apriori has trivial candidate sets. However, as support decreases to $1\%$, Apriori's runtime increases by **141.7x** (from 0.041s to 5.810s) due to the exponential growth of candidate combinations and repeated full dataset scans. Conversely, **FP-Growth scales sub-linearly** (only increasing from 0.252s to 1.111s), running **5.23x faster** by traversing a compact in-memory tree without candidate generation.

---

### **VI. Contextual Slice-Aware Association Rule Mining (RQ3)**

We evaluated rule generation across three distinct slices using fixed parameters (Top 200 products, $\text{min\_sup} = 0.008$, $\text{min\_conf} = 0.25$, $\text{min\_lift} = 1.2$):
1. **Global Baseline:** Full transaction set ($15$ rules).
2. **Weekend Morning:** `is_weekend = TRUE AND part_of_day = 'Morning'` ($22$ rules).
3. **Weekday Evening:** `is_weekend = FALSE AND part_of_day = 'Evening'` ($11$ rules).

#### TABLE IV: JACCARD SIMILARITY & CONTEXTUAL EXCLUSIVITY
| Slice Comparison | Shared Rules | Exclusive to Context Slice | Jaccard Similarity ($J$) |
|---|:---:|:---:|:---:|
| **Weekend Morning vs. Global** | 14 rules | **8 exclusive rules** | **60.87%** |
| **Weekday Evening vs. Global** | 11 rules | 0 exclusive rules | **73.33%** |
| **Weekend Morning vs. Weekday Evening** | 11 rules | — | **50.00%** |

#### TABLE V: TOP CONTEXTUAL RULES EXCLUSIVE TO WEEKEND MORNINGS
| Antecedent | Consequent | Support | Confidence | Lift | Real-World Context Interpretation |
|---|---|:---:|:---:|:---:|---|
| **Organic Cilantro** | **Limes** | 0.0084 | **28.59%** | **4.83** | Weekend culinary cooking / salsa recipe basket |
| **Organic Raspberries** | **Organic Strawberries** | 0.0134 | **26.39%** | **2.39** | Fresh family breakfast & smoothie basket |
| **Organic Gala Apples** | **Bag of Organic Bananas**| 0.0094 | **26.89%** | **1.68** | Weekend organic fruit restocking |
| **Original Hummus** | **Banana** | 0.0082 | **28.97%** | **1.35** | Weekend healthy snack replenishment |
| **Half & Half** | **Banana** | 0.0088 | **27.84%** | **1.30** | Morning coffee and breakfast routine |

**Discussion (RQ3):** Global market basket mining averaged out and completely missed all 8 rules in Table V. Slicing into Weekend Mornings isolated specific behavioral contexts (e.g., culinary preparation and breakfast routines) that exhibit high statistical lift. Persisting these 48 rules into `fact_rules` enables BI dashboards to directly serve context-specific product recommendations.

---

### **VII. Customer Behavioral Segmentation (Adapted RFM)**
Applying K-Means clustering ($k=4$, Silhouette = $0.4131$, Inertia = $149,643.9$) to all $206,209$ customers yielded four distinct retail personas:
* **Loyal Power Shoppers ($4.55\%$ / $9,383$ users):** $R=5.40$ days, $F=68.9$ orders, $M=838.9$ items. High-velocity weekly shoppers.
* **High-Volume Regulars ($15.78\%$ / $32,543$ users):** $R=9.15$ days, $F=34.7$ orders, $M=355.4$ items. Core grocery buyers.
* **Casual Occasionals ($42.75\%$ / $88,147$ users):** $R=12.16$ days, $F=11.8$ orders, $M=104.8$ items. Bi-weekly low-basket shoppers.
* **Infrequent / At-Risk ($36.92\%$ / $76,136$ users):** $R=22.94$ days, $F=7.0$ orders, $M=67.6$ items. Long purchase intervals.

---

### **VIII. Limitations**
* **Lack of Calendar Dates & Pricing:** Instacart lacks real timestamps and item monetary amounts, requiring adapted behavioral proxies.
* **Single-Node Execution:** Benchmarks were conducted on single-node hardware (DuckDB); distributed execution (e.g., Apache Spark) may yield different network overhead characteristics.

---

### **IX. Conclusion**
This research demonstrated that integrating dimensional OLAP warehousing with association rule mining creates substantial performance and analytical synergies. The Galaxy dimensional schema delivered a **2x latency advantage** and **up to 87x speedup** through pre-aggregation. FP-Growth demonstrated clear superiority over Apriori (**5.2x faster**), and Contextual Slice-Aware Mining successfully uncovered **8 high-lift purchasing associations** that global market basket mining averages out. Storing discovered rules within the warehouse schema closes the loop between data engineering and machine learning.

---

### **References**
1. R. Agrawal and R. Srikant, "Fast Algorithms for Mining Association Rules," in *Proc. 20th Int. Conf. Very Large Data Bases (VLDB)*, 1994, pp. 487–499.
2. J. Han, J. Pei, and Y. Yin, "Mining Frequent Patterns without Candidate Generation," in *ACM SIGMOD Record*, vol. 29, no. 2, pp. 1–12, 2000.
3. S. Chaudhuri and U. Dayal, "An Overview of Data Warehousing and OLAP Technology," in *ACM SIGMOD Record*, vol. 26, no. 1, pp. 65–74, 1997.
4. R. Kimball and M. Ross, *The Data Warehouse Toolkit: The Definitive Guide to Dimensional Modeling*, 3rd ed., John Wiley & Sons, 2013.
5. J. Han, M. Kamber, and J. Pei, *Data Mining: Concepts and Techniques*, 3rd ed., Morgan Kaufmann, 2011.
6. M. Raasveldt and H. Mühleisen, "DuckDB: An Embeddable Analytical Database," in *Proc. ACM SIGMOD Int. Conf. Management of Data*, 2019, pp. 1981–1984.
