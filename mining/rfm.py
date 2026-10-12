import os
import time
import duckdb
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import plotly.express as px
import plotly.graph_objects as go

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "warehouse", "dwm.duckdb")
REPORT_DIR = os.path.join(BASE_DIR, "report")
os.makedirs(REPORT_DIR, exist_ok=True)


def run_rfm_segmentation():
    print("=" * 70)
    print("WEEK 5 - PART 1: ADAPTED RFM CUSTOMER SEGMENTATION (K-MEANS)")
    print("=" * 70)

    con = duckdb.connect(DB_PATH)

    # 1. Extract RFM features
    print("Extracting customer behavioral features from dim_customer...")
    df = con.execute("""
        SELECT 
            customer_key,
            avg_days_between_orders AS R,
            total_orders AS F,
            total_items AS M
        FROM dim_customer
        WHERE avg_days_between_orders IS NOT NULL;
    """).df()
    print(f"Loaded {len(df):,} valid customers with repeat orders.")

    # 2. Standardize Features
    scaler = StandardScaler()
    X = scaler.fit_transform(df[["R", "F", "M"]])

    # 3. Determine Optimal K (Elbow Method & Silhouette Analysis)
    print("\nEvaluating K values (k=2 to 6) on a representative sample (20,000 customers)...")
    np.random.seed(42)
    sample_indices = np.random.choice(len(X), size=20000, replace=False)
    X_sample = X[sample_indices]

    k_eval = []
    for k in range(2, 7):
        km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(X)
        sample_preds = km.predict(X_sample)
        sil = silhouette_score(X_sample, sample_preds)
        k_eval.append({
            "k": k,
            "Inertia": round(km.inertia_, 2),
            "Silhouette": round(sil, 4)
        })
        print(f"  k={k} | Inertia={km.inertia_:,.1f} | Silhouette Score={sil:.4f}")

    df_keval = pd.DataFrame(k_eval)
    df_keval.to_csv(os.path.join(REPORT_DIR, "rfm_k_evaluation.csv"), index=False)

    # Choose k=4 (balances distinct business persona separation and inertia elbow)
    optimal_k = 4
    print(f"\nFitting final K-Means model with optimal k={optimal_k} on all {len(X):,} customers...")
    t0 = time.time()
    final_km = KMeans(n_clusters=optimal_k, n_init=10, random_state=42).fit(X)
    df["cluster"] = final_km.labels_
    fit_time = time.time() - t0
    print(f"Model fitted in {fit_time:.2f}s.")

    # 4. Profile Clusters
    cluster_stats = df.groupby("cluster").agg(
        customers=("customer_key", "count"),
        avg_R=("R", "mean"),
        avg_F=("F", "mean"),
        avg_M=("M", "mean")
    ).round(2)
    cluster_stats["pct"] = round(cluster_stats["customers"] * 100.0 / len(df), 2)
    print("\nCluster Means (R = Avg Gap Days, F = Total Orders, M = Total Items):")
    print(cluster_stats.to_string())

    # 5. Assign Meaningful Business Segment Labels
    # High F & High M & Low R => Champions / Frequent Heavy Buyers
    # Moderate F & M & Low R => Steady Regulars
    # Low F & High R => Churn-Risk / Lapsed Occasionals
    # Moderate F & High M => Bulk Family Shoppers
    def assign_segment_name(row):
        r, f, m = row["avg_R"], row["avg_F"], row["avg_M"]
        if f > 40:
            return "Loyal Power Shoppers"
        elif r > 18:
            return "Infrequent / At-Risk"
        elif m > 150:
            return "High-Volume Regulars"
        else:
            return "Casual Occasionals"

    cluster_stats["rfm_segment"] = cluster_stats.apply(assign_segment_name, axis=1)
    label_map = cluster_stats["rfm_segment"].to_dict()
    df["rfm_segment"] = df["cluster"].map(label_map)

    print("\nAssigned Business Segment Taxonomy:")
    for c_id, name in label_map.items():
        stats = cluster_stats.loc[c_id]
        print(f"  Cluster {c_id} -> '{name}': {stats['customers']:,} users ({stats['pct']}%) | R={stats['avg_R']}d, F={stats['avg_F']} orders, M={stats['avg_M']} items")

    # 6. Update dim_customer in DuckDB
    print("\nUpdating dim_customer.rfm_segment in DuckDB warehouse...")
    seg_update_df = df[["customer_key", "rfm_segment"]]
    con.register("seg_update_df", seg_update_df)
    con.execute("""
        UPDATE dim_customer
        SET rfm_segment = seg_update_df.rfm_segment
        FROM seg_update_df
        WHERE dim_customer.customer_key = seg_update_df.customer_key;
    """)
    updated_count = con.execute("SELECT COUNT(*) FROM dim_customer WHERE rfm_segment IS NOT NULL;").fetchone()[0]
    print(f" -> Successfully updated {updated_count:,} customer profiles in dim_customer!")

    # 7. Update Parquet export
    pq_cust = os.path.join(BASE_DIR, "data", "warehouse", "dim_customer.parquet").replace("\\", "/")
    con.execute(f"COPY dim_customer TO '{pq_cust}' (FORMAT PARQUET, COMPRESSION ZSTD);")
    print(f" -> Re-exported dim_customer.parquet with rfm_segment.")

    # 8. Generate Visualizations
    fig = px.scatter_3d(
        df.sample(5000, random_state=42),
        x="R", y="F", z="M",
        color="rfm_segment",
        title="3D Customer Segmentation: Recency (Gap Days) vs Frequency vs Monetary (Items)",
        labels={"R": "Recency (Avg Gap Days)", "F": "Frequency (Orders)", "M": "Monetary Proxy (Items)"},
        template="plotly_white",
        opacity=0.7
    )
    fig.write_html(os.path.join(REPORT_DIR, "rfm_clusters_3d.html"))

    pie_df = df["rfm_segment"].value_counts().reset_index()
    pie_df.columns = ["Segment", "Count"]
    fig2 = px.pie(
        pie_df,
        names="Segment",
        values="Count",
        title="Customer Base Distribution across RFM Segments",
        template="plotly_white",
        hole=0.4
    )
    fig2.write_html(os.path.join(REPORT_DIR, "rfm_segment_distribution.html"))

    con.close()
    return cluster_stats


if __name__ == "__main__":
    run_rfm_segmentation()
