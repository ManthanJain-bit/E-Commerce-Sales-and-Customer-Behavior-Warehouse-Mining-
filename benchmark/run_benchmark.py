import os
import time
import statistics
import csv
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "warehouse", "dwm.duckdb")
BENCH_DIR = os.path.join(BASE_DIR, "benchmark")
REPORT_DIR = os.path.join(BASE_DIR, "report")
os.makedirs(BENCH_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

# Parquet paths formatted with forward slashes for DuckDB
FOI_PQ = os.path.join(BASE_DIR, "data", "warehouse", "fact_order_items.parquet").replace("\\", "/")
DP_PQ  = os.path.join(BASE_DIR, "data", "warehouse", "dim_product.parquet").replace("\\", "/")
DT_PQ  = os.path.join(BASE_DIR, "data", "warehouse", "dim_time.parquet").replace("\\", "/")
DC_PQ  = os.path.join(BASE_DIR, "data", "warehouse", "dim_customer.parquet").replace("\\", "/")

BENCHMARK_QUERIES = {
    "Q1_Dept_Rollup": {
        "C1_Normalized": """
            SELECT d.department, COUNT(*) AS items_sold
            FROM stg_op op
            JOIN stg_products p ON op.product_id = p.product_id
            JOIN stg_departments d ON p.department_id = d.department_id
            GROUP BY d.department;
        """,
        "C2_Galaxy": """
            SELECT p.department, COUNT(*) AS items_sold
            FROM fact_order_items f
            JOIN dim_product p USING (product_key)
            GROUP BY p.department;
        """,
        "C3_Parquet": f"""
            SELECT p.department, COUNT(*) AS items_sold
            FROM '{FOI_PQ}' f
            JOIN '{DP_PQ}' p ON f.product_key = p.product_key
            GROUP BY p.department;
        """,
        "C4_PreAgg": """
            SELECT department, SUM(items) AS items_sold
            FROM cube_dept_time
            GROUP BY department;
        """
    },
    "Q2_Dept_Day_Pivot": {
        "C1_Normalized": """
            SELECT d.department,
                   SUM(CASE WHEN o.order_dow = 0 THEN 1 ELSE 0 END) AS d0,
                   SUM(CASE WHEN o.order_dow = 1 THEN 1 ELSE 0 END) AS d1,
                   SUM(CASE WHEN o.order_dow = 2 THEN 1 ELSE 0 END) AS d2,
                   SUM(CASE WHEN o.order_dow = 3 THEN 1 ELSE 0 END) AS d3,
                   SUM(CASE WHEN o.order_dow = 4 THEN 1 ELSE 0 END) AS d4,
                   SUM(CASE WHEN o.order_dow = 5 THEN 1 ELSE 0 END) AS d5,
                   SUM(CASE WHEN o.order_dow = 6 THEN 1 ELSE 0 END) AS d6
            FROM stg_op op
            JOIN stg_orders o USING (order_id)
            JOIN stg_products p ON op.product_id = p.product_id
            JOIN stg_departments d ON p.department_id = d.department_id
            GROUP BY d.department;
        """,
        "C2_Galaxy": """
            SELECT p.department,
                   SUM(CASE WHEN t.order_dow = 0 THEN 1 ELSE 0 END) AS d0,
                   SUM(CASE WHEN t.order_dow = 1 THEN 1 ELSE 0 END) AS d1,
                   SUM(CASE WHEN t.order_dow = 2 THEN 1 ELSE 0 END) AS d2,
                   SUM(CASE WHEN t.order_dow = 3 THEN 1 ELSE 0 END) AS d3,
                   SUM(CASE WHEN t.order_dow = 4 THEN 1 ELSE 0 END) AS d4,
                   SUM(CASE WHEN t.order_dow = 5 THEN 1 ELSE 0 END) AS d5,
                   SUM(CASE WHEN t.order_dow = 6 THEN 1 ELSE 0 END) AS d6
            FROM fact_order_items f
            JOIN dim_product p USING (product_key)
            JOIN dim_time t USING (time_key)
            GROUP BY p.department;
        """,
        "C3_Parquet": f"""
            SELECT p.department,
                   SUM(CASE WHEN t.order_dow = 0 THEN 1 ELSE 0 END) AS d0,
                   SUM(CASE WHEN t.order_dow = 1 THEN 1 ELSE 0 END) AS d1,
                   SUM(CASE WHEN t.order_dow = 2 THEN 1 ELSE 0 END) AS d2,
                   SUM(CASE WHEN t.order_dow = 3 THEN 1 ELSE 0 END) AS d3,
                   SUM(CASE WHEN t.order_dow = 4 THEN 1 ELSE 0 END) AS d4,
                   SUM(CASE WHEN t.order_dow = 5 THEN 1 ELSE 0 END) AS d5,
                   SUM(CASE WHEN t.order_dow = 6 THEN 1 ELSE 0 END) AS d6
            FROM '{FOI_PQ}' f
            JOIN '{DP_PQ}' p ON f.product_key = p.product_key
            JOIN '{DT_PQ}' t ON f.time_key = t.time_key
            GROUP BY p.department;
        """,
        "C4_PreAgg": """
            SELECT department,
                   SUM(CASE WHEN order_dow = 0 THEN items ELSE 0 END) AS d0,
                   SUM(CASE WHEN order_dow = 1 THEN items ELSE 0 END) AS d1,
                   SUM(CASE WHEN order_dow = 2 THEN items ELSE 0 END) AS d2,
                   SUM(CASE WHEN order_dow = 3 THEN items ELSE 0 END) AS d3,
                   SUM(CASE WHEN order_dow = 4 THEN items ELSE 0 END) AS d4,
                   SUM(CASE WHEN order_dow = 5 THEN items ELSE 0 END) AS d5,
                   SUM(CASE WHEN order_dow = 6 THEN items ELSE 0 END) AS d6
            FROM cube_dept_time
            GROUP BY department;
        """
    },
    "Q3_Dice_Reorder_Rate": {
        "C1_Normalized": """
            SELECT d.department, AVG(op.reordered) AS reorder_rate
            FROM stg_op op
            JOIN stg_orders o USING (order_id)
            JOIN stg_products p ON op.product_id = p.product_id
            JOIN stg_departments d ON p.department_id = d.department_id
            WHERE d.department IN ('produce', 'dairy eggs')
              AND o.order_dow IN (0, 1)
              AND CAST(o.order_hour_of_day AS INTEGER) BETWEEN 8 AND 12
            GROUP BY d.department;
        """,
        "C2_Galaxy": """
            SELECT p.department, AVG(f.reordered) AS reorder_rate
            FROM fact_order_items f
            JOIN dim_product p USING (product_key)
            JOIN dim_time t USING (time_key)
            WHERE p.department IN ('produce', 'dairy eggs')
              AND t.is_weekend = TRUE
              AND t.hour BETWEEN 8 AND 12
            GROUP BY p.department;
        """,
        "C3_Parquet": f"""
            SELECT p.department, AVG(f.reordered) AS reorder_rate
            FROM '{FOI_PQ}' f
            JOIN '{DP_PQ}' p ON f.product_key = p.product_key
            JOIN '{DT_PQ}' t ON f.time_key = t.time_key
            WHERE p.department IN ('produce', 'dairy eggs')
              AND t.is_weekend = TRUE
              AND t.hour BETWEEN 8 AND 12
            GROUP BY p.department;
        """,
        "C4_PreAgg": """
            SELECT department, SUM(reordered_items) * 1.0 / SUM(items) AS reorder_rate
            FROM cube_dept_time
            WHERE department IN ('produce', 'dairy eggs')
              AND order_dow IN (0, 1)
              AND hour BETWEEN 8 AND 12
            GROUP BY department;
        """
    },
    "Q4_Top_20_Products": {
        "C1_Normalized": """
            SELECT p.product_name, COUNT(*) AS items, AVG(op.reordered) AS reorder_rate
            FROM stg_op op
            JOIN stg_products p USING (product_id)
            GROUP BY p.product_name
            ORDER BY items DESC
            LIMIT 20;
        """,
        "C2_Galaxy": """
            SELECT p.product_name, COUNT(*) AS items, AVG(f.reordered) AS reorder_rate
            FROM fact_order_items f
            JOIN dim_product p USING (product_key)
            GROUP BY p.product_name
            ORDER BY items DESC
            LIMIT 20;
        """,
        "C3_Parquet": f"""
            SELECT p.product_name, COUNT(*) AS items, AVG(f.reordered) AS reorder_rate
            FROM '{FOI_PQ}' f
            JOIN '{DP_PQ}' p ON f.product_key = p.product_key
            GROUP BY p.product_name
            ORDER BY items DESC
            LIMIT 20;
        """
    },
    "Q5_Cube_Dept_Time": {
        "C1_Normalized": """
            SELECT d.department,
                   CASE WHEN CAST(o.order_hour_of_day AS INTEGER) BETWEEN 5 AND 11 THEN 'Morning'
                        WHEN CAST(o.order_hour_of_day AS INTEGER) BETWEEN 12 AND 16 THEN 'Afternoon'
                        WHEN CAST(o.order_hour_of_day AS INTEGER) BETWEEN 17 AND 21 THEN 'Evening'
                        ELSE 'Night' END AS part_of_day,
                   COUNT(*) AS items
            FROM stg_op op
            JOIN stg_orders o USING (order_id)
            JOIN stg_products p ON op.product_id = p.product_id
            JOIN stg_departments d ON p.department_id = d.department_id
            GROUP BY CUBE (d.department, part_of_day);
        """,
        "C2_Galaxy": """
            SELECT p.department, t.part_of_day, COUNT(*) AS items
            FROM fact_order_items f
            JOIN dim_product p USING (product_key)
            JOIN dim_time t USING (time_key)
            GROUP BY CUBE (p.department, t.part_of_day);
        """,
        "C3_Parquet": f"""
            SELECT p.department, t.part_of_day, COUNT(*) AS items
            FROM '{FOI_PQ}' f
            JOIN '{DP_PQ}' p ON f.product_key = p.product_key
            JOIN '{DT_PQ}' t ON f.time_key = t.time_key
            GROUP BY CUBE (p.department, t.part_of_day);
        """,
        "C4_PreAgg": """
            SELECT department,
                   CASE WHEN hour BETWEEN 5 AND 11 THEN 'Morning'
                        WHEN hour BETWEEN 12 AND 16 THEN 'Afternoon'
                        WHEN hour BETWEEN 17 AND 21 THEN 'Evening'
                        ELSE 'Night' END AS part_of_day,
                   SUM(items) AS items
            FROM cube_dept_time
            GROUP BY CUBE (department, part_of_day);
        """
    },
    "Q6_Customer_Aggregation": {
        "C1_Normalized": """
            SELECT o.user_id, COUNT(DISTINCT o.order_id) AS total_orders, COUNT(op.product_id) AS total_items
            FROM stg_orders o
            JOIN stg_op op USING (order_id)
            GROUP BY o.user_id
            LIMIT 100;
        """,
        "C2_Galaxy": """
            SELECT customer_key, total_orders, total_items
            FROM dim_customer
            LIMIT 100;
        """,
        "C3_Parquet": f"""
            SELECT customer_key, total_orders, total_items
            FROM '{DC_PQ}'
            LIMIT 100;
        """
    }
}


def run_latency_benchmark(con: duckdb.DuckDBPyConnection, runs: int = 5):
    print("=" * 70)
    print("WEEK 4: ARCHITECTURAL PERFORMANCE BENCHMARKING (C1 - C4)")
    print(f"Executing {len(BENCHMARK_QUERIES)} queries x {runs} runs each...")
    print("=" * 70)

    rows = []

    for qname, cfgs in BENCHMARK_QUERIES.items():
        print(f"\nEvaluating Query: {qname}")
        for cfg, sql in cfgs.items():
            latencies = []
            for r in range(runs):
                t0 = time.perf_counter()
                con.execute(sql).fetchall()
                elapsed = time.perf_counter() - t0
                latencies.append(elapsed)

            cold_run = latencies[0]
            warm_mean = statistics.mean(latencies[1:]) if len(latencies) > 1 else cold_run
            warm_std = statistics.stdev(latencies[1:]) if len(latencies) > 2 else 0.0

            rows.append({
                "Query": qname,
                "Config": cfg,
                "Cold Run (s)": round(cold_run, 4),
                "Warm Mean (s)": round(warm_mean, 4),
                "Warm Stdev (s)": round(warm_std, 4)
            })
            print(f"  -> [{cfg:14s}] Cold: {cold_run:.4f}s | Warm Mean: {warm_mean:.4f}s (+/- {warm_std:.4f}s)")

    df_results = pd.DataFrame(rows)
    df_results.to_csv(os.path.join(BENCH_DIR, "results.csv"), index=False)
    return df_results


def run_scalability_test(con: duckdb.DuckDBPyConnection):
    print("\n" + "=" * 70)
    print("WEEK 4: SCALABILITY EXPERIMENT (10%, 50%, 100% Data Scale)")
    print("=" * 70)

    scale_configs = [
        ("10%", "order_id % 10 < 1"),
        ("50%", "order_id % 10 < 5"),
        ("100%", "order_id % 10 < 10"),
    ]

    scalability_rows = []

    for scale_label, filter_condition in scale_configs:
        print(f"\nTesting Scale: {scale_label} ({filter_condition})")

        # C1 Normalized query at scale
        sql_c1 = f"""
            SELECT d.department, COUNT(*) AS items_sold
            FROM stg_op op
            JOIN stg_orders o USING (order_id)
            JOIN stg_products p ON op.product_id = p.product_id
            JOIN stg_departments d ON p.department_id = d.department_id
            WHERE {filter_condition}
            GROUP BY d.department;
        """
        # C2 Galaxy query at scale
        sql_c2 = f"""
            SELECT p.department, COUNT(*) AS items_sold
            FROM fact_order_items f
            JOIN dim_product p USING (product_key)
            WHERE {filter_condition}
            GROUP BY p.department;
        """

        times_c1 = []
        times_c2 = []
        for _ in range(3):
            t0 = time.perf_counter()
            con.execute(sql_c1).fetchall()
            times_c1.append(time.perf_counter() - t0)

            t0 = time.perf_counter()
            con.execute(sql_c2).fetchall()
            times_c2.append(time.perf_counter() - t0)

        mean_c1 = round(statistics.mean(times_c1), 4)
        mean_c2 = round(statistics.mean(times_c2), 4)
        speedup = round(mean_c1 / mean_c2, 2) if mean_c2 > 0 else 1.0

        scalability_rows.append({
            "Data Scale": scale_label,
            "C1 Normalized (s)": mean_c1,
            "C2 Galaxy (s)": mean_c2,
            "Speedup (C1/C2)": speedup
        })
        print(f"  -> Scale {scale_label}: C1={mean_c1}s | C2={mean_c2}s | Speedup={speedup}x")

    df_scale = pd.DataFrame(scalability_rows)
    df_scale.to_csv(os.path.join(BENCH_DIR, "scalability_results.csv"), index=False)
    return df_scale


def generate_benchmark_charts(df_results: pd.DataFrame, df_scale: pd.DataFrame):
    print("\nGenerating Benchmark Visualizations...")
    # Chart 1: Latency by Query and Config
    fig1 = px.bar(
        df_results,
        x="Query",
        y="Warm Mean (s)",
        color="Config",
        barmode="group",
        title="Warm Query Latency Comparison across Architectural Configurations (RQ1)",
        labels={"Warm Mean (s)": "Mean Latency (Seconds, lower is better)"},
        template="plotly_white"
    )
    fig1.write_html(os.path.join(REPORT_DIR, "benchmark_architectures.html"))

    # Chart 2: Scalability Curves
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=df_scale["Data Scale"], y=df_scale["C1 Normalized (s)"], mode="lines+markers", name="C1: Normalized"))
    fig2.add_trace(go.Scatter(x=df_scale["Data Scale"], y=df_scale["C2 Galaxy (s)"], mode="lines+markers", name="C2: Galaxy Schema"))
    fig2.update_layout(
        title="Scalability Analysis: Execution Latency across Data Volumes (10%, 50%, 100%)",
        xaxis_title="Dataset Scale",
        yaxis_title="Execution Time (Seconds)",
        template="plotly_white"
    )
    fig2.write_html(os.path.join(REPORT_DIR, "benchmark_scalability.html"))
    print("Charts generated in report/ directory.")


def main():
    con = duckdb.connect(DB_PATH, read_only=True)
    try:
        df_results = run_latency_benchmark(con, runs=5)
        df_scale = run_scalability_test(con)
        generate_benchmark_charts(df_results, df_scale)

        print("\n" + "=" * 70)
        print("SUMMARY TABLE: WARM QUERY LATENCIES (Seconds)")
        print("=" * 70)
        pivot_view = df_results.pivot(index="Query", columns="Config", values="Warm Mean (s)")
        print(pivot_view.to_string())

        print("\n" + "=" * 70)
        print("SUMMARY TABLE: SCALABILITY TEST")
        print("=" * 70)
        print(df_scale.to_string(index=False))
    finally:
        con.close()


if __name__ == "__main__":
    main()
