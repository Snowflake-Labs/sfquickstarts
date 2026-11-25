---
name: sales_report
description: Generate a comprehensive sales report by store or by state. Use this skill when the user asks for a sales report, performance summary, store report, state report, executive summary, or full analysis of a specific store or state.
---

# Sales Report Generator

Generate a structured executive sales report with top products, trends, missed opportunities, and recommended actions.

## When to Use

- User asks for a "sales report" or "performance report"
- User asks for analysis of a specific store or state
- User asks for an "executive summary" or "full breakdown"
- User mentions "report for [store name]" or "report for [state]"

## Instructions

### Step 1: Determine Report Scope

Extract from the user's question:

- **Report Type**: `STORE` (single store) or `STATE` (single state)
- **Filter Value**: The specific store name or state code

If the user says "by store" without naming one, ask which store. If they say "by state" without naming one, ask which state.

### Step 2: Run Report Queries

Execute the following queries sequentially, substituting the appropriate filter.

**For STORE reports**, use: `WHERE s.STORE_NAME = '{STORE_NAME}'`
**For STATE reports**, use: `WHERE s.STATE = '{STATE_CODE}'`

#### Query 1: Summary Metrics

```sql
SELECT
    COUNT(DISTINCT f.SALE_ID) AS total_transactions,
    ROUND(SUM(f.TOTAL_SALES), 2) AS total_revenue,
    ROUND(AVG(f.TOTAL_SALES), 2) AS avg_transaction_value,
    SUM(f.QUANTITY_SOLD) AS total_units_sold,
    COUNT(DISTINCT f.SALE_DATE) AS active_days,
    ROUND(AVG(f.DISCOUNT_PCT), 1) AS avg_discount_pct
FROM HOL_COCO_COWORK.DATA.FACT_ITEM_SALES f
JOIN HOL_COCO_COWORK.DATA.DIM_STORE s ON f.STORE_ID = s.STORE_ID
{WHERE_CLAUSE};
```

#### Query 2: Top 10 Products by Revenue

```sql
SELECT
    i.ITEM_NAME,
    i.CATEGORY,
    SUM(f.TOTAL_SALES) AS revenue,
    SUM(f.QUANTITY_SOLD) AS units_sold,
    ROUND(AVG(f.DISCOUNT_PCT), 1) AS avg_discount
FROM HOL_COCO_COWORK.DATA.FACT_ITEM_SALES f
JOIN HOL_COCO_COWORK.DATA.DIM_STORE s ON f.STORE_ID = s.STORE_ID
JOIN HOL_COCO_COWORK.DATA.DIM_ITEM i ON f.ITEM_ID = i.ITEM_ID
{WHERE_CLAUSE}
GROUP BY i.ITEM_NAME, i.CATEGORY
ORDER BY revenue DESC
LIMIT 10;
```

#### Query 3: Monthly Revenue Trend

```sql
SELECT
    DATE_TRUNC('MONTH', f.SALE_DATE) AS month,
    ROUND(SUM(f.TOTAL_SALES), 2) AS revenue,
    SUM(f.QUANTITY_SOLD) AS units,
    COUNT(DISTINCT f.SALE_ID) AS transactions
FROM HOL_COCO_COWORK.DATA.FACT_ITEM_SALES f
JOIN HOL_COCO_COWORK.DATA.DIM_STORE s ON f.STORE_ID = s.STORE_ID
{WHERE_CLAUSE}
GROUP BY month
ORDER BY month;
```

#### Query 4: Category Performance (for missed opportunities)

