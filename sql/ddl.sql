-- ============================================================================
-- DWM E-Commerce Data Warehouse DDL (DuckDB / ANSI SQL Compatible)
-- Schema Type: Galaxy Schema (Fact Constellation)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. DIMENSION TABLES
-- ----------------------------------------------------------------------------

-- Product Dimension (Hierarchy: Department -> Aisle -> Product)
CREATE TABLE IF NOT EXISTS dim_product (
    product_key   INTEGER PRIMARY KEY,
    product_name  VARCHAR NOT NULL,
    aisle_id      INTEGER NOT NULL,
    aisle         VARCHAR NOT NULL,
    department_id INTEGER NOT NULL,
    department    VARCHAR NOT NULL
);

-- Time Dimension (Granularity: 168 Hourly Slots across 7 Days of Week)
CREATE TABLE IF NOT EXISTS dim_time (
    time_key    INTEGER PRIMARY KEY, -- order_dow * 24 + hour
    order_dow   INTEGER NOT NULL,    -- 0 to 6
    hour        INTEGER NOT NULL,    -- 0 to 23
    day_label   VARCHAR NOT NULL,    -- 'Day 0' ... 'Day 6'
    is_weekend  BOOLEAN NOT NULL,    -- TRUE for Days 0 and 1
    part_of_day VARCHAR NOT NULL     -- 'Morning', 'Afternoon', 'Evening', 'Night'
);

-- Customer Dimension (Profile enriched with purchase frequency & behavior)
CREATE TABLE IF NOT EXISTS dim_customer (
    customer_key            INTEGER PRIMARY KEY,
    total_orders            INTEGER NOT NULL,
    total_items             INTEGER NOT NULL,
    avg_basket_size         DOUBLE NOT NULL,
    avg_days_between_orders DOUBLE,
    rfm_segment             VARCHAR -- Populated in Week 5 (Clustering)
);

-- ----------------------------------------------------------------------------
-- 2. FACT TABLES
-- ----------------------------------------------------------------------------

-- Fact 1: Order Items (Grain: 1 row per product inside an order)
CREATE TABLE IF NOT EXISTS fact_order_items (
    order_id          INTEGER NOT NULL,
    product_key       INTEGER NOT NULL,
    customer_key      INTEGER NOT NULL,
    time_key          INTEGER NOT NULL,
    add_to_cart_order INTEGER NOT NULL,
    reordered         TINYINT NOT NULL
);

-- Fact 2: Orders (Grain: 1 row per order)
CREATE TABLE IF NOT EXISTS fact_orders (
    order_id               INTEGER PRIMARY KEY,
    customer_key           INTEGER NOT NULL,
    time_key               INTEGER NOT NULL,
    order_number           INTEGER NOT NULL,
    days_since_prior_order DOUBLE,
    basket_size            INTEGER NOT NULL,
    reorder_ratio          DOUBLE NOT NULL
);

-- Fact 3: Mined Association Rules (Populated in Week 5)
CREATE TABLE IF NOT EXISTS fact_rules (
    slice_name VARCHAR NOT NULL,
    antecedent VARCHAR NOT NULL,
    consequent VARCHAR NOT NULL,
    support    DOUBLE NOT NULL,
    confidence DOUBLE NOT NULL,
    lift       DOUBLE NOT NULL
);

-- ----------------------------------------------------------------------------
-- 3. PRE-AGGREGATED OLAP SUMMARY TABLE (For query acceleration in Week 3/4)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cube_dept_time (
    department      VARCHAR NOT NULL,
    aisle           VARCHAR NOT NULL,
    order_dow       INTEGER NOT NULL,
    hour            INTEGER NOT NULL,
    items           BIGINT NOT NULL,
    reordered_items BIGINT NOT NULL
);
