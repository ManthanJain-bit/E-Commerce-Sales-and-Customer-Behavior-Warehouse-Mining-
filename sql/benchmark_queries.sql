-- ============================================================================
-- DWM Project: Standardized Benchmark Queries (Week 4 / Research Question 1)
-- Comparing 4 Storage & Schema Architectures Across 33.8M+ Rows
-- C1: Normalized Staging (Multi-table joins)
-- C2: Galaxy Schema (fact_* + dim_* conformed dimensional model)
-- C3: Direct Columnar Parquet (Querying .parquet files directly on disk)
-- C4: Pre-Aggregated OLAP Cube (cube_dept_time summary table)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Q1: Department Roll-Up (Items Sold by Department)
-- ----------------------------------------------------------------------------
-- C1 (Normalized)
SELECT d.department, COUNT(*) AS items_sold
FROM stg_op op
JOIN stg_products p ON op.product_id = p.product_id
JOIN stg_departments d ON p.department_id = d.department_id
GROUP BY d.department;

-- C2 (Galaxy)
SELECT p.department, COUNT(*) AS items_sold
FROM fact_order_items f
JOIN dim_product p USING (product_key)
GROUP BY p.department;

-- C3 (Columnar Parquet)
SELECT p.department, COUNT(*) AS items_sold
FROM 'data/warehouse/fact_order_items.parquet' f
JOIN 'data/warehouse/dim_product.parquet' p ON f.product_key = p.product_key
GROUP BY p.department;

-- C4 (Pre-Aggregated Cube)
SELECT department, SUM(items) AS items_sold
FROM cube_dept_time
GROUP BY department;


-- ----------------------------------------------------------------------------
-- Q2: Department x Day of Week Pivot Cross-Tabulation
-- ----------------------------------------------------------------------------
-- C1 (Normalized)
SELECT d.department,
       SUM(CASE WHEN o.order_dow = 0 THEN 1 ELSE 0 END) AS d0,
       SUM(CASE WHEN o.order_dow = 1 THEN 1 ELSE 0 END) AS d1,
       SUM(CASE WHEN o.order_dow = 2 THEN 1 ELSE 0 END) AS d2,
       SUM(CASE WHEN o.order_dow = 3 THEN 1 ELSE 0 END) AS d3,
       SUM(CASE WHEN o.order_dow = 4 THEN 1 ELSE 0 END) AS d4,
       SUM(CASE WHEN o.order_dow = 5 THEN 1 ELSE 0 END) AS d5,
       SUM(CASE WHEN o.order_dow = 6 THEN 1 ELSE 0 END) AS d6
FROM stg_op op
JOIN stg_orders o USING (order_id)
JOIN stg_products p ON op.product_id = p.product_id
JOIN stg_departments d ON p.department_id = d.department_id
GROUP BY d.department;

-- C2 (Galaxy)
SELECT p.department,
       SUM(CASE WHEN t.order_dow = 0 THEN 1 ELSE 0 END) AS d0,
       SUM(CASE WHEN t.order_dow = 1 THEN 1 ELSE 0 END) AS d1,
       SUM(CASE WHEN t.order_dow = 2 THEN 1 ELSE 0 END) AS d2,
       SUM(CASE WHEN t.order_dow = 3 THEN 1 ELSE 0 END) AS d3,
       SUM(CASE WHEN t.order_dow = 4 THEN 1 ELSE 0 END) AS d4,
       SUM(CASE WHEN t.order_dow = 5 THEN 1 ELSE 0 END) AS d5,
       SUM(CASE WHEN t.order_dow = 6 THEN 1 ELSE 0 END) AS d6
FROM fact_order_items f
JOIN dim_product p USING (product_key)
JOIN dim_time t USING (time_key)
GROUP BY p.department;

-- C3 (Columnar Parquet)
SELECT p.department,
       SUM(CASE WHEN t.order_dow = 0 THEN 1 ELSE 0 END) AS d0,
       SUM(CASE WHEN t.order_dow = 1 THEN 1 ELSE 0 END) AS d1,
       SUM(CASE WHEN t.order_dow = 2 THEN 1 ELSE 0 END) AS d2,
       SUM(CASE WHEN t.order_dow = 3 THEN 1 ELSE 0 END) AS d3,
       SUM(CASE WHEN t.order_dow = 4 THEN 1 ELSE 0 END) AS d4,
       SUM(CASE WHEN t.order_dow = 5 THEN 1 ELSE 0 END) AS d5,
       SUM(CASE WHEN t.order_dow = 6 THEN 1 ELSE 0 END) AS d6
FROM 'data/warehouse/fact_order_items.parquet' f
JOIN 'data/warehouse/dim_product.parquet' p ON f.product_key = p.product_key
JOIN 'data/warehouse/dim_time.parquet' t ON f.time_key = t.time_key
GROUP BY p.department;

-- C4 (Pre-Aggregated Cube)
SELECT department,
       SUM(CASE WHEN order_dow = 0 THEN items ELSE 0 END) AS d0,
       SUM(CASE WHEN order_dow = 1 THEN items ELSE 0 END) AS d1,
       SUM(CASE WHEN order_dow = 2 THEN items ELSE 0 END) AS d2,
       SUM(CASE WHEN order_dow = 3 THEN items ELSE 0 END) AS d3,
       SUM(CASE WHEN order_dow = 4 THEN items ELSE 0 END) AS d4,
       SUM(CASE WHEN order_dow = 5 THEN items ELSE 0 END) AS d5,
       SUM(CASE WHEN order_dow = 6 THEN items ELSE 0 END) AS d6
FROM cube_dept_time
GROUP BY department;


