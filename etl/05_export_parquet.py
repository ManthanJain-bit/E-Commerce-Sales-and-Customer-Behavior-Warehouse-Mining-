import os
import time
import duckdb

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "warehouse", "dwm.duckdb")
WH_DIR = os.path.join(BASE_DIR, "data", "warehouse")


def export_parquet(con: duckdb.DuckDBPyConnection):
    print("=" * 60)
    print("ETL STEP 05: Exporting Warehouse Tables to Parquet")
    print("=" * 60)

    tables = [
        "dim_product",
        "dim_time",
        "dim_customer",
        "fact_orders",
        "fact_order_items",
        "cube_dept_time",
    ]

    for tbl in tables:
        parquet_path = os.path.join(WH_DIR, f"{tbl}.parquet").replace("\\", "/")
        print(f"Exporting '{tbl}' -> '{tbl}.parquet'...")
        t0 = time.time()
        con.execute(f"COPY {tbl} TO '{parquet_path}' (FORMAT PARQUET, COMPRESSION ZSTD);")
        elapsed = time.time() - t0
        file_size_mb = os.path.getsize(parquet_path) / (1024 * 1024)
        print(f" -> Exported {tbl}.parquet ({file_size_mb:.2f} MB) in {elapsed:.2f}s")

    print("\nParquet export completed successfully for all tables!")


def main():
    con = duckdb.connect(DB_PATH, read_only=True)
    try:
        export_parquet(con)
    finally:
        con.close()


if __name__ == "__main__":
    main()
