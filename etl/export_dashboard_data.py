import os
import json
import duckdb
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "warehouse", "dwm.duckdb")

con = duckdb.connect(DB_PATH, read_only=True)

# 1. KPIs
kpis = {
    'total_orders': 3346083,
    'total_customers': 206209,
    'total_items': 33819106,
    'avg_basket_size': 10.11,
    'reorder_rate': 58.97
}

# 2. Heatmap: 7 days x 24 hours
hm_df = con.execute("""
    SELECT order_dow, hour, sum(items) as total_items
    FROM cube_dept_time
    GROUP BY order_dow, hour
    ORDER BY order_dow, hour
""").df()
heatmap_data = hm_df.to_dict(orient='records')

# 3. Top Products
top_prod_df = con.execute("""
    SELECT p.product_name, count(*) as orders, round(avg(f.reordered)*100, 1) as reorder_pct, p.department, p.aisle
    FROM fact_order_items f
    JOIN dim_product p ON f.product_key = p.product_key
    GROUP BY p.product_name, p.department, p.aisle
    ORDER BY orders DESC
    LIMIT 20
""").df()
top_products = top_prod_df.to_dict(orient='records')

# 4. Department Share
dept_df = con.execute("""
    SELECT department, sum(items) as total_items, round(avg(reordered_items::FLOAT / items::FLOAT)*100, 1) as reorder_pct
    FROM cube_dept_time
    GROUP BY department
    ORDER BY total_items DESC
""").df()
departments = dept_df.to_dict(orient='records')

# 5. Customer Loyalty Curve
loy_df = con.execute("""
    SELECT order_number, round(avg(basket_size), 2) as avg_basket, count(*) as count
    FROM fact_orders
    WHERE order_number <= 50
    GROUP BY order_number
    ORDER BY order_number
""").df()
loyalty_curve = loy_df.to_dict(orient='records')

# 6. RFM Segments
rfm_df = con.execute("""
    SELECT rfm_segment, count(*) as shoppers, 
           round(avg(total_orders), 1) as avg_orders, 
           round(avg(avg_days_between_orders), 1) as avg_days,
           round(avg(total_items), 1) as avg_items
    FROM dim_customer
    GROUP BY rfm_segment
    ORDER BY shoppers DESC
""").df()
rfm_segments = rfm_df.to_dict(orient='records')

# 7. Association Rules
rules_df = con.execute("SELECT * FROM fact_rules ORDER BY lift DESC").df()
rules = rules_df.to_dict(orient='records')

# 8. Department x Daypart Pivot
piv_df = con.execute("""
    SELECT c.department, t.part_of_day, sum(c.items) as total_items
    FROM cube_dept_time c
    JOIN dim_time t ON c.order_dow = t.order_dow AND c.hour = t.hour
    GROUP BY c.department, t.part_of_day
""").df()
pivot_data = piv_df.to_dict(orient='records')

# 9. Top Aisles
aisle_df = con.execute("""
    SELECT department, aisle, sum(items) as total_items
    FROM cube_dept_time
    GROUP BY department, aisle
    ORDER BY total_items DESC
    LIMIT 40
""").df()
aisles = aisle_df.to_dict(orient='records')

# 10. Sample Rows per table
tables = ['fact_order_items', 'fact_orders', 'dim_product', 'dim_customer', 'dim_time', 'cube_dept_time', 'fact_rules']
samples = {}
for t in tables:
    samples[t] = con.execute(f"SELECT * FROM {t} LIMIT 4").df().to_dict(orient='records')

# 11. Top products per aisle for smart recommender fallback
fallback_recs = con.execute("""
    SELECT p.aisle, p.product_name, count(*) as orders, p.department
    FROM fact_order_items f
    JOIN dim_product p ON f.product_key = p.product_key
    GROUP BY p.aisle, p.product_name, p.department
    QUALIFY row_number() OVER (PARTITION BY p.aisle ORDER BY orders DESC) <= 3
""").df().to_dict(orient='records')

# 12. Benchmark results
benchmarks = {
    'q_latencies': [
        {'architecture': 'C4: Pre-Agg Cube', 'latency': 0.005, 'note': '87× Faster', 'color': '#22A06B'},
        {'architecture': 'C2: Galaxy Schema', 'latency': 0.183, 'note': '2× Faster than 3NF', 'color': '#6C63D9'},
        {'architecture': 'C3: Columnar Parquet', 'latency': 0.173, 'note': 'Zero-Copy Scan', 'color': '#8B85E5'},
        {'architecture': 'C1: Normalized (3NF)', 'latency': 0.401, 'note': 'Multi-Table Join', 'color': '#FF6B4A'}
    ],
    'scalability': [
        {'scale': '10% (3.4M rows)', 'normalized': 0.165, 'galaxy': 0.073},
        {'scale': '50% (16.9M rows)', 'normalized': 0.268, 'galaxy': 0.139},
        {'scale': '100% (33.8M rows)', 'normalized': 0.401, 'galaxy': 0.208}
    ],
    'mining': [
        {'support': '5.0%', 'apriori': 0.041, 'fpgrowth': 0.403},
        {'support': '3.0%', 'apriori': 0.161, 'fpgrowth': 0.452},
        {'support': '2.0%', 'apriori': 0.702, 'fpgrowth': 1.075},
        {'support': '1.0%', 'apriori': 5.810, 'fpgrowth': 1.111}
    ]
}

export_bundle = {
    'kpis': kpis,
    'heatmap': heatmap_data,
    'top_products': top_products,
    'departments': departments,
    'loyalty_curve': loyalty_curve,
    'rfm_segments': rfm_segments,
    'rules': rules,
    'pivot': pivot_data,
    'aisles': aisles,
    'samples': samples,
    'fallback_recs': fallback_recs,
    'benchmarks': benchmarks
}

output_path = os.path.join(BASE_DIR, "dashboard", "data.js")
with open(output_path, "w", encoding="utf-8") as f:
    f.write("const DWM_DATA = " + json.dumps(export_bundle, indent=2) + ";\n")

print(f"Successfully generated {output_path} ({os.path.getsize(output_path)/1024:.1f} KB)")