-- ----------------------------------------------------------------------------
-- Q3: Multi-Dimensional Dice with Reorder Rate
-- ----------------------------------------------------------------------------
-- C1 (Normalized)
SELECT d.department, AVG(op.reordered) AS reorder_rate
FROM stg_op op
JOIN stg_orders o USING (order_id)
JOIN stg_products p ON op.product_id = p.product_id
JOIN stg_departments d ON p.department_id = d.department_id
WHERE d.department IN ('produce', 'dairy eggs')
  AND o.order_dow IN (0, 1)
  AND CAST(o.order_hour_of_day AS INTEGER) BETWEEN 8 AND 12
GROUP BY d.department;

-- C2 (Galaxy)
SELECT p.department, AVG(f.reordered) AS reorder_rate
FROM fact_order_items f
JOIN dim_product p USING (product_key)
JOIN dim_time t USING (time_key)
WHERE p.department IN ('produce', 'dairy eggs')
  AND t.is_weekend = TRUE
  AND t.hour BETWEEN 8 AND 12
GROUP BY p.department;

-- C3 (Columnar Parquet)
SELECT p.department, AVG(f.reordered) AS reorder_rate
FROM 'data/warehouse/fact_order_items.parquet' f
JOIN 'data/warehouse/dim_product.parquet' p ON f.product_key = p.product_key
JOIN 'data/warehouse/dim_time.parquet' t ON f.time_key = t.time_key
WHERE p.department IN ('produce', 'dairy eggs')
  AND t.is_weekend = TRUE
  AND t.hour BETWEEN 8 AND 12
GROUP BY p.department;

-- C4 (Pre-Aggregated Cube)
SELECT department, SUM(reordered_items) * 1.0 / SUM(items) AS reorder_rate
FROM cube_dept_time
WHERE department IN ('produce', 'dairy eggs')
  AND order_dow IN (0, 1)
  AND hour BETWEEN 8 AND 12
GROUP BY department;


-- ----------------------------------------------------------------------------
-- Q4: Top 20 High-Velocity Products
-- ----------------------------------------------------------------------------
-- C1 (Normalized)
SELECT p.product_name, COUNT(*) AS items, AVG(op.reordered) AS reorder_rate
FROM stg_op op
JOIN stg_products p USING (product_id)
GROUP BY p.product_name
ORDER BY items DESC
LIMIT 20;

-- C2 (Galaxy)
SELECT p.product_name, COUNT(*) AS items, AVG(f.reordered) AS reorder_rate
FROM fact_order_items f
JOIN dim_product p USING (product_key)
GROUP BY p.product_name
ORDER BY items DESC
LIMIT 20;

-- C3 (Columnar Parquet)
SELECT p.product_name, COUNT(*) AS items, AVG(f.reordered) AS reorder_rate
FROM 'data/warehouse/fact_order_items.parquet' f
JOIN 'data/warehouse/dim_product.parquet' p ON f.product_key = p.product_key
GROUP BY p.product_name
ORDER BY items DESC
LIMIT 20;


-- ----------------------------------------------------------------------------
-- Q5: Multidimensional CUBE Aggregation (Department x Part of Day)
-- ----------------------------------------------------------------------------
-- C1 (Normalized)
SELECT d.department,
       CASE WHEN CAST(o.order_hour_of_day AS INTEGER) BETWEEN 5 AND 11 THEN 'Morning'
            WHEN CAST(o.order_hour_of_day AS INTEGER) BETWEEN 12 AND 16 THEN 'Afternoon'
            WHEN CAST(o.order_hour_of_day AS INTEGER) BETWEEN 17 AND 21 THEN 'Evening'
            ELSE 'Night' END AS part_of_day,
       COUNT(*) AS items
FROM stg_op op
JOIN stg_orders o USING (order_id)
JOIN stg_products p ON op.product_id = p.product_id
JOIN stg_departments d ON p.department_id = d.department_id
GROUP BY CUBE (d.department, part_of_day);

-- C2 (Galaxy)
SELECT p.department, t.part_of_day, COUNT(*) AS items
FROM fact_order_items f
JOIN dim_product p USING (product_key)
JOIN dim_time t USING (time_key)
GROUP BY CUBE (p.department, t.part_of_day);

-- C3 (Columnar Parquet)
SELECT p.department, t.part_of_day, COUNT(*) AS items
FROM 'data/warehouse/fact_order_items.parquet' f
JOIN 'data/warehouse/dim_product.parquet' p ON f.product_key = p.product_key
JOIN 'data/warehouse/dim_time.parquet' t ON f.time_key = t.time_key
GROUP BY CUBE (p.department, t.part_of_day);

-- C4 (Pre-Aggregated Cube)
SELECT department,
       CASE WHEN hour BETWEEN 5 AND 11 THEN 'Morning'
            WHEN hour BETWEEN 12 AND 16 THEN 'Afternoon'
            WHEN hour BETWEEN 17 AND 21 THEN 'Evening'
            ELSE 'Night' END AS part_of_day,
       SUM(items) AS items
FROM cube_dept_time
GROUP BY CUBE (department, part_of_day);


-- ----------------------------------------------------------------------------
-- Q6: Customer Profile Aggregate (Orders and Items per Customer)
-- ----------------------------------------------------------------------------
-- C1 (Normalized)
SELECT o.user_id, COUNT(DISTINCT o.order_id) AS total_orders, COUNT(op.product_id) AS total_items
FROM stg_orders o
JOIN stg_op op USING (order_id)
GROUP BY o.user_id
LIMIT 50;

-- C2 (Galaxy)
SELECT customer_key, total_orders, total_items
FROM dim_customer
LIMIT 50;

-- C3 (Columnar Parquet)
SELECT customer_key, total_orders, total_items
FROM 'data/warehouse/dim_customer.parquet'
LIMIT 50;
