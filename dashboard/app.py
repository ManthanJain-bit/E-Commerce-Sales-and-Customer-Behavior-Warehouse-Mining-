import os
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# =============================================================================
# 1. PAGE SETUP & METADATA
# =============================================================================
st.set_page_config(
    page_title="Retail DWM Intelligence Portal | Galaxy Warehouse",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "warehouse", "dwm.duckdb").replace("\\", "/")


@st.cache_resource
def get_db_connection():
    """Persistent read-only connection to the DuckDB analytics warehouse."""
    return duckdb.connect(DB_PATH, read_only=True)


@st.cache_data(ttl=3600)
def run_query(sql_query: str) -> pd.DataFrame:
    """Execute SQL query against DuckDB and return a Pandas DataFrame."""
    con = get_db_connection()
    return con.execute(sql_query).df()


# =============================================================================
# 2. STATE-OF-THE-ART OBSIDIAN LUXURY DESIGN SYSTEM (CSS)
# =============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    /* Global Root & Typography */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Ambient Obsidian Background */
    .stApp {
        background: 
            radial-gradient(circle at 12% 15%, rgba(99, 102, 241, 0.12) 0%, transparent 45%),
            radial-gradient(circle at 88% 85%, rgba(168, 85, 247, 0.10) 0%, transparent 45%),
            radial-gradient(circle at 50% 50%, rgba(16, 185, 129, 0.04) 0%, transparent 60%),
            #070a13;
        color: #e2e8f0;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0b0f1e 0%, #080c18 50%, #050811 100%) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.07);
        box-shadow: 4px 0 24px rgba(0, 0, 0, 0.4);
    }
    section[data-testid="stSidebar"] .stRadio label {
        color: #cbd5e1 !important;
        font-weight: 500 !important;
        padding: 6px 10px;
        border-radius: 8px;
        transition: all 0.2s ease;
    }
    section[data-testid="stSidebar"] .stRadio label:hover {
        background: rgba(99, 102, 241, 0.12);
        color: #ffffff !important;
    }

    /* Top Brand Badge */
    .brand-header {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 16px;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 14px;
        margin-bottom: 20px;
    }
    .brand-logo {
        width: 38px;
        height: 38px;
        border-radius: 10px;
        background: linear-gradient(135deg, #6366f1, #a855f7);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4);
    }
    .brand-text h2 {
        margin: 0;
        font-size: 16px;
        font-weight: 700;
        letter-spacing: -0.3px;
        background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .brand-text p {
        margin: 0;
        font-size: 11px;
        color: #64748b;
        font-weight: 500;
    }

    /* System Status Pill */
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 12px;
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.25);
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
        color: #34d399;
        letter-spacing: 0.3px;
        margin-bottom: 16px;
    }
    .status-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: #10b981;
        box-shadow: 0 0 10px #10b981;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(1.15); }
    }

    /* Hero Banner */
    .hero-banner {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.12) 0%, rgba(168, 85, 247, 0.08) 50%, rgba(16, 185, 129, 0.04) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 28px 32px;
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(16px);
    }
    .hero-banner::after {
        content: '';
        position: absolute;
        top: 0; right: 0; width: 200px; height: 100%;
        background: radial-gradient(circle at 100% 0%, rgba(99, 102, 241, 0.25) 0%, transparent 70%);
        pointer-events: none;
    }
    .hero-banner h1 {
        font-size: 26px !important;
        font-weight: 800 !important;
        letter-spacing: -0.5px;
        margin: 0 0 8px 0 !important;
        color: #ffffff !important;
    }
    .hero-banner p {
        font-size: 14px !important;
        color: #94a3b8 !important;
        margin: 0 !important;
        line-height: 1.5;
        max-width: 900px;
    }

    /* KPI Grid & Cards */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px;
        margin-bottom: 28px;
    }
    .kpi-card {
        background: rgba(15, 23, 42, 0.65);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 16px;
        padding: 22px 20px;
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(20px);
        transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.25s cubic-bezier(0.4, 0, 0.2, 1), border-color 0.25s ease;
    }
    .kpi-card:hover {
        transform: translateY(-4px);
        border-color: rgba(99, 102, 241, 0.35);
        box-shadow: 0 16px 36px rgba(0, 0, 0, 0.5), 0 0 20px rgba(99, 102, 241, 0.15);
    }
    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; height: 3px;
        border-radius: 16px 16px 0 0;
    }
    .kpi-icon {
        font-size: 26px;
        margin-bottom: 12px;
        display: inline-block;
    }
    .kpi-label {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        color: #64748b;
        margin-bottom: 4px;
    }
    .kpi-val {
        font-size: 28px;
        font-weight: 800;
        letter-spacing: -0.5px;
        color: #ffffff;
        font-family: 'Plus Jakarta Sans', sans-serif;
        line-height: 1.1;
        margin-bottom: 8px;
    }
    .kpi-sub {
        font-size: 12px;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 4px;
    }

    .kpi-indigo::before { background: linear-gradient(90deg, #6366f1, #818cf8); }
    .kpi-indigo .kpi-val { color: #e0e7ff; }
    .kpi-indigo .kpi-sub { color: #818cf8; }

    .kpi-emerald::before { background: linear-gradient(90deg, #10b981, #34d399); }
    .kpi-emerald .kpi-val { color: #d1fae5; }
    .kpi-emerald .kpi-sub { color: #34d399; }

    .kpi-cyan::before { background: linear-gradient(90deg, #06b6d4, #38bdf8); }
    .kpi-cyan .kpi-val { color: #cffafe; }
    .kpi-cyan .kpi-sub { color: #38bdf8; }

    .kpi-amber::before { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
    .kpi-amber .kpi-val { color: #fef3c7; }
    .kpi-amber .kpi-sub { color: #fbbf24; }

    .kpi-rose::before { background: linear-gradient(90deg, #f43f5e, #fb7185); }
    .kpi-rose .kpi-val { color: #ffe4e6; }
    .kpi-rose .kpi-sub { color: #fb7185; }

    /* Glass Container */
    .glass-card {
        background: rgba(15, 23, 42, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 16px;
        padding: 24px;
        backdrop-filter: blur(16px);
        margin-bottom: 24px;
    }

    /* Insight Callouts */
    .insight-pill {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.04) 100%);
        border-left: 4px solid #10b981;
        border-radius: 0 14px 14px 0;
        padding: 16px 20px;
        margin: 20px 0;
    }
    .insight-pill p {
        margin: 0 !important;
        font-size: 13.5px !important;
        line-height: 1.6 !important;
        color: #a7f3d0 !important;
    }
    .insight-pill strong {
        color: #34d399 !important;
    }

    .discovery-pill {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.12) 0%, rgba(168, 85, 247, 0.06) 100%);
        border-left: 4px solid #818cf8;
        border-radius: 0 14px 14px 0;
        padding: 16px 20px;
        margin: 20px 0;
    }
    .discovery-pill p {
        margin: 0 !important;
        font-size: 13.5px !important;
        line-height: 1.6 !important;
        color: #c7d2fe !important;
    }
    .discovery-pill strong {
        color: #a5b4fc !important;
    }

    /* Strategy Matrix Table */
    .luxury-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        border-radius: 14px;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.07);
        margin: 16px 0;
    }
    .luxury-table th {
        background: rgba(30, 41, 59, 0.7);
        color: #cbd5e1;
        padding: 14px 18px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        text-align: left;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }
    .luxury-table td {
        background: rgba(15, 23, 42, 0.4);
        color: #94a3b8;
        padding: 14px 18px;
        font-size: 13px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.04);
    }
    .luxury-table tr:last-child td {
        border-bottom: none;
    }
    .luxury-table tr:hover td {
        background: rgba(99, 102, 241, 0.08);
        color: #f1f5f9;
    }

    /* Section Divider */
    .divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.08), transparent);
        margin: 32px 0;
    }

    /* Footer */
    .footer {
        text-align: center;
        padding: 32px 0 16px 0;
        color: #475569;
        font-size: 12px;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
        margin-top: 48px;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# 3. PLOTLY LUXURY DARK TEMPLATE
# =============================================================================
PLOTLY_THEME = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Plus Jakarta Sans, sans-serif", color="#94a3b8", size=12),
    title_font=dict(family="Plus Jakarta Sans, sans-serif", size=15, color="#f8fafc"),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8", size=11),
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ),
    xaxis=dict(
        gridcolor="rgba(255,255,255,0.04)",
        zerolinecolor="rgba(255,255,255,0.06)",
        tickfont=dict(color="#64748b")
    ),
    yaxis=dict(
        gridcolor="rgba(255,255,255,0.04)",
        zerolinecolor="rgba(255,255,255,0.06)",
        tickfont=dict(color="#64748b")
    ),
    margin=dict(l=40, r=20, t=55, b=40),
)

HEATMAP_PALETTE = [
    [0.0, "#0b0f1e"],
    [0.2, "#1e293b"],
    [0.4, "#312e81"],
    [0.6, "#4f46e5"],
    [0.8, "#818cf8"],
    [1.0, "#c7d2fe"]
]


# =============================================================================
# 4. SIDEBAR NAVIGATION & METRICS
# =============================================================================
with st.sidebar:
    st.markdown("""
    <div class="brand-header">
        <div class="brand-logo">⚡</div>
        <div class="brand-text">
            <h2>RETAIL DWM PORTAL</h2>
            <p>Intelligence & Mining Engine</p>
        </div>
    </div>
    <div class="status-pill">
        <span class="status-dot"></span>
        <span>DuckDB Warehouse Online</span>
    </div>
    """, unsafe_allow_html=True)

    nav_selection = st.radio(
        "Navigation",
        [
            "📊 Executive Overview",
            "🧊 OLAP Multidimensional Explorer",
            "👥 Customer Intelligence (RFM)",
            "🔍 Market Basket & Association Rules",
            "⚡ Architectural Performance (RQ1-3)"
        ],
        label_visibility="collapsed"
    )

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Warehouse Live Stats Card
    st.markdown("""
    <div class="glass-card" style="padding: 16px; margin: 0;">
        <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.2px; color: #64748b; margin-bottom: 12px;">
            Warehouse Metadata
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
            <span style="color: #94a3b8; font-size: 12px;">Storage Model</span>
            <span style="color: #818cf8; font-weight: 600; font-size: 12px;">Galaxy Constellation</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
            <span style="color: #94a3b8; font-size: 12px;">OLAP Engine</span>
            <span style="color: #38bdf8; font-weight: 600; font-size: 12px;">DuckDB 1.5.6</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
            <span style="color: #94a3b8; font-size: 12px;">Orders Fact</span>
            <span style="color: #34d399; font-weight: 600; font-size: 12px;">3,346,083</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
            <span style="color: #94a3b8; font-size: 12px;">Items Grain</span>
            <span style="color: #f59e0b; font-weight: 600; font-size: 12px;">33,819,106</span>
        </div>
        <div style="display: flex; justify-content: space-between;">
            <span style="color: #94a3b8; font-size: 12px;">Customers</span>
            <span style="color: #f43f5e; font-weight: 600; font-size: 12px;">206,209</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# 5. MODULE 1: EXECUTIVE OVERVIEW
# =============================================================================
if nav_selection == "📊 Executive Overview":
    st.markdown("""
    <div class="hero-banner">
        <h1>📊 Executive Operations & Performance Cockpit</h1>
        <p>Enterprise visibility across 33.8M product transactions, basket velocity patterns, and temporal purchasing cadences powered by in-process columnar DuckDB queries.</p>
    </div>
    """, unsafe_allow_html=True)

    # Fetch Top KPI Values
    kpis = run_query("""
        SELECT 
            COUNT(*) AS total_orders,
            COUNT(DISTINCT customer_key) AS total_customers,
            ROUND(AVG(basket_size), 2) AS avg_basket_size,
            ROUND(AVG(reorder_ratio) * 100, 2) AS avg_reorder_pct,
            SUM(basket_size) AS total_items
        FROM fact_orders;
    """).iloc[0]

    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi-card kpi-indigo">
            <span class="kpi-icon">📦</span>
            <div class="kpi-label">Total Orders</div>
            <div class="kpi-val">{int(kpis.total_orders):,}</div>
            <div class="kpi-sub">Across prior & train sets</div>
        </div>
        <div class="kpi-card kpi-emerald">
            <span class="kpi-icon">👥</span>
            <div class="kpi-label">Active Customers</div>
            <div class="kpi-val">{int(kpis.total_customers):,}</div>
            <div class="kpi-sub">Segmented via RFM K-Means</div>
        </div>
        <div class="kpi-card kpi-cyan">
            <span class="kpi-icon">🛍️</span>
            <div class="kpi-label">Items Transacted</div>
            <div class="kpi-val">{int(kpis.total_items):,}</div>
            <div class="kpi-sub">Across 49,688 SKUs</div>
        </div>
        <div class="kpi-card kpi-amber">
            <span class="kpi-icon">🧺</span>
            <div class="kpi-label">Avg Basket Size</div>
            <div class="kpi-val">{kpis.avg_basket_size}</div>
            <div class="kpi-sub">Items per checkout</div>
        </div>
        <div class="kpi-card kpi-rose">
            <span class="kpi-icon">🔄</span>
            <div class="kpi-label">Repurchase Rate</div>
            <div class="kpi-val">{kpis.avg_reorder_pct}%</div>
            <div class="kpi-sub">Customer brand loyalty</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown("#### 🏆 Product Sales Velocity (Top 15)")
        top_products = run_query("""
            SELECT p.product_name, COUNT(*) AS items_sold, 
                   ROUND(AVG(f.reordered) * 100, 1) AS reorder_rate
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
            color_continuous_scale=[[0, "#1e293b"], [0.5, "#6366f1"], [1, "#c084fc"]],
            labels={"items_sold": "Units Sold", "product_name": "Product Name", "reorder_rate": "Reorder %"}
        ).update_yaxes(autorange="reversed")
        fig_top.update_layout(**PLOTLY_THEME, title="Units Sold (Color Intensity = Reorder Rate %)")
        fig_top.update_layout(coloraxis_colorbar=dict(title="Reorder %", tickfont=dict(color="#64748b")))
        st.plotly_chart(fig_top, use_container_width=True)

    with col_right:
        st.markdown("#### 🔥 Customer Reorder Cadence (Day × Hour)")
        heat_data = run_query("""
            SELECT 
                t.order_dow, t.hour, 
                ROUND(AVG(f.reordered) * 100, 2) AS reorder_rate
            FROM fact_order_items f
            JOIN dim_time t USING (time_key)
            GROUP BY t.order_dow, t.hour
            ORDER BY t.order_dow, t.hour;
        """)
        pivot_heat = heat_data.pivot(index="order_dow", columns="hour", values="reorder_rate")
        day_names = ["Sun (Day 0)", "Mon (Day 1)", "Tue (Day 2)", "Wed (Day 3)", "Thu (Day 4)", "Fri (Day 5)", "Sat (Day 6)"]
        fig_heat = go.Figure(data=go.Heatmap(
            z=pivot_heat.values,
            x=[f"{h:02d}:00" for h in pivot_heat.columns],
            y=[day_names[d] if d < len(day_names) else f"Day {d}" for d in pivot_heat.index],
            colorscale=HEATMAP_PALETTE,
            colorbar=dict(title="Reorder %", tickfont=dict(color="#64748b")),
            hovertemplate="<b>%{y}</b> at <b>%{x}</b><br>Reorder Rate: %{z:.1f}%<extra></extra>"
        ))
        fig_heat.update_layout(**PLOTLY_THEME, title="Temporal Reorder Intensity Across 168 Hour Slots")
        st.plotly_chart(fig_heat, use_container_width=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown("#### 📈 Basket Dynamics Over Customer Lifecycle")
        trend_df = run_query("""
            SELECT order_number, ROUND(AVG(basket_size), 2) AS avg_basket_size
            FROM fact_orders
            WHERE order_number <= 60
            GROUP BY order_number
            ORDER BY order_number;
        """)
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=trend_df["order_number"], y=trend_df["avg_basket_size"],
            mode="lines+markers",
            line=dict(color="#6366f1", width=3),
            marker=dict(size=4, color="#a855f7"),
            fill="tozeroy",
            fillcolor="rgba(99, 102, 241, 0.08)",
            hovertemplate="Order #%{x}<br>Avg Basket: <b>%{y:.2f} items</b><extra></extra>"
        ))
        fig_trend.update_layout(**PLOTLY_THEME, title="Basket Size vs Repeat Order Sequence (Order 1 → 60)")
        fig_trend.update_layout(xaxis_title="Order Sequence Number", yaxis_title="Average Basket Size")
        st.plotly_chart(fig_trend, use_container_width=True)

    with col2:
        st.markdown("#### 🏢 Sales Volume by Top Departments")
        dept_df = run_query("""
            SELECT p.department, COUNT(*) AS items_sold, ROUND(AVG(f.reordered)*100, 1) AS reorder_rate
            FROM fact_order_items f
            JOIN dim_product p USING (product_key)
            GROUP BY p.department
            ORDER BY items_sold DESC
            LIMIT 7;
        """)
        fig_dept = px.pie(
            dept_df,
            names="department",
            values="items_sold",
            hole=0.6,
            color_discrete_sequence=["#6366f1", "#10b981", "#06b6d4", "#f59e0b", "#f43f5e", "#a855f7", "#ec4899"]
        )
        fig_dept.update_layout(**PLOTLY_THEME, title="Top 7 Department Market Share")
        fig_dept.update_traces(
            textinfo="percent+label",
            textfont=dict(color="#f8fafc", size=11),
            marker=dict(line=dict(color="#070a13", width=2))
        )
        st.plotly_chart(fig_dept, use_container_width=True)

    st.markdown("""
    <div class="insight-pill">
        <p><strong>💡 Key Lifecycle Finding:</strong> Repeat customers demonstrate a pronounced maturity curve: average basket size expands from <strong>9.5 items</strong> on initial checkout to <strong>11.4 items</strong> by their 30th purchase — validating cross-category catalog exploration over customer tenure.</p>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# 6. MODULE 2: OLAP MULTIDIMENSIONAL EXPLORER
# =============================================================================
elif nav_selection == "🧊 OLAP Multidimensional Explorer":
    st.markdown("""
    <div class="hero-banner">
        <h1>🧊 OLAP Multidimensional Explorer</h1>
        <p>Sub-second slice, dice, roll-up, and drill-down across products, departments, and temporal hierarchies leveraging DuckDB vector execution on 33.8 million transaction records.</p>
    </div>
    """, unsafe_allow_html=True)

    # Interactive Dimension Selector
    st.sidebar.markdown("### 🎛️ Multidimensional Filters")

    all_depts = run_query("SELECT DISTINCT department FROM dim_product ORDER BY 1;")["department"].tolist()
    sel_depts = st.sidebar.multiselect(
        "Departments (Dice)",
        all_depts,
        default=["produce", "dairy eggs", "snacks", "beverages"]
    )

    parts_of_day = ["Morning", "Afternoon", "Evening", "Night"]
    sel_parts = st.sidebar.multiselect("Part of Day (Dice)", parts_of_day, default=parts_of_day)

    weekend_mode = st.sidebar.selectbox("Day Type (Slice)", ["All Days", "Weekends Only (Sun/Mon)", "Weekdays Only"])

    hierarchy_level = st.sidebar.selectbox(
        "Drill-Down Hierarchy",
        ["department", "aisle", "product_name"],
        format_func=lambda x: {"department": "🏢 Department Level (Highest)", "aisle": "🛒 Aisle Level (Mid)", "product_name": "📦 SKU Product Level (Fine Grain)"}[x]
    )

    if not sel_depts or not sel_parts:
        st.warning("⚠️ Please select at least one department and part-of-day in the sidebar to run the OLAP engine.")
        st.stop()

    dept_clause = ", ".join(f"'{d}'" for d in sel_depts)
    part_clause = ", ".join(f"'{p}'" for p in sel_parts)
    wk_clause = {"All Days": "TRUE", "Weekends Only (Sun/Mon)": "t.is_weekend = TRUE", "Weekdays Only": "t.is_weekend = FALSE"}[weekend_mode]

    olap_query = f"""
        SELECT 
            p.{hierarchy_level} AS dimensional_dimension,
            COUNT(*) AS total_items,
            ROUND(AVG(f.reordered) * 100, 2) AS reorder_rate_pct
        FROM fact_order_items f
        JOIN dim_product p USING (product_key)
        JOIN dim_time t USING (time_key)
        WHERE p.department IN ({dept_clause})
          AND t.part_of_day IN ({part_clause})
          AND {wk_clause}
        GROUP BY p.{hierarchy_level}
        ORDER BY total_items DESC
        LIMIT 30;
    """
    df_olap = run_query(olap_query)

    col1, col2 = st.columns([3, 2], gap="large")

    with col1:
        st.markdown(f"#### 📊 Volume Distribution by {hierarchy_level.replace('_', ' ').title()}")
        fig_olap = px.bar(
            df_olap,
            x="dimensional_dimension",
            y="total_items",
            color="reorder_rate_pct",
            color_continuous_scale=[[0, "#0369a1"], [0.5, "#6366f1"], [1, "#a855f7"]],
            labels={"dimensional_dimension": hierarchy_level.replace('_', ' ').title(), "total_items": "Volume Sold", "reorder_rate_pct": "Reorder %"}
        )
        fig_olap.update_layout(**PLOTLY_THEME, title=f"OLAP Drill Level: {hierarchy_level.replace('_', ' ').title()}")
        st.plotly_chart(fig_olap, use_container_width=True)

    with col2:
        st.markdown("#### 📋 Aggregated Results")
        display_df = df_olap.rename(columns={
            "dimensional_dimension": hierarchy_level.replace('_', ' ').title(),
            "total_items": "Total Units",
            "reorder_rate_pct": "Reorder %"
        })
        st.dataframe(
            display_df.style.format({
                "Total Units": "{:,.0f}",
                "Reorder %": "{:.2f}%"
            }),
            height=400
        )

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Pivot Matrix View
    st.markdown("#### 🔲 Cross-Tabulation Pivot Matrix: Department × Part of Day")
    pivot_query = f"""
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
        WHERE p.department IN ({dept_clause})
        GROUP BY p.department
        ORDER BY Total DESC;
    """
    df_pivot = run_query(pivot_query)
    st.dataframe(
        df_pivot.style.format({
            "Morning": "{:,.0f}",
            "Afternoon": "{:,.0f}",
            "Evening": "{:,.0f}",
            "Night": "{:,.0f}",
            "Total": "{:,.0f}"
        }),
        height=320
    )


# =============================================================================
# 7. MODULE 3: CUSTOMER INTELLIGENCE (RFM)
# =============================================================================
elif nav_selection == "👥 Customer Intelligence (RFM)":
    st.markdown("""
    <div class="hero-banner">
        <h1>👥 Customer Intelligence — Adapted RFM Segmentation</h1>
        <p>Unsupervised K-Means clustering ($k=4$, silhouette=0.411) partitioning 206,209 customers into actionable retail personas based on Recency gap days, Frequency order counts, and Monetary volume.</p>
    </div>
    """, unsafe_allow_html=True)

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

    # Persona Highlights
    persona_metadata = {
        "Loyal Power Shoppers": {"color": "#a855f7", "icon": "👑", "sub": "High Frequency · Low Gap"},
        "High-Volume Regulars": {"color": "#10b981", "icon": "🔥", "sub": "Consistent Weekly Volume"},
        "Casual Occasionals": {"color": "#06b6d4", "icon": "🛒", "sub": "Bi-weekly Basket Builders"},
        "Infrequent / At-Risk": {"color": "#f43f5e", "icon": "⚠️", "sub": "Lapsed / Churn Danger"}
    }

    cols = st.columns(len(seg_summary), gap="medium")
    for idx, (_, row) in enumerate(seg_summary.iterrows()):
        seg_name = row["rfm_segment"]
        meta = persona_metadata.get(seg_name, {"color": "#6366f1", "icon": "👤", "sub": "Customer Segment"})
        with cols[idx]:
            st.markdown(f"""
            <div class="kpi-card" style="border-top: 3px solid {meta['color']}; text-align: center;">
                <span style="font-size: 32px; margin-bottom: 8px; display: inline-block;">{meta['icon']}</span>
                <div style="font-size: 13px; font-weight: 700; color: {meta['color']}; margin-bottom: 6px;">
                    {seg_name}
                </div>
                <div style="font-size: 26px; font-weight: 800; color: #ffffff; line-height: 1.1; margin-bottom: 4px;">
                    {int(row['customer_count']):,}
                </div>
                <div style="font-size: 11px; color: #64748b; font-weight: 600;">
                    {row['percentage']}% of total base
                </div>
                <div style="font-size: 11px; color: {meta['color']}; margin-top: 8px;">
                    {meta['sub']}
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown("#### 🍩 Persona Share of Customer Base")
        fig_donut = px.pie(
            seg_summary,
            names="rfm_segment",
            values="customer_count",
            hole=0.6,
            color="rfm_segment",
            color_discrete_map={
                "Loyal Power Shoppers": "#a855f7",
                "High-Volume Regulars": "#10b981",
                "Casual Occasionals": "#06b6d4",
                "Infrequent / At-Risk": "#f43f5e"
            }
        )
        fig_donut.update_layout(**PLOTLY_THEME, title="Distribution Across 206,209 Customer Accounts")
        fig_donut.update_traces(
            textinfo="percent+label",
            textfont=dict(color="#ffffff", size=11),
            marker=dict(line=dict(color="#070a13", width=2))
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with col2:
        st.markdown("#### 📊 Behavioral Metrics Comparison")
        fig_bar = px.bar(
            seg_summary,
            x="rfm_segment",
            y="avg_frequency_orders",
            color="avg_recency_gap_days",
            color_continuous_scale=[[0, "#10b981"], [0.5, "#f59e0b"], [1, "#f43f5e"]],
            labels={"rfm_segment": "Segment", "avg_frequency_orders": "Avg Orders", "avg_recency_gap_days": "Avg Gap (Days)"}
        )
        fig_bar.update_layout(**PLOTLY_THEME, title="Order Velocity (Color Intensity = Gap Days Between Orders)")
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    st.markdown("#### 🎯 Prescriptive Retail CRM Playbooks")
    st.markdown("""
    <table class="luxury-table">
        <thead>
            <tr>
                <th>Persona</th>
                <th>Behavioral Profile</th>
                <th>Average Metrics (R · F · M)</th>
                <th>Targeted Marketing Strategy</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td style="color: #a855f7; font-weight: 700;">👑 Loyal Power Shoppers</td>
                <td>Highly active, top repurchase volume, minimal ordering friction</td>
                <td>5.4d gap · 68.9 orders · 839 items</td>
                <td>VIP delivery subscriptions, early access to new SKUs, white-glove customer support</td>
            </tr>
            <tr>
                <td style="color: #10b981; font-weight: 700;">🔥 High-Volume Regulars</td>
                <td>Predictable weekly replenishment, substantial basket totals</td>
                <td>9.2d gap · 34.7 orders · 355 items</td>
                <td>Multi-buy discounts, automated replenishment reminders, cross-category bundle savings</td>
            </tr>
            <tr>
                <td style="color: #06b6d4; font-weight: 700;">🛒 Casual Occasionals</td>
                <td>Moderate repurchase cadence, occasional basket top-ups</td>
                <td>12.2d gap · 11.8 orders · 105 items</td>
                <td>Basket-builder thresholds (e.g. Free delivery on orders over $50), weekend deal spotlights</td>
            </tr>
            <tr>
                <td style="color: #f43f5e; font-weight: 700;">⚠️ Infrequent / At-Risk</td>
                <td>Long gap between orders, declining checkout frequency</td>
                <td>22.9d gap · 7.0 orders · 68 items</td>
                <td>Win-back promo codes, personalized "We Miss You" notifications, surveys on friction points</td>
            </tr>
        </tbody>
    </table>
    """, unsafe_allow_html=True)


# =============================================================================
# 8. MODULE 4: ASSOCIATION RULES & MARKET BASKET MINING
# =============================================================================
elif nav_selection == "🔍 Market Basket & Association Rules":
    st.markdown("""
    <div class="hero-banner">
        <h1>🔍 Market Basket Intelligence & Contextual Slice Mining</h1>
        <p>High-confidence item association rules derived via FP-Growth on multi-dimensional transaction slices — demonstrating how dimensional context reveals hidden cross-selling opportunities.</p>
    </div>
    """, unsafe_allow_html=True)

    rules_df = run_query("SELECT * FROM fact_rules;")

    st.sidebar.markdown("### 🎛️ Association Rule Controls")
    slice_options = sorted(rules_df["slice_name"].unique())
    selected_slice = st.sidebar.selectbox("Contextual Slice", slice_options)
    min_lift_val = st.sidebar.slider("Minimum Lift Threshold", 1.0, 5.0, 1.2, 0.1)
    min_conf_val = st.sidebar.slider("Minimum Confidence Threshold", 0.20, 0.80, 0.25, 0.05)

    filtered = rules_df[
        (rules_df["slice_name"] == selected_slice) &
        (rules_df["lift"] >= min_lift_val) &
        (rules_df["confidence"] >= min_conf_val)
    ].sort_values("lift", ascending=False)

    col1, col2, col3 = st.columns(3)
    col1.metric("🎯 Active Context", selected_slice.replace("_", " "))
    col2.metric("📋 Discovered Rules", len(filtered))
    col3.metric("🚀 Max Rule Lift", f"{filtered['lift'].max():.2f}" if len(filtered) > 0 else "N/A")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    if len(filtered) > 0:
        col1, col2 = st.columns([3, 2], gap="large")

        with col1:
            st.markdown("#### 🌐 Rule Metric Geometry (Support vs Confidence)")
            fig_rules = px.scatter(
                filtered,
                x="support",
                y="confidence",
                size="lift",
                color="lift",
                hover_data=["antecedent", "consequent"],
                color_continuous_scale=[[0, "#1e293b"], [0.5, "#6366f1"], [1, "#ec4899"]],
                size_max=28,
            )
            fig_rules.update_layout(**PLOTLY_THEME, title=f"Rules in {selected_slice} (Bubble Size = Lift)")
            st.plotly_chart(fig_rules, use_container_width=True)

        with col2:
            st.markdown("#### 📋 High-Lift Rules Table")
            display_cols = ["antecedent", "consequent", "support", "confidence", "lift"]
            st.dataframe(
                filtered[display_cols].rename(columns={
                    "antecedent": "Antecedent (IF)",
                    "consequent": "Consequent (THEN)",
                    "support": "Support",
                    "confidence": "Confidence",
                    "lift": "Lift"
                }).style.format({
                    "Support": "{:.4f}",
                    "Confidence": "{:.2%}",
                    "Lift": "{:.2f}"
                }),
                height=400
            )
    else:
        st.warning("⚠️ No rules found matching the chosen Lift/Confidence thresholds. Lower the sliders in the sidebar.")

    # Contextual Discovery Banner
    if selected_slice == "Weekend_Morning":
        st.markdown("""
        <div class="discovery-pill">
            <p>🧪 <strong>Research Finding (RQ3 Contextual Novelty):</strong> On <em>Weekend Mornings</em>, specialized culinary co-purchases emerge: 
            <code>Organic Lemon ⟹ Organic Hass Avocado</code> achieves a <strong>Lift of 3.03</strong> (Confidence: 26.4%). 
            This reflects weekend brunch and fresh meal prep behaviors that are <strong>completely diluted and invisible in global baseline mining</strong>!</p>
        </div>
        """, unsafe_allow_html=True)


# =============================================================================
# 9. MODULE 5: ARCHITECTURAL PERFORMANCE BENCHMARKS (RQ1-3)
# =============================================================================
else:
    st.markdown("""
    <div class="hero-banner">
        <h1>⚡ Architectural Benchmarks & Research Findings</h1>
        <p>Empirical latency measurements evaluating query execution across 4 storage architectures (RQ1), Apriori vs FP-Growth scalability (RQ2), and contextual slice-aware rule novelty (RQ3).</p>
    </div>
    """, unsafe_allow_html=True)

    bench_path = os.path.join(BASE_DIR, "benchmark", "results.csv")
    scale_path = os.path.join(BASE_DIR, "benchmark", "scalability_results.csv")
    apfp_path = os.path.join(BASE_DIR, "report", "apriori_vs_fpgrowth_benchmark.csv")

    st.markdown("#### 🔬 RQ1: Analytical Query Latency Across Storage Architectures")
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        if os.path.exists(bench_path):
            df_b = pd.read_csv(bench_path)
            config_palette = {
                "C1_Normalized": "#f43f5e",
                "C2_Galaxy": "#6366f1",
                "C3_Parquet": "#06b6d4",
                "C4_PreAgg": "#10b981"
            }
            fig_b = px.bar(
                df_b, x="Query", y="Warm Mean (s)", color="Config",
                barmode="group",
                color_discrete_map=config_palette,
                labels={"Warm Mean (s)": "Mean Latency (Seconds)", "Query": "Benchmark Query"}
            )
            fig_b.update_layout(**PLOTLY_THEME, title="Warm Execution Latency: C1 vs C2 vs C3 vs C4")
            st.plotly_chart(fig_b, use_container_width=True)
        else:
            st.info("Benchmark data not found.")

    with col2:
        if os.path.exists(scale_path):
            df_s = pd.read_csv(scale_path)
            fig_s = go.Figure()
            fig_s.add_trace(go.Scatter(
                x=df_s["Data Scale"], y=df_s["C1 Normalized (s)"],
                mode="lines+markers", name="C1: Normalized Staging",
                line=dict(color="#f43f5e", width=2.5),
                marker=dict(size=8, color="#f43f5e")
            ))
            fig_s.add_trace(go.Scatter(
                x=df_s["Data Scale"], y=df_s["C2 Galaxy (s)"],
                mode="lines+markers", name="C2: Galaxy Schema",
                line=dict(color="#6366f1", width=2.5),
                marker=dict(size=8, color="#6366f1")
            ))
            fig_s.update_layout(**PLOTLY_THEME, title="Scalability: Latency Growth vs Dataset Scale")
            fig_s.update_layout(xaxis_title="Data Scale", yaxis_title="Latency (Seconds)")
            st.plotly_chart(fig_s, use_container_width=True)
        else:
            st.info("Scalability data not found.")

    st.markdown("""
    <div class="insight-pill">
        <p><strong>RQ1 Conclusion:</strong> The Galaxy Schema (C2) provides a steady <strong>2.4x - 2.7x speedup</strong> over 3NF normalized tables across all scales. The pre-aggregated summary cube (C4) delivers <strong>up to 106x acceleration</strong> (e.g. Q2 Dept-Day Pivot drops from 0.34s to 0.0032s), proving pre-aggregation is essential for real-time dashboards on large volumes.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    st.markdown("#### 🔬 RQ2: Apriori vs FP-Growth Algorithmic Scalability")
    if os.path.exists(apfp_path):
        df_ap = pd.read_csv(apfp_path)
        col_c1, col_c2 = st.columns([3, 2], gap="large")
        with col_c1:
            fig_algo = go.Figure()
            fig_algo.add_trace(go.Scatter(
                x=df_ap["Min Support (%)"], y=df_ap["Apriori Latency (s)"],
                mode="lines+markers", name="Apriori",
                line=dict(color="#f43f5e", width=2.5, dash="dot"),
                marker=dict(size=8, color="#f43f5e")
            ))
            fig_algo.add_trace(go.Scatter(
                x=df_ap["Min Support (%)"], y=df_ap["FP-Growth Latency (s)"],
                mode="lines+markers", name="FP-Growth",
                line=dict(color="#10b981", width=2.5),
                marker=dict(size=8, color="#10b981")
            ))
            fig_algo.update_layout(**PLOTLY_THEME, title="Execution Latency Across Decreasing Support Thresholds")
            fig_algo.update_layout(xaxis_title="Minimum Support Threshold", yaxis_title="Runtime (Seconds)")
            st.plotly_chart(fig_algo, use_container_width=True)

        with col_c2:
            st.markdown("##### 📋 Benchmark Data")
            st.dataframe(
                df_ap[["Min Support (%)", "Frequent Itemsets", "Apriori Latency (s)", "FP-Growth Latency (s)", "Speedup (Apriori / FP)"]].rename(columns={
                    "Min Support (%)": "Min Support",
                    "Frequent Itemsets": "Itemsets",
                    "Apriori Latency (s)": "Apriori (s)",
                    "FP-Growth Latency (s)": "FP-Growth (s)",
                    "Speedup (Apriori / FP)": "Speedup"
                }),
                height=300
            )

    st.markdown("""
    <div class="insight-pill">
        <p><strong>RQ2 Conclusion:</strong> FP-Growth avoids exponential candidate generation, processing 100K orders with 200 products in <strong>2.7s</strong> at 1% support, whereas Apriori faces combinatorial bottlenecking as support drops.</p>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# 10. FOOTER
# =============================================================================
st.markdown("""
<div class="footer">
    <span>⚡ Retail DWM Analytics & Intelligence Platform</span> · 
    <span>Galaxy Constellation Schema</span> · 
    <span>DuckDB Columnar Engine × Streamlit</span>
</div>
""", unsafe_allow_html=True)
