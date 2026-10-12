import os
import time
import duckdb
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "warehouse", "dwm.duckdb")
REPORT_DIR = os.path.join(BASE_DIR, "report")
os.makedirs(REPORT_DIR, exist_ok=True)


def execute_olap_suite(con: duckdb.DuckDBPyConnection):
    print("=" * 70)
    print("WEEK 3: OLAP MULTIDIMENSIONAL ANALYTICAL ENGINE EXECUTION")
    print("=" * 70)

    results_summary = []

    # -------------------------------------------------------------------------
    # 1. ROLL-UP (Department -> Aisle)
    # -------------------------------------------------------------------------
    print("\n[1. ROLL-UP OPERATION: Department -> Aisle Hierarchy]")
    t0 = time.time()
    df_rollup = con.execute("""
        SELECT 
            COALESCE(p.department, '>> GRAND TOTAL') AS department,
            COALESCE(p.aisle, '-> SUB-TOTAL') AS aisle,
            COUNT(*) AS items_sold,
            ROUND(AVG(f.reordered) * 100, 2) AS reorder_rate_pct
        FROM fact_order_items f
        JOIN dim_product p USING (product_key)
        GROUP BY ROLLUP (p.department, p.aisle)
        ORDER BY p.department NULLS LAST, p.aisle NULLS LAST;
    """).df()
    lat_rollup = time.time() - t0
    print(f"Executed in {lat_rollup:.3f}s. Total aggregated combinations: {len(df_rollup)}")
    print("Top 5 Roll-up Rows Preview:")
    print(df_rollup.head(6).to_string(index=False))
    results_summary.append({"Operation": "Roll-up", "Target": "Dept -> Aisle -> Grand Total", "Rows": len(df_rollup), "Latency (s)": round(lat_rollup, 3)})

    # -------------------------------------------------------------------------
    # 2. DRILL-DOWN (Department -> Aisle -> Top Products)
    # -------------------------------------------------------------------------
    print("\n[2. DRILL-DOWN OPERATION: Department -> Produce Aisle -> Fruit Products]")
    t0 = time.time()
    # Level 1: Dept
    df_dd_l1 = con.execute("""
        SELECT p.department, COUNT(*) AS items_sold
        FROM fact_order_items f JOIN dim_product p USING (product_key)
        GROUP BY p.department ORDER BY items_sold DESC LIMIT 3;
    """).df()
    # Level 2: Top Produce Aisles
    df_dd_l2 = con.execute("""
        SELECT p.aisle, COUNT(*) AS items_sold, ROUND(AVG(f.reordered) * 100, 2) AS reorder_rate_pct
        FROM fact_order_items f JOIN dim_product p USING (product_key)
        WHERE p.department = 'produce'
        GROUP BY p.aisle ORDER BY items_sold DESC LIMIT 3;
    """).df()
    # Level 3: Top Products in 'fresh fruits'
    df_dd_l3 = con.execute("""
        SELECT p.product_name, COUNT(*) AS items_sold, ROUND(AVG(f.reordered) * 100, 2) AS reorder_rate_pct
        FROM fact_order_items f JOIN dim_product p USING (product_key)
        WHERE p.aisle = 'fresh fruits'
        GROUP BY p.product_name ORDER BY items_sold DESC LIMIT 5;
    """).df()
    lat_dd = time.time() - t0
    print(f"Executed in {lat_dd:.3f}s.")
    print("Level 1 (Top Departments):\n", df_dd_l1.to_string(index=False))
    print("Level 2 (Produce Aisles):\n", df_dd_l2.to_string(index=False))
    print("Level 3 (Fresh Fruits Products):\n", df_dd_l3.to_string(index=False))
    results_summary.append({"Operation": "Drill-down", "Target": "Produce -> Fresh Fruits -> SKUs", "Rows": 5, "Latency (s)": round(lat_dd, 3)})

    # -------------------------------------------------------------------------
    # 3. SLICE (Fixing Time = Weekend)
    # -------------------------------------------------------------------------
    print("\n[3. SLICE OPERATION: Fixing Time Dimension (is_weekend = TRUE)]")
    t0 = time.time()
    df_slice = con.execute("""
        SELECT 
            p.department, 
            COUNT(*) AS weekend_items_sold,
            ROUND(AVG(f.reordered) * 100, 2) AS weekend_reorder_rate_pct
        FROM fact_order_items f
        JOIN dim_product p USING (product_key)
        JOIN dim_time t USING (time_key)
        WHERE t.is_weekend = TRUE
        GROUP BY p.department
        ORDER BY weekend_items_sold DESC
        LIMIT 5;
    """).df()
    lat_slice = time.time() - t0
    print(f"Executed in {lat_slice:.3f}s.")
    print(df_slice.to_string(index=False))
    results_summary.append({"Operation": "Slice", "Target": "Weekend Only (is_weekend=True)", "Rows": len(df_slice), "Latency (s)": round(lat_slice, 3)})

    # -------------------------------------------------------------------------
    # 4. DICE (Sub-cube: Departments in ('produce', 'dairy eggs') x Weekend x Morning 8-12)
    # -------------------------------------------------------------------------
    print("\n[4. DICE OPERATION: Sub-cube (Produce/Dairy x Weekend x Morning Hours 8-12)]")
    t0 = time.time()
    df_dice = con.execute("""
        SELECT 
            p.department,
            t.hour,
            COUNT(*) AS items_sold,
            ROUND(AVG(f.reordered) * 100, 2) AS reorder_rate_pct
        FROM fact_order_items f
        JOIN dim_product p USING (product_key)
        JOIN dim_time t USING (time_key)
        WHERE p.department IN ('produce', 'dairy eggs')
          AND t.is_weekend = TRUE
          AND t.hour BETWEEN 8 AND 12
        GROUP BY p.department, t.hour
        ORDER BY p.department, t.hour;
    """).df()
    lat_dice = time.time() - t0
    print(f"Executed in {lat_dice:.3f}s. Generated {len(df_dice)} coordinate cells.")
    print(df_dice.head(8).to_string(index=False))
    results_summary.append({"Operation": "Dice", "Target": "2 Depts x Weekend x Hours 8-12", "Rows": len(df_dice), "Latency (s)": round(lat_dice, 3)})

    # -------------------------------------------------------------------------
    # 5. PIVOT (Cross-Tabulation: Department x Day of Week 0..6)
    # -------------------------------------------------------------------------
    print("\n[5. PIVOT OPERATION: Department x Day of Week Cross-Tabulation]")
    t0 = time.time()
    df_pivot = con.execute("""
        SELECT 
            p.department,
            SUM(CASE WHEN t.order_dow = 0 THEN 1 ELSE 0 END) AS Day_0_Wknd,
            SUM(CASE WHEN t.order_dow = 1 THEN 1 ELSE 0 END) AS Day_1_Wknd,
            SUM(CASE WHEN t.order_dow = 2 THEN 1 ELSE 0 END) AS Day_2,
            SUM(CASE WHEN t.order_dow = 3 THEN 1 ELSE 0 END) AS Day_3,
            SUM(CASE WHEN t.order_dow = 4 THEN 1 ELSE 0 END) AS Day_4,
            SUM(CASE WHEN t.order_dow = 5 THEN 1 ELSE 0 END) AS Day_5,
            SUM(CASE WHEN t.order_dow = 6 THEN 1 ELSE 0 END) AS Day_6,
            COUNT(*) AS Total
        FROM fact_order_items f
        JOIN dim_product p USING (product_key)
        JOIN dim_time t USING (time_key)
        GROUP BY p.department
        ORDER BY Total DESC
        LIMIT 5;
    """).df()
    lat_pivot = time.time() - t0
    print(f"Executed in {lat_pivot:.3f}s.")
    print(df_pivot.to_string(index=False))
    results_summary.append({"Operation": "Pivot", "Target": "Dept x 7 Days of Week", "Rows": len(df_pivot), "Latency (s)": round(lat_pivot, 3)})

    # -------------------------------------------------------------------------
    # 6. CUBE (Multi-Dimensional Cross-Combination: Department x Part of Day)
    # -------------------------------------------------------------------------
    print("\n[6. CUBE OPERATION: Multi-Dimensional Power Set Aggregation (Dept x Part of Day)]")
    t0 = time.time()
    df_cube = con.execute("""
        SELECT 
            COALESCE(p.department, 'ALL DEPTS') AS department,
            COALESCE(t.part_of_day, 'ALL PARTS') AS part_of_day,
            COUNT(*) AS items_sold
        FROM fact_order_items f
        JOIN dim_product p USING (product_key)
        JOIN dim_time t USING (time_key)
        WHERE p.department IN ('produce', 'dairy eggs', 'beverages')
        GROUP BY CUBE (p.department, t.part_of_day)
        ORDER BY p.department NULLS LAST, t.part_of_day NULLS LAST;
    """).df()
    lat_cube = time.time() - t0
    print(f"Executed in {lat_cube:.3f}s. Generated {len(df_cube)} cube combinations.")
    print(df_cube.head(10).to_string(index=False))
    results_summary.append({"Operation": "Cube", "Target": "3 Depts x 4 Parts of Day Cube", "Rows": len(df_cube), "Latency (s)": round(lat_cube, 3)})

    # -------------------------------------------------------------------------
    # 7. GROUPING SETS (Selective Multi-Level Aggregation)
    # -------------------------------------------------------------------------
    print("\n[7. GROUPING SETS OPERATION: Selective Multi-Level Groupings]")
    t0 = time.time()
    df_gs = con.execute("""
        SELECT 
            COALESCE(p.department, 'ALL DEPTS') AS department,
            CASE 
                WHEN t.is_weekend IS NULL THEN 'ALL DAYS'
                WHEN t.is_weekend THEN 'Weekend'
                ELSE 'Weekday'
            END AS day_type,
            COUNT(*) AS items_sold,
            ROUND(AVG(f.reordered) * 100, 2) AS reorder_rate_pct
        FROM fact_order_items f
        JOIN dim_product p USING (product_key)
        JOIN dim_time t USING (time_key)
        WHERE p.department IN ('produce', 'dairy eggs')
        GROUP BY GROUPING SETS (
            (p.department, t.is_weekend),
            (p.department),
            (t.is_weekend),
            ()
        )
        ORDER BY p.department NULLS LAST, day_type NULLS LAST;
    """).df()
    lat_gs = time.time() - t0
    print(f"Executed in {lat_gs:.3f}s.")
    print(df_gs.to_string(index=False))
    results_summary.append({"Operation": "Grouping Sets", "Target": "(Dept, Wknd), (Dept), (Wknd), ()", "Rows": len(df_gs), "Latency (s)": round(lat_gs, 3)})

    # -------------------------------------------------------------------------
    # 8. PRE-AGGREGATED CUBE ACCELERATION COMPARISON
    # -------------------------------------------------------------------------
    print("\n[8. PRE-AGGREGATED CUBE SPEED COMPARISON]")
    # Full scan query
    t0 = time.time()
    con.execute("""
        SELECT p.department, COUNT(*) AS total_items
        FROM fact_order_items f JOIN dim_product p USING (product_key)
        GROUP BY p.department;
    """).fetchall()
    fact_time = time.time() - t0

    # Pre-aggregated cube query
    t0 = time.time()
    con.execute("""
        SELECT department, SUM(items) AS total_items
        FROM cube_dept_time
        GROUP BY department;
    """).fetchall()
    cube_time = time.time() - t0

    speedup = fact_time / cube_time if cube_time > 0 else 1.0
    print(f"Full Fact Scan (33.8M rows): {fact_time:.3f}s")
    print(f"Pre-aggregated Cube (22K rows): {cube_time:.4f}s")
    print(f"Acceleration Factor: {speedup:.1f}x faster using pre-aggregated cube!")
    results_summary.append({"Operation": "Pre-Agg Speedup", "Target": "cube_dept_time vs fact_order_items", "Rows": 21, "Latency (s)": round(cube_time, 4)})

    # Save summary table
    df_summary = pd.DataFrame(results_summary)
    df_summary.to_csv(os.path.join(REPORT_DIR, "olap_execution_benchmarks.csv"), index=False)
    print("\n" + "=" * 70)
    print("OLAP EXECUTION SUITE BENCHMARK SUMMARY")
    print("=" * 70)
    print(df_summary.to_string(index=False))

    return df_summary


def main():
    con = duckdb.connect(DB_PATH, read_only=True)
    try:
        execute_olap_suite(con)
    finally:
        con.close()


if __name__ == "__main__":
    main()
