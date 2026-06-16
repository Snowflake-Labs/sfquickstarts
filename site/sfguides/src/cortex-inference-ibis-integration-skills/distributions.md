# Shannon Entropy & Distribution Analysis Reference

Functions in `cortex_ibis.py` section 10. Use to measure category diversity per group.

## Intuition

Shannon entropy quantifies how unpredictable a distribution is:

| H (bits) | Meaning for 4-category reviews |
|---|---|
| 2.0 | Perfectly uniform — equal spread across billing/delivery/defect/positive |
| 1.0–1.9 | Mixed — 2–3 categories dominant |
| 0.3–1.0 | Concentrated — one category dominates (~70–90%) |
| 0.0 | Single category — 100% of reviews in one bucket |

**Product insight**: high-entropy products need broad support coverage; low-entropy products have a focused root cause.

## category_entropy() — pure SQL via Ibis

```python
from cortex_ibis import category_entropy

# Input: any Ibis table with a group col and a category col
# (e.g. output of add_classification())
classified = add_classification(reviews_tbl, "body",
                                ["billing issue", "delivery problem",
                                 "product defect", "positive feedback"])

entropy_tbl = category_entropy(
    classified,
    group_cols=["product_id"],
    category_col="category",
)
# → product_id | entropy | dominant_category | dominant_share
# Ordered by entropy ASC (lowest = most concentrated)

# Preview SQL before running
print(ibis.to_sql(entropy_tbl, dialect="snowflake"))

# Execute
df = entropy_tbl.execute()
```

## normalized_entropy() — [0, 1] scale

```python
from cortex_ibis import normalized_entropy

norm_tbl = normalized_entropy(
    classified,
    group_cols=["product_id"],
    category_col="category",
    num_categories=4,       # must match the actual number of distinct labels
)
# Adds 'normalized_entropy' column: 0.0 = single class, 1.0 = perfectly uniform
```

## entropy_from_pandas() — scipy path

```python
from cortex_ibis import entropy_from_pandas

# From raw rows
result = entropy_from_pandas(df, group_col="product_id", category_col="true_category")

# From pre-aggregated counts
counts_df = df.groupby(["product_id", "category"]).size().reset_index(name="n")
result = entropy_from_pandas(counts_df, "product_id", "category", count_col="n")

# Returns: product_id | entropy | normalized_entropy | dominant_category | dominant_share
```

## Synthetic Dataset

`synthetic_data.py` generates 300 reviews across 8 products with controlled Dirichlet distributions:

```python
from synthetic_data import make_reviews, distribution_summary

df = make_reviews(seed=42)                # 300 rows: id, product_id, body, true_category
summary = distribution_summary(df)       # pivot with per-product counts + true_entropy_bits
```

| Product | Profile | True H |
|---|---|---|
| P001 | Uniform | ~2.00 bits |
| P002 | 90% product defect | ~0.47 bits |
| P003 | Bimodal billing+delivery | ~1.0 bits |
| P004 | All positive | ~0.0 bits |
| P005 | Bimodal delivery+defect | ~1.0 bits |
| P006 | Slight positive skew | ~1.9 bits |
| P007 | 90% billing | ~0.47 bits |
| P008 | Trimodal billing/delivery/defect | ~1.58 bits |

## Miller–Madow Bias Note

Sample entropy underestimates true entropy for small n. The gap shrinks as n grows:
- n=30 → sample H can be 0.2–0.6 bits below true H
- n=300+ → gap < 0.05 bits typically

Use `distribution_summary(df)` to compare true vs sample entropy on the synthetic dataset.

## Full Demo

```python
python distribution_demo.py
# Prints rich entropy table + ASCII bar chart + exports assets/s_entropy.svg
```
