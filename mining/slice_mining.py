import os
import time
import duckdb
import pandas as pd
from mlxtend.frequent_patterns import fpgrowth, association_rules
import plotly.express as px

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "warehouse", "dwm.duckdb")
REPORT_DIR = os.path.join(BASE_DIR, "report")
os.makedirs(REPORT_DIR, exist_ok=True)

TOP_N = 200
SAMPLE_ORDERS = 80_000
MIN_SUPPORT = 0.008   # 0.8% support threshold allows capturing nuanced patterns
MIN_CONFIDENCE = 0.25
MIN_LIFT = 1.2


def fmt_items(items):
    return ", ".join(sorted(list(items)))


def mine_slice(con: duckdb.DuckDBPyConnection, slice_name: str, where_condition: str = None):
    print(f"\n--- Mining Slice: '{slice_name}' ---")
    where_clause = f"WHERE {where_condition}" if where_condition else ""

    t0 = time.time()
    df = con.execute(f"""
        WITH top_products AS (
            SELECT product_key 
            FROM fact_order_items
            GROUP BY product_key 
            ORDER BY COUNT(*) DESC 
            LIMIT {TOP_N}
        ),
        slice_orders AS (
            SELECT o.order_id 
            FROM fact_orders o
            JOIN dim_time t USING (time_key)
            {where_clause}
        ),
        sample_orders AS (
            SELECT order_id 
            FROM slice_orders 
            USING SAMPLE {SAMPLE_ORDERS} ROWS (reservoir, 42)
        )
        SELECT f.order_id, p.product_name
        FROM fact_order_items f
        JOIN top_products USING (product_key)
        JOIN sample_orders USING (order_id)
        JOIN dim_product p USING (product_key);
    """).df()

    print(f"  -> Extracted {len(df):,} items across sampled orders in {time.time() - t0:.2f}s.")

    # Matrix crosstab
    basket = pd.crosstab(df["order_id"], df["product_name"]).astype(bool)

    # FP-Growth
    t0 = time.time()
    fi = fpgrowth(basket, min_support=MIN_SUPPORT, use_colnames=True)
    rules = association_rules(fi, metric="lift", min_threshold=MIN_LIFT)
    rules = rules[rules["confidence"] >= MIN_CONFIDENCE].sort_values("lift", ascending=False)
    mine_time = time.time() - t0

    print(f"  -> Generated {len(rules):,} association rules in {mine_time:.2f}s.")

    if len(rules) == 0:
        return pd.DataFrame(columns=["slice_name", "antecedent", "consequent", "support", "confidence", "lift", "rule_signature"])

    rules["slice_name"] = slice_name
    rules["antecedent"] = rules["antecedents"].apply(fmt_items)
    rules["consequent"] = rules["consequents"].apply(fmt_items)
    rules["rule_signature"] = rules["antecedent"] + " ==> " + rules["consequent"]

    cols = ["slice_name", "antecedent", "consequent", "support", "confidence", "lift", "rule_signature"]
    return rules[cols]


