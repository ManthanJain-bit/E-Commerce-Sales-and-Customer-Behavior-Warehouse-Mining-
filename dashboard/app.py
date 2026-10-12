import os
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# -----------------------------------------------------------------------------
# Configuration & Theming
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Retail DWM Analytics & Mining Warehouse",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "warehouse", "dwm.duckdb").replace("\\", "/")


@st.cache_resource
def get_db_connection():
    return duckdb.connect(DB_PATH, read_only=True)


@st.cache_data
def run_query(sql_query: str) -> pd.DataFrame:
    con = get_db_connection()
    return con.execute(sql_query).df()


# Custom CSS for styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 5px solid #1f77b4;
    }
    .stMetric label {
        font-size: 0.9rem !important;
        font-weight: 600 !important;
        color: #555 !important;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Sidebar Navigation
# -----------------------------------------------------------------------------
st.sidebar.title("🛒 Retail DWM Portal")
st.sidebar.caption("Data Warehouse & Mining Analytical Platform")

page = st.sidebar.radio(
    "Select Analytical Module:",
    [
        "📊 Executive Overview",
        "🧊 OLAP Multidimensional Explorer",
        "👥 Customer Intelligence (RFM)",
        "🔍 Association Rules & Mining",
        "⚡ Architectural Performance (RQ1-3)"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Warehouse Metadata:**")
st.sidebar.info("""
* **Total Transactions:** 3.35M Orders
* **Item Rows:** 33.8M Items
* **Engine:** DuckDB + Parquet
* **Schema:** Galaxy (Constellation)
""")

# =============================================================================
# 1. EXECUTIVE OVERVIEW PAGE
# =============================================================================
if page == "📊 Executive Overview":
    st.title("📊 Executive Sales & Operations Overview")
    st.markdown("High-level Key Performance Indicators (KPIs) and macro retail demand distributions.")

    # KPI Metrics Row
    kpis = run_query("""
        SELECT 
            COUNT(*) AS total_orders,
            COUNT(DISTINCT customer_key) AS total_customers,
            ROUND(AVG(basket_size), 2) AS avg_basket_size,
            ROUND(AVG(reorder_ratio) * 100, 2) AS avg_reorder_pct,
            SUM(basket_size) AS total_items
        FROM fact_orders;
    """).iloc[0]

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Orders", f"{int(kpis.total_orders):,}")
    col2.metric("Unique Customers", f"{int(kpis.total_customers):,}")
    col3.metric("Total Items Sold", f"{int(kpis.total_items):,}")
    col4.metric("Avg Basket Size", f"{kpis.avg_basket_size} items")
    col5.metric("Avg Reorder Rate", f"{kpis.avg_reorder_pct}%")

    st.markdown("---")

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("🏆 Top 15 Products by Volume")
        top_products = run_query("""
            SELECT p.product_name, COUNT(*) AS items_sold, ROUND(AVG(f.reordered) * 100, 1) AS reorder_rate
            FROM fact_order_items f
            JOIN dim_product p USING (product_key)
            GROUP BY p.product_name
            ORDER BY items_sold DESC
            LIMIT 15;
        """)
        fig_top = px.bar(
            top_products,
            x="items_sold",
            y="product_name",
            orientation="h",
            color="reorder_rate",
            color_continuous_scale="Viridis",
            labels={"items_sold": "Total Units Sold", "product_name": "Product", "reorder_rate": "Reorder %"},
            title="Top 15 Selling Products (Colored by Reorder Rate %)",
            template="plotly_white"
        ).update_yaxes(autorange="reversed")
        st.plotly_chart(fig_top, use_container_width=True)

    with col_right:
        st.subheader("🔥 Reorder Intensity Heatmap (Day × Hour)")
        heat_data = run_query("""
            SELECT 
                t.order_dow, 
                t.hour, 
                ROUND(AVG(f.reordered) * 100, 2) AS reorder_rate
            FROM fact_order_items f
            JOIN dim_time t USING (time_key)
            GROUP BY t.order_dow, t.hour
            ORDER BY t.order_dow, t.hour;
        """)
        fig_heat = px.density_heatmap(
            heat_data,
            x="hour",
            y="order_dow",
            z="reorder_rate",
            histfunc="avg",
            title="Customer Reorder Rate (%) Across Day-of-Week and Hour",
            labels={"hour": "Hour of Day (0-23)", "order_dow": "Day of Week (0=Wknd)", "reorder_rate": "Reorder %"},
            color_continuous_scale="RdYlBu_r",
            template="plotly_white"
        )
        st.plotly_chart(fig_heat, use_container_width=True)

    # Customer Maturity Trend
    st.subheader("📈 Basket Size vs Customer Maturity (Order Number)")
    trend_df = run_query("""
        SELECT order_number, ROUND(AVG(basket_size), 2) AS avg_basket_size
        FROM fact_orders
        WHERE order_number <= 60
        GROUP BY order_number
        ORDER BY order_number;
    """)
    fig_trend = px.line(
        trend_df,
        x="order_number",
        y="avg_basket_size",
        markers=True,
        title="Basket Size Dynamics Over Customer Lifetime (Order Sequence 1 to 60)",
        labels={"order_number": "Customer Order Sequence (n-th Order)", "avg_basket_size": "Average Basket Size (Units)"},
        template="plotly_white"
    )
    st.plotly_chart(fig_trend, use_container_width=True)


# =============================================================================
# 2. OLAP MULTIDIMENSIONAL EXPLORER
# =============================================================================
elif page == "🧊 OLAP Multidimensional Explorer":
    st.title("🧊 OLAP Multidimensional Explorer")
    st.markdown("Interactive slice, dice, roll-up, and drill-down across products, departments, and time dimensions.")

    # Control Panel
    st.sidebar.subheader("Multidimensional Filters")

    all_depts = run_query("SELECT DISTINCT department FROM dim_product ORDER BY 1;")["department"].tolist()
    sel_depts = st.sidebar.multiselect("Select Departments (Dice):", all_depts, default=["produce", "dairy eggs", "snacks"])

    parts_of_day = ["Morning", "Afternoon", "Evening", "Night"]
    sel_parts = st.sidebar.multiselect("Part of Day (Dice):", parts_of_day, default=parts_of_day)

    weekend_filter = st.sidebar.selectbox("Weekend Filter (Slice):", ["All Days", "Weekends Only", "Weekdays Only"])

    drill_level = st.sidebar.radio("Aggregation Hierarchy Level (Drill-Down / Roll-Up):", ["department", "aisle", "product_name"])

    if not sel_depts or not sel_parts:
        st.warning("Please select at least one department and one part of day from the sidebar.")
        st.stop()

    # Dynamic SQL query generation
    dept_sql_str = ", ".join(f"'{d}'" for d in sel_depts)
    part_sql_str = ", ".join(f"'{p}'" for p in sel_parts)
    wk_sql = {
        "All Days": "TRUE",
        "Weekends Only": "t.is_weekend = TRUE",
        "Weekdays Only": "t.is_weekend = FALSE"
    }[weekend_filter]

    olap_sql = f"""
        SELECT 
            p.{drill_level} AS dimensional_group,
            COUNT(*) AS total_items,
            ROUND(AVG(f.reordered) * 100, 2) AS reorder_rate_pct
        FROM fact_order_items f
        JOIN dim_product p USING (product_key)
        JOIN dim_time t USING (time_key)
        WHERE p.department IN ({dept_sql_str})
          AND t.part_of_day IN ({part_sql_str})
          AND {wk_sql}
        GROUP BY p.{drill_level}
        ORDER BY total_items DESC
        LIMIT 35;
    """

    df_olap = run_query(olap_sql)

    col1, col2 = st.columns([3, 2])
    with col1:
        fig_olap = px.bar(
            df_olap,
            x="dimensional_group",
            y="total_items",
            color="reorder_rate_pct",
            color_continuous_scale="Teal",
            title=f"OLAP View: Aggregated Items by {drill_level.capitalize()}",
            labels={"dimensional_group": drill_level.capitalize(), "total_items": "Items Sold", "reorder_rate_pct": "Reorder %"},
            template="plotly_white"
        )
        st.plotly_chart(fig_olap, use_container_width=True)

    with col2:
        st.subheader("Aggregated Data Table")
        st.dataframe(df_olap, use_container_width=True)

    # Cross-tabulation Pivot View
    st.subheader("📊 Cross-Tabulation Pivot Matrix (Department × Part of Day)")
    pivot_df = run_query(f"""
        SELECT 
            p.department,
            SUM(CASE WHEN t.part_of_day = 'Morning' THEN 1 ELSE 0 END) AS Morning,
            SUM(CASE WHEN t.part_of_day = 'Afternoon' THEN 1 ELSE 0 END) AS Afternoon,
            SUM(CASE WHEN t.part_of_day = 'Evening' THEN 1 ELSE 0 END) AS Evening,
            SUM(CASE WHEN t.part_of_day = 'Night' THEN 1 ELSE 0 END) AS Night,
            COUNT(*) AS Total
        FROM fact_order_items f
        JOIN dim_product p USING (product_key)
        JOIN dim_time t USING (time_key)
        WHERE p.department IN ({dept_sql_str})
        GROUP BY p.department
        ORDER BY Total DESC;
    """)
    st.dataframe(pivot_df, use_container_width=True)


# =============================================================================
# 3. CUSTOMER INTELLIGENCE (RFM SEGMENTATION)
# =============================================================================
elif page == "👥 Customer Intelligence (RFM)":
    st.title("👥 Customer Segmentation (Adapted RFM & K-Means)")
    st.markdown("Machine learning clustering classifying 206,209 customers into actionable retail personas.")

    seg_summary = run_query("""
        SELECT 
            rfm_segment,
            COUNT(*) AS customer_count,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM dim_customer WHERE rfm_segment IS NOT NULL), 2) AS percentage,
            ROUND(AVG(avg_days_between_orders), 1) AS avg_recency_gap_days,
            ROUND(AVG(total_orders), 1) AS avg_frequency_orders,
            ROUND(AVG(total_items), 1) AS avg_monetary_items
        FROM dim_customer
        WHERE rfm_segment IS NOT NULL
        GROUP BY rfm_segment
        ORDER BY customer_count DESC;
    """)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Customer Segment Distribution")
        fig_pie = px.pie(
            seg_summary,
            names="rfm_segment",
            values="customer_count",
            hole=0.4,
            title="Distribution of Customer Personas (206,209 Customers)",
            template="plotly_white",
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        st.subheader("Segment Behavioral Attributes")
        fig_bar = px.bar(
            seg_summary,
            x="rfm_segment",
            y="avg_frequency_orders",
            color="avg_recency_gap_days",
            color_continuous_scale="Viridis_r",
            title="Average Orders per Persona (Colored by Order Gap Days)",
            labels={"rfm_segment": "Segment", "avg_frequency_orders": "Avg Orders", "avg_recency_gap_days": "Avg Gap (Days)"},
            template="plotly_white"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("📋 Segment Performance Profiles & Strategies")
    st.dataframe(seg_summary, use_container_width=True)

    # Strategy Guide Cards
    st.markdown("""
    | Persona | Profile Characteristics | Targeted Retail Strategy |
    |---|---|---|
    | **Loyal Power Shoppers** | Extreme frequency (~69 orders), very low gap (~5.4 days), high item volume | Priority grocery delivery passes, VIP concierge perks, subscription retention |
    | **High-Volume Regulars** | Steady cadence (~35 orders), ~9 day gap, high basket volume | Multi-pack promotions, cross-department bundle incentives |
    | **Casual Occasionals** | Bi-weekly cadence (~12 orders), ~12 day gap, moderate items | Re-engagement push alerts, basket-builder coupons |
    | **Infrequent / At-Risk** | Sparse orders (~7 orders), long purchase gap (~23 days) | Win-back discounts, personalized re-ordering reminders |
    """)


# =============================================================================
# 4. ASSOCIATION RULES & MINING EXPLORER
# =============================================================================
elif page == "🔍 Association Rules & Mining":
    st.title("🔍 Association Rules & Contextual Slice Mining")
    st.markdown("Discovering market basket product associations across global baseline and contextual OLAP slices.")

    rules_df = run_query("SELECT * FROM fact_rules;")

    slices = sorted(rules_df["slice_name"].unique())
    sel_slice = st.sidebar.selectbox("Select Context Slice:", slices)
    min_lift = st.sidebar.slider("Minimum Lift Threshold:", 1.0, 5.0, 1.2, 0.1)
    min_conf = st.sidebar.slider("Minimum Confidence Threshold:", 0.2, 0.8, 0.25, 0.05)

    filtered_rules = rules_df[
        (rules_df["slice_name"] == sel_slice) &
        (rules_df["lift"] >= min_lift) &
        (rules_df["confidence"] >= min_conf)
    ].sort_values("lift", ascending=False)

    col1, col2, col3 = st.columns(3)
    col1.metric("Active Slice", sel_slice)
    col2.metric("Matching Rules", len(filtered_rules))
    if len(filtered_rules) > 0:
        col3.metric("Peak Rule Lift", f"{filtered_rules['lift'].max():.2f}")
    else:
        col3.metric("Peak Rule Lift", "N/A")

    st.markdown("---")

    if len(filtered_rules) > 0:
        fig_scatter = px.scatter(
            filtered_rules,
            x="support",
            y="confidence",
            size="lift",
            color="lift",
            hover_data=["antecedent", "consequent"],
            color_continuous_scale="Plasma",
            title=f"Association Rules Scatter Plot: {sel_slice} (Support vs. Confidence, Sized by Lift)",
            template="plotly_white"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

        st.subheader("Discovered Association Rules Table")
        st.dataframe(filtered_rules, use_container_width=True)
    else:
        st.info("No rules match the current threshold filters. Please lower the lift or confidence slider.")

    # Contextual comparison banner
    if sel_slice == "Weekend_Morning":
        st.success("💡 **Contextual Discovery (RQ3):** On Weekend Mornings, `Organic Cilantro ==> Limes` achieves a peak **Lift of 4.83**, reflecting fresh weekend culinary and salsa preparation that is diluted and missed in global baseline mining!")


# =============================================================================
# 5. ARCHITECTURAL PERFORMANCE PAGE (RQ1-3)
# =============================================================================
else:
    st.title("⚡ Architectural Performance & Research Benchmark")
    st.markdown("Empirical benchmark measurements evaluating query performance, scalability, and mining algorithms.")

    bench_results_path = os.path.join(BASE_DIR, "benchmark", "results.csv")
    scale_results_path = os.path.join(BASE_DIR, "benchmark", "scalability_results.csv")
    ap_fp_path = os.path.join(BASE_DIR, "report", "apriori_vs_fpgrowth_benchmark.csv")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("RQ1: Query Latency Across Architectures")
        if os.path.exists(bench_results_path):
            df_b = pd.read_csv(bench_results_path)
            fig_b = px.bar(
                df_b,
                x="Query",
                y="Warm Mean (s)",
                color="Config",
                barmode="group",
                title="Warm Query Latency: C1 (Normalized) vs C2 (Galaxy) vs C3 (Parquet) vs C4 (Pre-Agg)",
                template="plotly_white"
            )
            st.plotly_chart(fig_b, use_container_width=True)

    with col2:
        st.subheader("RQ1: Scalability Analysis (10%, 50%, 100%)")
        if os.path.exists(scale_results_path):
            df_s = pd.read_csv(scale_results_path)
            fig_s = go.Figure()
            fig_s.add_trace(go.Scatter(x=df_s["Data Scale"], y=df_s["C1 Normalized (s)"], mode="lines+markers", name="C1: Normalized"))
            fig_s.add_trace(go.Scatter(x=df_s["Data Scale"], y=df_s["C2 Galaxy (s)"], mode="lines+markers", name="C2: Galaxy Schema"))
            fig_s.update_layout(title="Scaling Curve: Execution Latency vs Dataset Size", template="plotly_white")
            st.plotly_chart(fig_s, use_container_width=True)

    st.subheader("RQ2: Mining Scalability (Apriori vs FP-Growth)")
    if os.path.exists(ap_fp_path):
        df_ap = pd.read_csv(ap_fp_path)
        fig_ap = px.line(
            df_ap,
            x="Min Support (%)",
            y=["Apriori Latency (s)", "FP-Growth Latency (s)"],
            markers=True,
            title="Algorithm Runtime Explosion: Apriori vs FP-Growth Across Support Thresholds",
            template="plotly_white"
        )
        st.plotly_chart(fig_ap, use_container_width=True)
        st.dataframe(df_ap, use_container_width=True)
