"""
synthetic_data.py — Controlled synthetic customer review dataset for distribution analysis.

Generates 300 reviews across 8 products with Dirichlet-controlled category distributions,
designed to demonstrate Shannon entropy analysis with cortex_ibis.

Products are engineered with distinct entropy profiles:

  P001  Uniform across all 4 categories         → H ≈ 2.00 bits  (max entropy)
  P002  90% product defect                       → H ≈ 0.47 bits  (very concentrated)
  P003  Bimodal: billing + delivery              → H ≈ 1.00 bits
  P004  All positive feedback                    → H ≈ 0.00 bits  (single class)
  P005  Bimodal: delivery + defect               → H ≈ 1.00 bits
  P006  Slight skew: mostly support issues       → H ≈ 1.52 bits
  P007  90% billing, 10% other                   → H ≈ 0.47 bits
  P008  Trimodal: billing / delivery / defect    → H ≈ 1.58 bits

Usage:
    from synthetic_data import make_reviews
    df = make_reviews(seed=42)
    # → pd.DataFrame with columns: id, product_id, body, true_category
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Optional

# ──────────────────────────────────────────────────────────────────────────────
# Category pools — realistic review text per category
# ──────────────────────────────────────────────────────────────────────────────

CATEGORIES = ["billing issue", "delivery problem", "product defect", "positive feedback"]

_POOL: dict[str, list[str]] = {
    "billing issue": [
        "I was charged twice for the same order. Please refund one payment immediately.",
        "My credit card was billed the wrong amount. The invoice shows a different total.",
        "I never received a receipt and my account shows a duplicate charge.",
        "The discount code was applied but I was still charged full price. Please fix.",
        "I requested a refund two weeks ago and the money has not appeared in my account.",
        "The auto-renewal charged me without any prior notice or warning.",
        "I was charged for an item I returned. The refund was never processed.",
        "There is an unexplained charge on my statement I did not authorise.",
        "Got store credit instead of the cash refund I explicitly requested.",
        "Billing address was wrong and now the charge is flagged. Very frustrating.",
    ],
    "delivery problem": [
        "My order arrived three weeks late with no updates from the courier.",
        "The tracking number provided never worked. I have no idea where my package is.",
        "Item was left outside in the rain and everything was completely soaked.",
        "Package marked as delivered but nothing arrived at my address.",
        "Wrong item was delivered. I ordered a blue one and received red.",
        "Delivery took six weeks. No communication at all from the seller.",
        "The courier attempted delivery when I was home but left no notice.",
        "Order was split across three shipments that arrived on different days.",
        "Packaging was completely destroyed. Looks like it was dropped multiple times.",
        "The estimated delivery date changed four times without explanation.",
    ],
    "product defect": [
        "The item arrived broken. The screen cracked straight out of the box.",
        "Defective unit — the USB port does not work at all.",
        "The product stopped working after two days of normal use.",
        "Advertised as waterproof but it broke after light rain.",
        "The zipper broke on first use. Very poor quality materials.",
        "Battery does not hold charge for more than an hour.",
        "The power button sticks and the device randomly turns off.",
        "Paint is already chipping after one week. Extremely poor finish.",
        "Seams came apart on first wash. Clearly a manufacturing defect.",
        "The product emits a burning smell when plugged in. Safety hazard.",
    ],
    "positive feedback": [
        "Shipped fast and the product works exactly as described. Very happy.",
        "Best purchase I have made this year. Exceeds every expectation.",
        "Outstanding build quality and the price is very reasonable.",
        "Customer support resolved my question in minutes. Outstanding service.",
        "Simple setup, intuitive interface — my kids love it.",
        "Great value for money. Arrived ahead of schedule in perfect condition.",
        "Impressed by the attention to detail. Premium feel for the price.",
        "Smooth checkout, arrived on time, everything exactly as pictured.",
        "Solid build quality and does exactly what it says on the box.",
        "Fantastic product. Will definitely buy again and recommend to friends.",
    ],
}

# ──────────────────────────────────────────────────────────────────────────────
# Product distribution configurations
# ──────────────────────────────────────────────────────────────────────────────
# Each tuple: (product_id, n_reviews, Dirichlet alpha for [billing, delivery, defect, positive])
# Higher alpha → more weight on that category. Equal alphas → uniform.

_PRODUCT_CONFIGS: list[tuple[str, int, list[float]]] = [
    ("P001", 40, [1.0, 1.0, 1.0, 1.0]),       # uniform          H ≈ 2.00
    ("P002", 40, [0.5, 0.5, 9.0, 0.5]),        # 90% defect       H ≈ 0.47
    ("P003", 40, [4.5, 4.5, 0.5, 0.5]),        # bimodal billing+delivery  H ≈ 1.00
    ("P004", 30, [0.1, 0.1, 0.1, 9.7]),        # all positive     H ≈ 0.00
    ("P005", 40, [0.5, 4.5, 4.5, 0.5]),        # bimodal delivery+defect   H ≈ 1.00
    ("P006", 30, [2.0, 2.0, 2.0, 4.0]),        # slight skew positive H ≈ 1.96
    ("P007", 40, [9.0, 0.5, 0.5, 0.5]),        # 90% billing      H ≈ 0.47
    ("P008", 40, [3.5, 3.5, 3.5, 0.5]),        # trimodal         H ≈ 1.58
]


def _expected_entropy(alpha: list[float]) -> float:
    """Compute expected Shannon entropy (bits) of a Dirichlet(alpha) distribution."""
    a = np.array(alpha, dtype=float)
    p = a / a.sum()
    p = p[p > 0]
    return float(-np.sum(p * np.log2(p)))


def make_reviews(seed: int = 42) -> pd.DataFrame:
    """
    Generate the full synthetic review dataset.

    Returns
    -------
    pd.DataFrame with columns:
        id            int   — unique row id
        product_id    str   — P001..P008
        body          str   — review text
        true_category str   — ground-truth category label (for benchmarking Cortex AI)
    """
    rng = np.random.default_rng(seed)
    rows: list[dict] = []
    row_id = 1

    for product_id, n_reviews, alpha in _PRODUCT_CONFIGS:
        # Sample category probabilities from Dirichlet (one draw per product)
        probs = rng.dirichlet(alpha)
        # Sample n_reviews category indices from the distribution
        cat_indices = rng.choice(len(CATEGORIES), size=n_reviews, p=probs)

        for cat_idx in cat_indices:
            category = CATEGORIES[cat_idx]
            pool = _POOL[category]
            text = pool[rng.integers(len(pool))]
            rows.append({
                "id":            row_id,
                "product_id":    product_id,
                "body":          text,
                "true_category": category,
            })
            row_id += 1

    df = pd.DataFrame(rows)
    return df


def distribution_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Show per-product category counts + true Shannon entropy.

    Returns a DataFrame with:
        product_id, billing_issue, delivery_problem, product_defect,
        positive_feedback, total, true_entropy_bits, normalized_entropy
    """
    pivot = (
        df.groupby(["product_id", "true_category"])
        .size()
        .unstack(fill_value=0)
        .rename(columns=lambda c: c.replace(" ", "_"))
    )
    pivot["total"] = pivot.sum(axis=1)

    def _entropy(row: pd.Series) -> float:
        counts = row[[c for c in pivot.columns if c != "total"]].values.astype(float)
        p = counts / counts.sum()
        p = p[p > 0]
        return float(-np.sum(p * np.log2(p)))

    pivot["true_entropy_bits"] = pivot.apply(_entropy, axis=1)
    n_cats = len(CATEGORIES)
    pivot["normalized_entropy"] = pivot["true_entropy_bits"] / np.log2(n_cats)
    return pivot.reset_index()


if __name__ == "__main__":
    df = make_reviews()
    summary = distribution_summary(df)
    print(f"Total reviews: {len(df)}")
    print("\nPer-product distribution + entropy:")
    print(summary.to_string(index=False, float_format="{:.3f}".format))
    print("\nExpected entropy per config:")
    for pid, n, alpha in _PRODUCT_CONFIGS:
        print(f"  {pid}  α={alpha}  → H_expected={_expected_entropy(alpha):.3f} bits")