def compare_slices(global_rules, weekend_morning_rules, weekday_evening_rules):
    print("\n" + "=" * 70)
    print("RESEARCH QUESTION 3: SLICE-AWARE MINING VS. GLOBAL MINING COMPARISON")
    print("=" * 70)

    g_set = set(global_rules["rule_signature"])
    wm_set = set(weekend_morning_rules["rule_signature"])
    we_set = set(weekday_evening_rules["rule_signature"])

    # Jaccard index
    def jaccard(s1, s2):
        if not s1 or not s2:
            return 0.0
        return round(len(s1.intersection(s2)) / len(s1.union(s2)), 4)

    j_wm_g = jaccard(wm_set, g_set)
    j_we_g = jaccard(we_set, g_set)
    j_wm_we = jaccard(wm_set, we_set)

    # Contextual rules (discovered in slice but NOT in global)
    wm_exclusive = weekend_morning_rules[~weekend_morning_rules["rule_signature"].isin(g_set)]
    we_exclusive = weekday_evening_rules[~weekday_evening_rules["rule_signature"].isin(g_set)]

    print(f"Rule Counts: Global={len(g_set):,} | Weekend Morning={len(wm_set):,} | Weekday Evening={len(we_set):,}")
    print(f"Jaccard Similarity (Weekend Morning vs Global): {j_wm_g * 100:.2f}%")
    print(f"Jaccard Similarity (Weekday Evening vs Global): {j_we_g * 100:.2f}%")
    print(f"Jaccard Similarity (Weekend Morning vs Weekday Evening): {j_wm_we * 100:.2f}%")
    print(f"Contextual Rules Discovered Exclusive to Weekend Mornings: {len(wm_exclusive)}")
    print(f"Contextual Rules Discovered Exclusive to Weekday Evenings: {len(we_exclusive)}")

    if len(wm_exclusive) > 0:
        print("\nTop 5 Contextual Rules Exclusive to Weekend Mornings:")
        print(wm_exclusive[["antecedent", "consequent", "confidence", "lift"]].head(5).to_string(index=False))

    if len(we_exclusive) > 0:
        print("\nTop 5 Contextual Rules Exclusive to Weekday Evenings:")
        print(we_exclusive[["antecedent", "consequent", "confidence", "lift"]].head(5).to_string(index=False))

    comparison_summary = [
        {"Comparison": "Weekend Morning vs Global", "Shared Rules": len(wm_set.intersection(g_set)), "Exclusive to Slice": len(wm_exclusive), "Jaccard Similarity": j_wm_g},
        {"Comparison": "Weekday Evening vs Global", "Shared Rules": len(we_set.intersection(g_set)), "Exclusive to Slice": len(we_exclusive), "Jaccard Similarity": j_we_g},
        {"Comparison": "Weekend Morning vs Weekday Evening", "Shared Rules": len(wm_set.intersection(we_set)), "Exclusive to Slice": "-", "Jaccard Similarity": j_wm_we},
    ]
    pd.DataFrame(comparison_summary).to_csv(os.path.join(REPORT_DIR, "slice_mining_comparison.csv"), index=False)


def persist_rules_to_warehouse(con: duckdb.DuckDBPyConnection, all_rules_df: pd.DataFrame):
    print("\n" + "=" * 70)
    print("PERSISTING MINED ASSOCIATION RULES INTO WAREHOUSE (fact_rules)")
    print("=" * 70)

    con.execute("CREATE TABLE IF NOT EXISTS fact_rules (slice_name VARCHAR, antecedent VARCHAR, consequent VARCHAR, support DOUBLE, confidence DOUBLE, lift DOUBLE);")
    con.execute("DELETE FROM fact_rules;")

    clean_rules = all_rules_df[["slice_name", "antecedent", "consequent", "support", "confidence", "lift"]].copy()
    con.register("clean_rules_df", clean_rules)
    con.execute("INSERT INTO fact_rules SELECT * FROM clean_rules_df;")

    rule_count = con.execute("SELECT COUNT(*) FROM fact_rules;").fetchone()[0]
    print(f" -> Successfully persisted {rule_count:,} association rules across slices into 'fact_rules'!")

    # Export to Parquet
    pq_path = os.path.join(BASE_DIR, "data", "warehouse", "fact_rules.parquet").replace("\\", "/")
    con.execute(f"COPY fact_rules TO '{pq_path}' (FORMAT PARQUET, COMPRESSION ZSTD);")
    print(f" -> Exported fact_rules.parquet.")


def main():
    con = duckdb.connect(DB_PATH)
    try:
        # 1. Global Baseline
        global_rules = mine_slice(con, "Global_Baseline", None)

        # 2. Weekend Morning Slice (Breakfast / Family replenishment)
        wm_rules = mine_slice(con, "Weekend_Morning", "t.is_weekend = TRUE AND t.part_of_day = 'Morning'")

        # 3. Weekday Evening Slice (Quick dinner prep / Evening grocery)
        we_rules = mine_slice(con, "Weekday_Evening", "t.is_weekend = FALSE AND t.part_of_day = 'Evening'")

        # 4. Compare Slices (RQ3)
        compare_slices(global_rules, wm_rules, we_rules)

        # 5. Persist to warehouse
        combined = pd.concat([global_rules, wm_rules, we_rules], ignore_index=True)
        persist_rules_to_warehouse(con, combined)
    finally:
        con.close()


if __name__ == "__main__":
    main()
