-- ============================================================================
-- DWM E-Commerce Warehouse: OLAP Analytical Queries (Week 3)
-- Demonstrating Multidimensional Operations: Roll-up, Drill-down, Slice, Dice,
-- Pivot, CUBE, and GROUPING SETS on 33.8M+ Rows
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. ROLL-UP: Hierarchical Aggregation (Product -> Aisle -> Department -> Grand Total)
-- ----------------------------------------------------------------------------
-- Department + Aisle roll-up computes subtotals per department and a grand total.
-- NULL aisle represents department subtotal; both NULL represents grand total.
SELECT 
    COALESCE(p.department, 'ALL DEPARTMENTS') AS department,
    COALESCE(p.aisle, 'ALL AISLES (SUBTOTAL)') AS aisle,
    COUNT(*) AS items_sold,
    ROUND(AVG(f.reordered) * 100, 2) AS reorder_rate_pct
FROM fact_order_items f
JOIN dim_product p USING (product_key)
GROUP BY ROLLUP (p.department, p.aisle)
ORDER BY p.department NULLS LAST, p.aisle NULLS LAST;

-- ----------------------------------------------------------------------------
-- 2. DRILL-DOWN: Moving Down Hierarchical Levels
-- ----------------------------------------------------------------------------

-- Level 1: Macro overview by Department
SELECT 
    p.department, 
    COUNT(*) AS items_sold,
    ROUND(AVG(f.reordered) * 100, 2) AS reorder_rate_pct
FROM fact_order_items f
JOIN dim_product p USING (product_key)
GROUP BY p.department
ORDER BY items_sold DESC;

-- Level 2: Drill down into top department ('produce') by Aisle
SELECT 
    p.aisle, 
    COUNT(*) AS items_sold,
    ROUND(AVG(f.reordered) * 100, 2) AS reorder_rate_pct
FROM fact_order_items f
JOIN dim_product p USING (product_key)
WHERE p.department = 'produce'
GROUP BY p.aisle
ORDER BY items_sold DESC;

-- Level 3: Drill down into specific aisle ('fresh fruits') by Product
SELECT 
    p.product_name, 
    COUNT(*) AS items_sold,
    ROUND(AVG(f.reordered) * 100, 2) AS reorder_rate_pct
FROM fact_order_items f
JOIN dim_product p USING (product_key)
WHERE p.aisle = 'fresh fruits'
GROUP BY p.product_name
ORDER BY items_sold DESC
LIMIT 20;

-- Time Dimension Drill-Down: Part of Day -> Specific Hour
SELECT 
    COALESCE(t.part_of_day, 'ALL DAY') AS part_of_day,
    COALESCE(CAST(t.hour AS VARCHAR), 'SUBTOTAL') AS hour,
    COUNT(*) AS total_orders
FROM fact_orders o
JOIN dim_time t USING (time_key)
GROUP BY ROLLUP (t.part_of_day, t.hour)
ORDER BY t.part_of_day NULLS LAST, t.hour NULLS LAST;

-- ----------------------------------------------------------------------------
-- 3. SLICE: Fixing a Single Dimension Value (Weekend Orders)
-- ----------------------------------------------------------------------------
-- Filtering solely by time slice: is_weekend = TRUE
SELECT 
    p.department, 
    COUNT(*) AS weekend_items_sold,
    ROUND(AVG(f.reordered) * 100, 2) AS weekend_reorder_rate_pct
FROM fact_order_items f
JOIN dim_product p USING (product_key)
JOIN dim_time t USING (time_key)
WHERE t.is_weekend = TRUE
GROUP BY p.department
ORDER BY weekend_items_sold DESC;

-- ----------------------------------------------------------------------------
-- 4. DICE: Sub-cube Restricting Multiple Dimensions
-- ----------------------------------------------------------------------------
-- Department restricted to ('produce', 'dairy eggs')
-- Time restricted to weekend mornings (is_weekend = TRUE AND hour BETWEEN 8 AND 12)
SELECT 
    p.department,
    t.part_of_day,
    t.hour,
    COUNT(*) AS items_sold,
    ROUND(AVG(f.reordered) * 100, 2) AS reorder_rate_pct
FROM fact_order_items f
JOIN dim_product p USING (product_key)
JOIN dim_time t USING (time_key)
WHERE p.department IN ('produce', 'dairy eggs')
  AND t.is_weekend = TRUE
  AND t.hour BETWEEN 8 AND 12
GROUP BY p.department, t.part_of_day, t.hour
ORDER BY p.department, t.hour;

-- ----------------------------------------------------------------------------
-- 5. PIVOT: Cross-Tabulation (Department x Day of Week)
-- ----------------------------------------------------------------------------
SELECT 
    p.department,
    SUM(CASE WHEN t.order_dow = 0 THEN 1 ELSE 0 END) AS day_0_weekend,
    SUM(CASE WHEN t.order_dow = 1 THEN 1 ELSE 0 END) AS day_1_weekend,
    SUM(CASE WHEN t.order_dow = 2 THEN 1 ELSE 0 END) AS day_2_weekday,
    SUM(CASE WHEN t.order_dow = 3 THEN 1 ELSE 0 END) AS day_3_weekday,
    SUM(CASE WHEN t.order_dow = 4 THEN 1 ELSE 0 END) AS day_4_weekday,
    SUM(CASE WHEN t.order_dow = 5 THEN 1 ELSE 0 END) AS day_5_weekday,
    SUM(CASE WHEN t.order_dow = 6 THEN 1 ELSE 0 END) AS day_6_weekday,
    COUNT(*) AS total_items
FROM fact_order_items f
JOIN dim_product p USING (product_key)
JOIN dim_time t USING (time_key)
GROUP BY p.department
ORDER BY total_items DESC;

-- ----------------------------------------------------------------------------
-- 6. CUBE: Multi-Dimensional Cross-Combination Aggregation
-- ----------------------------------------------------------------------------
-- Generates 2^N combinations for (department, part_of_day)
SELECT 
    COALESCE(p.department, 'ALL DEPARTMENTS') AS department,
    COALESCE(t.part_of_day, 'ALL PARTS OF DAY') AS part_of_day,
    COUNT(*) AS items_sold
FROM fact_order_items f
JOIN dim_product p USING (product_key)
JOIN dim_time t USING (time_key)
WHERE p.department IN ('produce', 'dairy eggs', 'beverages')
GROUP BY CUBE (p.department, t.part_of_day)
ORDER BY p.department NULLS LAST, t.part_of_day NULLS LAST;

-- ----------------------------------------------------------------------------
-- 7. GROUPING SETS: Selective Multi-Level Aggregations
-- ----------------------------------------------------------------------------
SELECT 
    COALESCE(p.department, 'ALL DEPARTMENTS') AS department,
    CASE 
        WHEN t.is_weekend IS NULL THEN 'ALL DAYS'
        WHEN t.is_weekend THEN 'Weekend'
        ELSE 'Weekday'
    END AS day_type,
    COUNT(*) AS items_sold,
    ROUND(AVG(f.reordered) * 100, 2) AS reorder_rate_pct
FROM fact_order_items f
JOIN dim_product p USING (product_key)
JOIN dim_time t USING (time_key)
WHERE p.department IN ('produce', 'dairy eggs', 'snacks')
GROUP BY GROUPING SETS (
    (p.department, t.is_weekend),
    (p.department),
    (t.is_weekend),
    ()
)
ORDER BY p.department NULLS LAST, day_type NULLS LAST;
