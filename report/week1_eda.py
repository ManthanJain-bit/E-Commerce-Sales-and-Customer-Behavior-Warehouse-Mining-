import os
import duckdb
import pandas as pd
import plotly.express as px

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "warehouse", "dwm.duckdb")
REPORT_DIR = os.path.join(BASE_DIR, "report")
os.makedirs(REPORT_DIR, exist_ok=True)


def generate_eda_charts():
    con = duckdb.connect(DB_PATH, read_only=True)
    try:
        # Chart 1: Orders by Hour of Day
        print("Generating Chart 1: Orders by Hour of Day...")
        df_hour = con.execute("""
            SELECT order_hour_of_day, COUNT(*) AS order_count
            FROM stg_orders
            GROUP BY order_hour_of_day
            ORDER BY order_hour_of_day;
        """).df()
        fig1 = px.bar(
            df_hour,
            x="order_hour_of_day",
            y="order_count",
            title="Distribution of Orders by Hour of Day (Peak Demand)",
            labels={"order_hour_of_day": "Hour of Day (0-23)", "order_count": "Total Orders"},
            template="plotly_white",
            color="order_count",
            color_continuous_scale="Viridis",
        )
        fig1.write_html(os.path.join(REPORT_DIR, "eda_orders_by_hour.html"))

        # Chart 2: Orders by Day of Week
        print("Generating Chart 2: Orders by Day of Week...")
        df_dow = con.execute("""
            SELECT order_dow, COUNT(*) AS order_count
            FROM stg_orders
            GROUP BY order_dow
            ORDER BY order_dow;
        """).df()
        # Days 0 and 1 are typically weekend days (highest volume)
        fig2 = px.bar(
            df_dow,
            x="order_dow",
            y="order_count",
            title="Distribution of Orders by Day of Week (0 & 1 Peak Days)",
            labels={"order_dow": "Day of Week (0-6)", "order_count": "Total Orders"},
            template="plotly_white",
            color="order_count",
            color_continuous_scale="Teal",
        )
        fig2.write_html(os.path.join(REPORT_DIR, "eda_orders_by_dow.html"))

        # Chart 3: Basket Size Distribution
        print("Generating Chart 3: Basket Size Distribution...")
        df_basket = con.execute("""
            WITH b AS (
                SELECT order_id, COUNT(*) AS basket_size
                FROM stg_op_prior
                GROUP BY order_id
            )
            SELECT basket_size, COUNT(*) AS order_count
            FROM b
            WHERE basket_size <= 50
            GROUP BY basket_size
            ORDER BY basket_size;
        """).df()
        fig3 = px.line(
            df_basket,
            x="basket_size",
            y="order_count",
            title="Basket Size Distribution (Items per Order, up to 50 items)",
            labels={"basket_size": "Number of Items in Basket", "order_count": "Number of Orders"},
            template="plotly_white",
            markers=True,
        )
        fig3.write_html(os.path.join(REPORT_DIR, "eda_basket_size_distribution.html"))

        # Chart 4: Reorder Rate by Department
        print("Generating Chart 4: Reorder Rate by Department...")
        df_reorder_dept = con.execute("""
            SELECT d.department, COUNT(*) AS total_items, ROUND(AVG(op.reordered) * 100, 2) AS reorder_rate_pct
            FROM stg_op_prior op
            JOIN stg_products p USING (product_id)
            JOIN stg_departments d USING (department_id)
            GROUP BY d.department
            ORDER BY reorder_rate_pct DESC;
        """).df()
        fig4 = px.bar(
            df_reorder_dept,
            x="reorder_rate_pct",
            y="department",
            orientation="h",
            title="Reorder Rate (%) Across Product Departments",
            labels={"reorder_rate_pct": "Reorder Rate (%)", "department": "Department"},
            template="plotly_white",
            color="reorder_rate_pct",
            color_continuous_scale="Blues",
        ).update_yaxes(autorange="reversed")
        fig4.write_html(os.path.join(REPORT_DIR, "eda_reorder_by_department.html"))

        print("All EDA charts generated successfully in report/ directory.")
    finally:
        con.close()


if __name__ == "__main__":
    generate_eda_charts()
