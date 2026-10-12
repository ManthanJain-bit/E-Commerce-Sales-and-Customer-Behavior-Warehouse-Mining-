import os
import time
import duckdb
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "warehouse", "dwm.duckdb")


def run_validations(con: duckdb.DuckDBPyConnection):
    print("=" * 70)
    print("ETL STEP 04: Data Warehouse Referential Integrity & Validation Tests")
    print("=" * 70)

    checks = {
        "1. Items Count Matches Staging": (
            """SELECT (SELECT COUNT(*) FROM fact_order_items) - 
                      (SELECT COUNT(*) FROM stg_op o JOIN stg_orders s USING(order_id));""",
            0,
            "Total items in fact_order_items must exactly equal item records in valid orders"
        ),
        "2. Orphan Product Keys (FK check)": (
            """SELECT COUNT(*) 
               FROM fact_order_items f 
               LEFT JOIN dim_product p ON f.product_key = p.product_key 
               WHERE p.product_key IS NULL;""",
            0,
            "Every product_key in fact_order_items must exist in dim_product"
        ),
        "3. Orphan Time Keys in Items (FK check)": (
            """SELECT COUNT(*) 
               FROM fact_order_items f 
               LEFT JOIN dim_time t ON f.time_key = t.time_key 
               WHERE t.time_key IS NULL;""",
            0,
            "Every time_key in fact_order_items must exist in dim_time (0..167)"
        ),
        "4. Orphan Time Keys in Orders (FK check)": (
            """SELECT COUNT(*) 
               FROM fact_orders o 
               LEFT JOIN dim_time t ON o.time_key = t.time_key 
               WHERE t.time_key IS NULL;""",
            0,
            "Every time_key in fact_orders must exist in dim_time (0..167)"
        ),
        "5. Orphan Customer Keys in Items (FK check)": (
            """SELECT COUNT(*) 
               FROM fact_order_items f 
               LEFT JOIN dim_customer c ON f.customer_key = c.customer_key 
               WHERE c.customer_key IS NULL;""",
            0,
            "Every customer_key in fact_order_items must exist in dim_customer"
        ),
        "6. Orphan Customer Keys in Orders (FK check)": (
            """SELECT COUNT(*) 
               FROM fact_orders o 
               LEFT JOIN dim_customer c ON o.customer_key = c.customer_key 
               WHERE c.customer_key IS NULL;""",
            0,
            "Every customer_key in fact_orders must exist in dim_customer"
        ),
        "7. Basket Size Mismatch (Granularity Consistency)": (
            """SELECT COUNT(*) 
               FROM fact_orders o 
               JOIN (SELECT order_id, COUNT(*) AS n FROM fact_order_items GROUP BY 1) i 
               USING(order_id) 
               WHERE o.basket_size <> i.n;""",
            0,
            "Basket size in fact_orders must match the count of items in fact_order_items"
        ),
        "8. Total Item Aggregation Equality": (
            """SELECT (SELECT SUM(basket_size) FROM fact_orders) - 
                      (SELECT COUNT(*) FROM fact_order_items);""",
            0,
            "Sum of basket sizes across fact_orders must match total rows in fact_order_items"
        ),
        "9. Pre-Aggregate Cube Equality": (
            """SELECT (SELECT SUM(items) FROM cube_dept_time) - 
                      (SELECT COUNT(*) FROM fact_order_items);""",
            0,
            "Sum of items in cube_dept_time must equal row count of fact_order_items"
        ),
    }

    results = []
    all_passed = True

    for name, (sql, expected, description) in checks.items():
        t0 = time.time()
        val = con.execute(sql).fetchone()[0]
        elapsed = time.time() - t0
        status = "PASSED" if val == expected else "FAILED"
        if status == "FAILED":
            all_passed = False

        results.append({
            "Validation Check": name,
            "Actual Value": val,
            "Expected": expected,
            "Status": status,
            "Latency (s)": round(elapsed, 3),
        })
        print(f"[{status}] {name} => Result: {val} (Expected: {expected}) in {elapsed:.3f}s")

    df_res = pd.DataFrame(results)
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    print(df_res.to_string(index=False))

    if all_passed:
        print("\n>>> ALL 9 INTEGRITY & REFERENTIAL CHECKS PASSED WITH ZERO DEFECTS! <<<")
    else:
        print("\n>>> WARNING: ONE OR MORE VALIDATION CHECKS FAILED! <<<")

    return df_res


def main():
    con = duckdb.connect(DB_PATH, read_only=True)
    try:
        run_validations(con)
    finally:
        con.close()


if __name__ == "__main__":
    main()
