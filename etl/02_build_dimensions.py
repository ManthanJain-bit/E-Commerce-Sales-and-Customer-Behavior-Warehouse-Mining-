import os
import time
import duckdb

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "warehouse", "dwm.duckdb")


def build_dimensions(con: duckdb.DuckDBPyConnection):
    print("=" * 60)
    print("ETL STEP 02: Building Dimension Tables")
    print("=" * 60)

    # 1. Build dim_product
    print("Building 'dim_product'...")
    t0 = time.time()
    con.execute("""
        CREATE OR REPLACE TABLE dim_product AS
        SELECT 
            p.product_id AS product_key,
            p.product_name,
            a.aisle_id,
            a.aisle,
            d.department_id,
            d.department
        FROM stg_products p
        JOIN stg_aisles a USING (aisle_id)
        JOIN stg_departments d USING (department_id);
    """)
    p_time = time.time() - t0
    p_count = con.execute("SELECT COUNT(*) FROM dim_product;").fetchone()[0]
    print(f" -> 'dim_product' built: {p_count:,} rows in {p_time:.2f}s")

    # 2. Build dim_time (7 days x 24 hours = 168 rows)
    print("Building 'dim_time'...")
    t0 = time.time()
    con.execute("""
        CREATE OR REPLACE TABLE dim_time AS
        SELECT 
            d.dow * 24 + h.hr AS time_key,
            d.dow AS order_dow,
            h.hr  AS hour,
            'Day ' || d.dow AS day_label,
            d.dow IN (0, 1) AS is_weekend,
            CASE 
                WHEN h.hr BETWEEN 5  AND 11 THEN 'Morning'
                WHEN h.hr BETWEEN 12 AND 16 THEN 'Afternoon'
                WHEN h.hr BETWEEN 17 AND 21 THEN 'Evening'
                ELSE 'Night' 
            END AS part_of_day
        FROM range(0, 7) AS d(dow), range(0, 24) AS h(hr);
    """)
    t_time = time.time() - t0
    t_count = con.execute("SELECT COUNT(*) FROM dim_time;").fetchone()[0]
    print(f" -> 'dim_time' built: {t_count} rows in {t_time:.2f}s")

    print("\nSample records from dim_product:")
    print(con.execute("SELECT * FROM dim_product LIMIT 3;").df().to_string(index=False))

    print("\nSample records from dim_time:")
    print(con.execute("SELECT * FROM dim_time LIMIT 5;").df().to_string(index=False))


def main():
    con = duckdb.connect(DB_PATH)
    try:
        build_dimensions(con)
    finally:
        con.close()


if __name__ == "__main__":
    main()
