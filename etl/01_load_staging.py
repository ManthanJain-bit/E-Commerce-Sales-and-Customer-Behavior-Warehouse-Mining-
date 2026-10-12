import os
import time
import duckdb
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_RAW = os.path.join(BASE_DIR, "data", "raw")
DATA_WH = os.path.join(BASE_DIR, "data", "warehouse")
DB_PATH = os.path.join(DATA_WH, "dwm.duckdb")

os.makedirs(DATA_WH, exist_ok=True)


def load_staging_tables(con: duckdb.DuckDBPyConnection):
    print("=" * 60)
    print("STAGE 1: Loading Raw CSVs into DuckDB Staging Tables")
    print("=" * 60)

    tables = {
        "stg_aisles": "aisles.csv",
        "stg_departments": "departments.csv",
        "stg_products": "products.csv",
        "stg_orders": "orders.csv",
        "stg_op_prior": "order_products__prior.csv",
        "stg_op_train": "order_products__train.csv",
    }

    profiling_stats = []

    for tbl_name, csv_file in tables.items():
        csv_path = os.path.join(DATA_RAW, csv_file).replace("\\", "/")
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Missing required raw file: {csv_path}")

        print(f"Loading '{tbl_name}' from {csv_file}...")
        t0 = time.time()
        con.execute(f"CREATE OR REPLACE TABLE {tbl_name} AS SELECT * FROM read_csv_auto('{csv_path}');")
        elapsed = time.time() - t0

        row_count = con.execute(f"SELECT COUNT(*) FROM {tbl_name}").fetchone()[0]
        col_count = len(con.execute(f"DESCRIBE {tbl_name}").fetchall())
        file_size_mb = os.path.getsize(csv_path) / (1024 * 1024)

        profiling_stats.append({
            "Table": tbl_name,
            "Source File": csv_file,
            "File Size (MB)": round(file_size_mb, 2),
            "Rows": row_count,
            "Columns": col_count,
            "Load Time (s)": round(elapsed, 2),
        })
        print(f" -> Loaded {row_count:,} rows ({col_count} columns) in {elapsed:.2f}s")

    return pd.DataFrame(profiling_stats)


def profile_data(con: duckdb.DuckDBPyConnection):
    print("\n" + "=" * 60)
    print("STAGE 2: Profiling Staging Tables (Data Quality & Metrics)")
    print("=" * 60)

    # 1. Orders & Users
    orders_info = con.execute("""
        SELECT COUNT(*) AS total_orders, COUNT(DISTINCT user_id) AS total_users
        FROM stg_orders;
    """).df().iloc[0]
    print(f"Total Orders: {int(orders_info['total_orders']):,}")
    print(f"Total Users:  {int(orders_info['total_users']):,}")

    # 2. Evaluation Set Breakdown
    print("\n[Orders by Evaluation Set (eval_set)]")
    eval_df = con.execute("""
        SELECT eval_set, COUNT(*) AS count,
               ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM stg_orders), 2) AS percentage
        FROM stg_orders
        GROUP BY eval_set
        ORDER BY count DESC;
    """).df()
    print(eval_df.to_string(index=False))

    # 3. Null Checks (Days Since Prior Order)
    null_gap = con.execute("""
        SELECT 
            COUNT(*) FILTER (WHERE days_since_prior_order IS NULL) AS null_gap_orders,
            COUNT(DISTINCT user_id) AS total_users
        FROM stg_orders;
    """).df().iloc[0]
    print(f"\nOrders with NULL days_since_prior_order (first order per user): {int(null_gap['null_gap_orders']):,} (Matches total users: {null_gap['null_gap_orders'] == null_gap['total_users']})")

    # 4. Duplicate checks
    dups_prior = con.execute("""
        SELECT COUNT(*) - COUNT(DISTINCT (order_id, product_id)) AS duplicate_pairs
        FROM stg_op_prior;
    """).fetchone()[0]
    print(f"Duplicate (order_id, product_id) in stg_op_prior: {dups_prior}")

    # 5. Basket Size Summary
    basket_stats = con.execute("""
        WITH basket_sizes AS (
            SELECT order_id, COUNT(*) AS basket_size
            FROM stg_op_prior
            GROUP BY order_id
        )
        SELECT 
            MIN(basket_size) AS min_basket,
            ROUND(AVG(basket_size), 2) AS avg_basket,
            MEDIAN(basket_size) AS median_basket,
            MAX(basket_size) AS max_basket
        FROM basket_sizes;
    """).df().iloc[0]
    print(f"\nBasket Size (stg_op_prior): Min={basket_stats['min_basket']}, Avg={basket_stats['avg_basket']}, Median={basket_stats['median_basket']}, Max={basket_stats['max_basket']}")

    # 6. Reorder Rate
    reorder_rate = con.execute("""
        SELECT ROUND(AVG(reordered) * 100.0, 2) AS overall_reorder_pct
        FROM stg_op_prior;
    """).fetchone()[0]
    print(f"Overall Reorder Rate (stg_op_prior): {reorder_rate}%")

    return {
        "orders_info": orders_info.to_dict(),
        "eval_df": eval_df,
        "null_gap": int(null_gap['null_gap_orders']),
        "dups_prior": dups_prior,
        "basket_stats": basket_stats.to_dict(),
        "reorder_rate": reorder_rate,
    }


def main():
    con = duckdb.connect(DB_PATH)
    try:
        staging_stats_df = load_staging_tables(con)
        print("\n" + "=" * 60)
        print("SUMMARY: Staging Tables Profile")
        print("=" * 60)
        print(staging_stats_df.to_string(index=False))

        profile_results = profile_data(con)
        print("\nDuckDB staging tables loaded and data profiling completed successfully!")
    finally:
        con.close()


if __name__ == "__main__":
    main()
