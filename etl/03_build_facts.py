import os
import time
import duckdb

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "warehouse", "dwm.duckdb")


def build_facts(con: duckdb.DuckDBPyConnection):
    print("=" * 60)
    print("ETL STEP 03: Building Fact Tables & Customer Dimension")
    print("=" * 60)

    # 1. Create unified order items view (prior + train)
    print("Creating unified view 'stg_op'...")
    con.execute("""
        CREATE OR REPLACE VIEW stg_op AS
        SELECT * FROM stg_op_prior
        UNION ALL
        SELECT * FROM stg_op_train;
    """)

    # 2. Build fact_order_items
    print("Building 'fact_order_items' (Fine Grain: item level)...")
    t0 = time.time()
    con.execute("""
        CREATE OR REPLACE TABLE fact_order_items AS
        SELECT 
            op.order_id,
            op.product_id AS product_key,
            o.user_id     AS customer_key,
            CAST(o.order_dow AS INTEGER) * 24 + CAST(o.order_hour_of_day AS INTEGER) AS time_key,
            op.add_to_cart_order,
            op.reordered
        FROM stg_op op
        JOIN stg_orders o USING (order_id);
    """)
    foi_time = time.time() - t0
    foi_count = con.execute("SELECT COUNT(*) FROM fact_order_items;").fetchone()[0]
    print(f" -> 'fact_order_items' built: {foi_count:,} rows in {foi_time:.2f}s")

    # 3. Build fact_orders
    print("Building 'fact_orders' (Coarse Grain: order level)...")
    t0 = time.time()
    con.execute("""
        CREATE OR REPLACE TABLE fact_orders AS
        SELECT 
            o.order_id,
            o.user_id AS customer_key,
            CAST(o.order_dow AS INTEGER) * 24 + CAST(o.order_hour_of_day AS INTEGER) AS time_key,
            o.order_number,
            o.days_since_prior_order,
            COUNT(op.product_id) AS basket_size,
            AVG(op.reordered)    AS reorder_ratio
        FROM stg_orders o
        JOIN stg_op op USING (order_id)
        GROUP BY 
            o.order_id, 
            o.user_id, 
            o.order_dow, 
            o.order_hour_of_day,
            o.order_number, 
            o.days_since_prior_order;
    """)
    fo_time = time.time() - t0
    fo_count = con.execute("SELECT COUNT(*) FROM fact_orders;").fetchone()[0]
    print(f" -> 'fact_orders' built: {fo_count:,} rows in {fo_time:.2f}s")

    # 4. Build dim_customer
    print("Building 'dim_customer' (Customer profile & aggregates)...")
    t0 = time.time()
    con.execute("""
        CREATE OR REPLACE TABLE dim_customer AS
        SELECT 
            customer_key,
            COUNT(*)                    AS total_orders,
            SUM(basket_size)            AS total_items,
            ROUND(AVG(basket_size), 2)  AS avg_basket_size,
            ROUND(AVG(days_since_prior_order), 2) AS avg_days_between_orders,
            CAST(NULL AS VARCHAR)       AS rfm_segment
        FROM fact_orders
        GROUP BY customer_key;
    """)
    dc_time = time.time() - t0
    dc_count = con.execute("SELECT COUNT(*) FROM dim_customer;").fetchone()[0]
    print(f" -> 'dim_customer' built: {dc_count:,} rows in {dc_time:.2f}s")

    # 5. Build pre-aggregated summary table cube_dept_time
    print("Building 'cube_dept_time' (Pre-aggregated rollups)...")
    t0 = time.time()
    con.execute("""
        CREATE OR REPLACE TABLE cube_dept_time AS
        SELECT 
            p.department, 
            p.aisle, 
            t.order_dow, 
            t.hour,
            COUNT(*)            AS items, 
            SUM(f.reordered)    AS reordered_items
        FROM fact_order_items f
        JOIN dim_product p USING (product_key)
        JOIN dim_time t USING (time_key)
        GROUP BY p.department, p.aisle, t.order_dow, t.hour;
    """)
    cube_time = time.time() - t0
    cube_count = con.execute("SELECT COUNT(*) FROM cube_dept_time;").fetchone()[0]
    print(f" -> 'cube_dept_time' built: {cube_count:,} rows in {cube_time:.2f}s")

    print("\nSample from fact_order_items:")
    print(con.execute("SELECT * FROM fact_order_items LIMIT 3;").df().to_string(index=False))

    print("\nSample from fact_orders:")
    print(con.execute("SELECT * FROM fact_orders LIMIT 3;").df().to_string(index=False))

    print("\nSample from dim_customer:")
    print(con.execute("SELECT * FROM dim_customer LIMIT 3;").df().to_string(index=False))


def main():
    con = duckdb.connect(DB_PATH)
    try:
        build_facts(con)
    finally:
        con.close()


if __name__ == "__main__":
    main()
