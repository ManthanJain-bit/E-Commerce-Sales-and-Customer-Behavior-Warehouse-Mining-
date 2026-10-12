import os
import time
import duckdb
import pandas as pd
from mlxtend.frequent_patterns import apriori, fpgrowth, association_rules
import plotly.express as px

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "warehouse", "dwm.duckdb")
REPORT_DIR = os.path.join(BASE_DIR, "report")
os.makedirs(REPORT_DIR, exist_ok=True)

TOP_N = 200          # Top 200 high-velocity products
N_ORDERS = 100_000   # Representative sample of 100,000 orders


def build_basket_matrix(con: duckdb.DuckDBPyConnection):
    print(f"Building market basket matrix for Top {TOP_N} products across {N_ORDERS:,} orders...")
    t0 = time.time()
    df = con.execute(f"""
        WITH top_products AS (
            SELECT product_key 
            FROM fact_order_items
            GROUP BY product_key 
            ORDER BY COUNT(*) DESC 
            LIMIT {TOP_N}
        ),
        order_sample AS (
            SELECT order_id 
            FROM fact_orders 
            USING SAMPLE {N_ORDERS} ROWS (reservoir, 42)
        )
        SELECT f.order_id, p.product_name
        FROM fact_order_items f
        JOIN top_products USING (product_key)
        JOIN order_sample USING (order_id)
        JOIN dim_product p USING (product_key);
    """).df()

    load_time = time.time() - t0
    print(f" -> Extracted {len(df):,} transaction records in {load_time:.2f}s.")

    # Pivot to binary one-hot crosstab
    t0 = time.time()
    basket = pd.crosstab(df["order_id"], df["product_name"]).astype(bool)
    matrix_time = time.time() - t0
    print(f" -> Constructed binary basket matrix: {basket.shape[0]:,} orders x {basket.shape[1]} products in {matrix_time:.2f}s.")
    return basket


def benchmark_algorithms(basket: pd.DataFrame):
    print("\n" + "=" * 70)
    print("RESEARCH QUESTION 2: APRIORI VS. FP-GROWTH SCALABILITY BENCHMARK")
    print("=" * 70)

    supports = [0.05, 0.03, 0.02, 0.01]
    bench_results = []

    for min_sup in supports:
        print(f"\n--- Testing Minimum Support: {min_sup * 100:.1f}% ---")

        # 1. Benchmark FP-Growth
        t0 = time.perf_counter()
        fi_fp = fpgrowth(basket, min_support=min_sup, use_colnames=True)
        fp_time = time.perf_counter() - t0
        itemset_count = len(fi_fp)

        # 2. Benchmark Apriori
        t0 = time.perf_counter()
        fi_ap = apriori(basket, min_support=min_sup, use_colnames=True)
        ap_time = time.perf_counter() - t0

        speedup = round(ap_time / fp_time, 2) if fp_time > 0 else 1.0

        bench_results.append({
            "Min Support": min_sup,
            "Min Support (%)": f"{min_sup * 100:.1f}%",
            "Frequent Itemsets": itemset_count,
            "Apriori Latency (s)": round(ap_time, 4),
            "FP-Growth Latency (s)": round(fp_time, 4),
            "Speedup (Apriori / FP)": speedup
        })
        print(f"  Itemsets: {itemset_count:,} | Apriori: {ap_time:.3f}s | FP-Growth: {fp_time:.3f}s | Speedup: {speedup}x")

    df_bench = pd.DataFrame(bench_results)
    df_bench.to_csv(os.path.join(REPORT_DIR, "apriori_vs_fpgrowth_benchmark.csv"), index=False)

    # Plot Comparison Chart
    fig = px.line(
        df_bench,
        x="Min Support (%)",
        y=["Apriori Latency (s)", "FP-Growth Latency (s)"],
        title="RQ2: Apriori vs FP-Growth Execution Latency vs. Minimum Support",
        markers=True,
        labels={"value": "Runtime (Seconds)", "variable": "Algorithm"},
        template="plotly_white"
    )
    fig.write_html(os.path.join(REPORT_DIR, "apriori_vs_fpgrowth_chart.html"))
    return df_bench


def generate_rules(basket: pd.DataFrame, min_sup: float = 0.01, min_conf: float = 0.3, min_lift: float = 1.2):
    print("\n" + "=" * 70)
    print("GLOBAL ASSOCIATION RULES GENERATION (FP-GROWTH)")
    print("=" * 70)

    t0 = time.time()
    fi = fpgrowth(basket, min_support=min_sup, use_colnames=True)
    rules = association_rules(fi, metric="lift", min_threshold=min_lift)
    rules = rules[rules["confidence"] >= min_conf].sort_values("lift", ascending=False)
    gen_time = time.time() - t0

    print(f"Generated {len(rules):,} association rules (min_sup={min_sup}, min_conf={min_conf}, min_lift={min_lift}) in {gen_time:.2f}s.")

    def fmt_items(items):
        return ", ".join(sorted(list(items)))

    rules_clean = rules.copy()
    rules_clean["antecedent"] = rules_clean["antecedents"].apply(fmt_items)
    rules_clean["consequent"] = rules_clean["consequents"].apply(fmt_items)
    cols = ["antecedent", "consequent", "support", "confidence", "lift"]
    display_rules = rules_clean[cols].round(4)

    print("\nTop 10 Global Association Rules by Lift:")
    print(display_rules.head(10).to_string(index=False))

    display_rules.to_csv(os.path.join(REPORT_DIR, "global_association_rules.csv"), index=False)
    return display_rules


def main():
    con = duckdb.connect(DB_PATH, read_only=True)
    try:
        basket = build_basket_matrix(con)
        df_bench = benchmark_algorithms(basket)
        rules = generate_rules(basket, min_sup=0.01, min_conf=0.25, min_lift=1.2)
    finally:
        con.close()


if __name__ == "__main__":
    main()
