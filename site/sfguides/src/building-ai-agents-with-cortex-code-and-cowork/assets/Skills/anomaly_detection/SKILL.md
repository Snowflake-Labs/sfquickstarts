---
name: anomaly_detection
description: Detect anomalies in hot food sales data. Use this skill when the user asks about unusual patterns, spikes, drops, outliers, or unexpected changes in revenue, quantity sold, or transaction counts across stores, categories, states, or items.
---

# Anomaly Detection

Identify statistically unusual sales patterns using z-score analysis over a 7-day rolling window.

## When to Use

- User asks about unusual sales patterns, spikes, or drops
- User wants to find outliers in revenue, quantity, or transactions
- User asks "what's abnormal", "anything unusual", "anomalies"
- User asks about sudden changes in performance for a store, category, or state

## Instructions

When this skill is invoked, follow these steps:

### Step 1: Determine Parameters

Extract from the user's question:

- **Dimension**: What to group by. One of: `STORE` (store name), `CATEGORY` (food category), `STATE` (state code), `ITEM` (item name). Default: `CATEGORY`
- **Metric**: What to measure. One of: `REVENUE` (total_sales), `QUANTITY` (quantity_sold), `TRANSACTIONS` (distinct sale count). Default: `REVENUE`
- **Sensitivity**: Z-score threshold. Higher = fewer anomalies. Default: `2.0` (standard). Use `1.5` for "any unusual pattern" and `2.5` for "only extreme outliers"

If the user is vague, default to CATEGORY + REVENUE + sensitivity 2.0.

### Step 2: Run Anomaly Detection Query

Execute this SQL with the appropriate dimension, metric, and sensitivity values:

```sql
WITH daily_metrics AS (
    SELECT
        f.SALE_DATE,
        {DIMENSION_EXPRESSION} AS dimension_value,
        {METRIC_EXPRESSION} AS metric_value
    FROM HOL_COCO_COWORK.DATA.FACT_ITEM_SALES f
    JOIN HOL_COCO_COWORK.DATA.DIM_STORE s ON f.STORE_ID = s.STORE_ID
    JOIN HOL_COCO_COWORK.DATA.DIM_ITEM i ON f.ITEM_ID = i.ITEM_ID
    GROUP BY f.SALE_DATE, dimension_value
),
stats AS (
    SELECT
        SALE_DATE,
        dimension_value,
        metric_value,
        AVG(metric_value) OVER (
            PARTITION BY dimension_value ORDER BY SALE_DATE
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS rolling_avg,
        STDDEV(metric_value) OVER (
            PARTITION BY dimension_value ORDER BY SALE_DATE
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS rolling_std
    FROM daily_metrics
)
SELECT
    SALE_DATE,
    dimension_value,
    ROUND(metric_value, 2) AS metric_value,
    ROUND(rolling_avg, 2) AS rolling_avg,
    ROUND((metric_value - rolling_avg) / NULLIF(rolling_std, 0), 2) AS z_score,
    CASE
        WHEN (metric_value - rolling_avg) / NULLIF(rolling_std, 0) > {SENSITIVITY} THEN 'SPIKE'
        WHEN (metric_value - rolling_avg) / NULLIF(rolling_std, 0) < -{SENSITIVITY} THEN 'DROP'
        ELSE 'NORMAL'
    END AS anomaly_type
FROM stats
WHERE rolling_std > 0
  AND ABS((metric_value - rolling_avg) / rolling_std) > {SENSITIVITY}
ORDER BY ABS(z_score) DESC
LIMIT 20;
```

**Dimension expressions:**
- STORE: `s.STORE_NAME`
- CATEGORY: `i.CATEGORY`
- STATE: `s.STATE`
- ITEM: `i.ITEM_NAME`

**Metric expressions:**
- REVENUE: `SUM(f.TOTAL_SALES)`
- QUANTITY: `SUM(f.QUANTITY_SOLD)`
- TRANSACTIONS: `COUNT(DISTINCT f.SALE_ID)`

### Step 3: Present Results

Format the response as:

1. **Summary**: "Found X anomalies (Y spikes, Z drops) in {metric} by {dimension}"
2. **Top anomalies table**: Show date, dimension value, actual vs expected, z-score, and type (SPIKE/DROP)
3. **Insight**: Explain the most significant anomaly in plain language

If no anomalies are found, say so and suggest lowering sensitivity to 1.5.