```sql
SELECT
    i.CATEGORY,
    ROUND(SUM(f.TOTAL_SALES), 2) AS revenue,
    SUM(f.QUANTITY_SOLD) AS units_sold,
    ROUND(AVG(f.DISCOUNT_PCT), 1) AS avg_discount,
    COUNT(DISTINCT i.ITEM_ID) AS unique_items_sold
FROM HOL_COCO_COWORK.DATA.FACT_ITEM_SALES f
JOIN HOL_COCO_COWORK.DATA.DIM_STORE s ON f.STORE_ID = s.STORE_ID
JOIN HOL_COCO_COWORK.DATA.DIM_ITEM i ON f.ITEM_ID = i.ITEM_ID
{WHERE_CLAUSE}
GROUP BY i.CATEGORY
ORDER BY revenue DESC;
```

#### Query 5: Underperforming Categories (compare to chain average)

```sql
WITH store_cat AS (
    SELECT i.CATEGORY, ROUND(SUM(f.TOTAL_SALES), 2) AS local_revenue
    FROM HOL_COCO_COWORK.DATA.FACT_ITEM_SALES f
    JOIN HOL_COCO_COWORK.DATA.DIM_STORE s ON f.STORE_ID = s.STORE_ID
    JOIN HOL_COCO_COWORK.DATA.DIM_ITEM i ON f.ITEM_ID = i.ITEM_ID
    {WHERE_CLAUSE}
    GROUP BY i.CATEGORY
),
chain_avg AS (
    SELECT i.CATEGORY, ROUND(AVG(store_revenue), 2) AS avg_revenue
    FROM (
        SELECT s.STORE_ID, i.CATEGORY, SUM(f.TOTAL_SALES) AS store_revenue
        FROM HOL_COCO_COWORK.DATA.FACT_ITEM_SALES f
        JOIN HOL_COCO_COWORK.DATA.DIM_STORE s ON f.STORE_ID = s.STORE_ID
        JOIN HOL_COCO_COWORK.DATA.DIM_ITEM i ON f.ITEM_ID = i.ITEM_ID
        GROUP BY s.STORE_ID, i.CATEGORY
    ) sub
    GROUP BY i.CATEGORY
)
SELECT
    c.CATEGORY,
    COALESCE(sc.local_revenue, 0) AS local_revenue,
    c.avg_revenue AS chain_avg_revenue,
    ROUND(((COALESCE(sc.local_revenue, 0) - c.avg_revenue) / NULLIF(c.avg_revenue, 0)) * 100, 1) AS pct_vs_avg
FROM chain_avg c
LEFT JOIN store_cat sc ON c.CATEGORY = sc.CATEGORY
ORDER BY pct_vs_avg ASC
LIMIT 5;
```

### Step 3: Compile and Present Report

Structure the output as a formatted executive report:

```
# Sales Report: {Store Name / State}
## Period: January - March 2025

---

## Executive Summary
- Total Revenue: ${total_revenue}
- Total Transactions: {total_transactions}
- Average Transaction Value: ${avg_transaction_value}
- Total Units Sold: {total_units_sold}
- Average Discount: {avg_discount_pct}%

---

## Top 10 Products by Revenue
[Table: Item Name | Category | Revenue | Units Sold | Avg Discount]

---

## Monthly Trend
[Table: Month | Revenue | Units | Transactions]
[Insight: Which month was strongest/weakest and % change]

---

## Missed Opportunities
[Categories where this store/state underperforms vs chain average]
- {Category}: {pct_vs_avg}% below chain average (${gap} in unrealized revenue)

---

## Recommended Actions
Based on the data:
1. [Action based on underperforming categories]
2. [Action based on discount patterns]
3. [Action based on trend direction]
```

### Guidelines for Missed Opportunities

- A category is a "missed opportunity" if its revenue is >20% below the chain average
- Quantify the gap in dollars: `chain_avg_revenue - local_revenue`
- Focus on categories with high chain averages (large addressable opportunity)

### Guidelines for Recommended Actions

Generate 3 actionable recommendations based on:
1. **Product mix**: If top categories here differ from chain average, suggest stocking adjustments
2. **Discount strategy**: If avg discount is significantly higher/lower than chain, suggest optimization
3. **Trend momentum**: If revenue is declining month-over-month, suggest promotional activity; if growing, suggest doubling down
