"""
Cortex Code Credit Manager - Intelligence Engine v3
=====================================================
EWMA-based trend prediction with smart donor selection strategies.
Admin-configurable via CC_APP_CONFIG.

Donor Selection Strategies:
  HIGHEST_SURPLUS   - Always take from donor with most surplus (safest)
  WEIGHTED_RANDOM   - Probability proportional to surplus (distributes load fairly)
  MINIMUM_DONORS    - Tries to satisfy from fewest donors (single-donor preferred)
  ROUND_ROBIN       - Skips recent donors, rotates across cohort (most equitable)

v3 changes:
  - True per-hour EWMA (pandas ewm, alpha=0.3) instead of simple mean
  - Cold-start guard: users with < MIN_HISTORY_DAYS treated as zero-surplus
  - MINIMUM_DONORS: prefers single-donor fulfillment before falling back to greedy
  - Fixed off-by-one in current_hour check
"""

import random
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from config import (
    REBALANCE_DEFAULT_BUFFER_PCT,
    REBALANCE_DEFAULT_LOOKBACK_DAYS,
    REBALANCE_DEFAULT_MAX_TRANSFER_PCT,
)

# Default strategy if not configured
DEFAULT_DONOR_STRATEGY = "WEIGHTED_RANDOM"
DEFAULT_DONOR_PROTECTION_HOURS = 4   # Skip donors who gave in last N hours

# Minimum days of hourly history needed for reliable EWMA prediction.
# Users below this threshold are treated as fully consuming their remaining limit
# (i.e., transferable = 0) — prevents new users from being donors.
MIN_HISTORY_DAYS = 5

# EWMA decay factor: alpha=0.3 means roughly the last 3-4 days dominate
EWMA_ALPHA = 0.3


def _ewma_per_hour(
    df: pd.DataFrame,
    remaining_hours: List[int],
) -> pd.Series:
    """
    Compute per-hour EWMA over historical observations.

    For each hour in `remaining_hours`, collect all past observations at
    that hour (sorted chronologically) and apply exponential weighting so
    that more-recent days contribute more to the prediction.

    Args:
        df: DataFrame with USAGE_HOUR and TOTAL_CREDITS columns, sorted ascending.
        remaining_hours: List of hours still to occur today.

    Returns:
        pd.Series indexed by hour with predicted credit usage for that hour.
    """
    result = {}
    for h in remaining_hours:
        obs = (
            df[df["USAGE_HOUR"] == h]
            .sort_values("USAGE_DATE")["TOTAL_CREDITS"]
        )
        if obs.empty:
            result[h] = 0.0
        elif len(obs) == 1:
            result[h] = float(obs.iloc[0])
        else:
            # ewm with adjust=True: each observation weighted by (1-alpha)^k
            # where k is the number of positions from the end (0 = most recent)
            result[h] = float(obs.ewm(alpha=EWMA_ALPHA, adjust=True).mean().iloc[-1])
    return pd.Series(result)


def predict_rest_of_day_usage(
    hourly_df: pd.DataFrame,
    user_name: str,
    surface: str,
    current_hour: int,
    lookback_days: int = REBALANCE_DEFAULT_LOOKBACK_DAYS,
) -> float:
    """
    Predict total credits a user will consume for the remaining hours today.

    Returns 0.0 if:
    - no historical data for this user/surface
    - current_hour is already the last hour of the day (no remaining hours)

    NOTE: Cold-start (< MIN_HISTORY_DAYS) is handled upstream in
    calculate_cohort_surplus — callers of this function should already
    have filtered such users out.
    """
    remaining_hours = list(range(current_hour + 1, 24))
    if not remaining_hours:
        return 0.0

    if hourly_df.empty:
        return 0.0

    udf = hourly_df[
        (hourly_df["USER_NAME"] == user_name) & (hourly_df["SURFACE"] == surface)
    ].copy()

    if udf.empty:
        return 0.0

    # Baseline EWMA across all days for remaining hours
    hourly_avg = _ewma_per_hour(udf, remaining_hours)

    if hourly_avg.empty:
        return 0.0

    # Day-of-week adjustment: recent same-weekday observations are blended in
    today_dow = datetime.utcnow().weekday()
    if "USAGE_DATE" in udf.columns:
        udf["DOW"] = pd.to_datetime(udf["USAGE_DATE"]).dt.weekday
        same_dow = udf[udf["DOW"] == today_dow]
        if len(same_dow) >= 3:
            dow_ewma = _ewma_per_hour(same_dow, remaining_hours)
            if not dow_ewma.empty:
                # 40% overall EWMA, 60% same-weekday EWMA
                hourly_avg = (
                    hourly_avg * 0.4
                    + dow_ewma.reindex(hourly_avg.index, fill_value=0) * 0.6
                )

    return max(float(hourly_avg.sum()), 0.0)


def calculate_cohort_surplus(
    hourly_df: pd.DataFrame,
    cohort_members: List[str],
    surface: str,
    current_limits: Dict[str, float],
    today_usage: Dict[str, float],
    buffer_pct: int = REBALANCE_DEFAULT_BUFFER_PCT,
    max_transfer_pct: int = REBALANCE_DEFAULT_MAX_TRANSFER_PCT,
    lookback_days: int = REBALANCE_DEFAULT_LOOKBACK_DAYS,
    recent_donors: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    current_hour = datetime.utcnow().hour
    recent_donors = recent_donors or []
    results = []

    for user in cohort_members:
        limit = current_limits.get(user, 0)
        used = today_usage.get(user, 0)

        # --- Cold-start guard ---
        # Users with insufficient history are assumed to use all remaining credits
        # so their surplus = 0 and they are never selected as donors.
        unique_dates = 0
        if not hourly_df.empty and "USAGE_DATE" in hourly_df.columns:
            user_data = hourly_df[
                (hourly_df["USER_NAME"] == user) & (hourly_df["SURFACE"] == surface)
            ]
            unique_dates = user_data["USAGE_DATE"].nunique()

        if unique_dates < MIN_HISTORY_DAYS:
            results.append({
                "user": user,
                "limit": limit,
                "used_today": used,
                "predicted_remaining": max(limit - used, 0),
                "total_predicted": limit,
                "raw_surplus": 0,
                "safe_surplus": 0,
                "transferable": 0,
                "recently_donated": user in recent_donors,
                "cold_start": True,
            })
            continue

        predicted_remaining = predict_rest_of_day_usage(
            hourly_df, user, surface, current_hour, lookback_days
        )

        total_predicted = used + predicted_remaining
        raw_surplus = limit - total_predicted

        buffer = limit * (buffer_pct / 100.0)
        safe_surplus = max(raw_surplus - buffer, 0)

        max_cap = limit * (max_transfer_pct / 100.0)
        transferable = min(safe_surplus, max_cap)

        results.append({
            "user": user,
            "limit": limit,
            "used_today": used,
            "predicted_remaining": round(predicted_remaining, 2),
            "total_predicted": round(total_predicted, 2),
            "raw_surplus": round(raw_surplus, 2),
            "safe_surplus": round(safe_surplus, 2),
            "transferable": round(transferable, 2),
            "recently_donated": user in recent_donors,
            "cold_start": False,
        })

    return results


def _select_donors_highest_surplus(
    eligible: List[Dict], amount_requested: float
) -> List[Dict]:
    """Take from donor with most surplus first — safest, most predictable."""
    sorted_donors = sorted(eligible, key=lambda x: x["transferable"], reverse=True)
    return _greedy_fill(sorted_donors, amount_requested)


def _select_donors_weighted_random(
    eligible: List[Dict], amount_requested: float, seed: Optional[int] = None
) -> List[Dict]:
    """
    Weighted random selection — donors chosen probabilistically proportional
    to surplus.  Users with more surplus are more likely to be chosen, but
    the selection varies across requests, distributing load over time.
    """
    if seed is not None:
        random.seed(seed)

    pool = [d for d in eligible if d["transferable"] > 0]
    if not pool:
        return []

    total_weight = sum(d["transferable"] for d in pool)
    if total_weight <= 0:
        return pool[:1]

    ordered = []
    remaining_pool = pool.copy()

    while remaining_pool and sum(d.get("reduction", d["transferable"]) for d in ordered) < amount_requested:
        weights = [
            d["transferable"] / sum(d["transferable"] for d in remaining_pool)
            for d in remaining_pool
        ]
        chosen = random.choices(remaining_pool, weights=weights, k=1)[0]
        ordered.append(chosen)
        remaining_pool.remove(chosen)

    return _greedy_fill(ordered, amount_requested)


def _select_donors_minimum_donors(
    eligible: List[Dict], amount_requested: float
) -> List[Dict]:
    """
    Minimize the number of donors impacted.

    Strategy:
    1. If any single donor can cover the entire request, pick the one
       whose post-transfer balance is highest (least disrupted).
    2. Otherwise fall back to greedy-from-largest, which minimises donor
       count by exhausting each high-surplus donor before moving to the next.
    """
    # Phase 1: single-donor fulfillment
    single_candidates = [d for d in eligible if d["transferable"] >= amount_requested]
    if single_candidates:
        # Among those who can cover the full amount, prefer the one with most surplus
        # (takes proportionally least from them)
        best = max(single_candidates, key=lambda x: x["transferable"])
        return _greedy_fill([best], amount_requested)

    # Phase 2: greedy from largest — still minimises donor count vs random order
    sorted_donors = sorted(eligible, key=lambda x: x["transferable"], reverse=True)
    return _greedy_fill(sorted_donors, amount_requested)


def _select_donors_round_robin(
    eligible: List[Dict], amount_requested: float
) -> List[Dict]:
    """
    Prioritize donors who have NOT recently donated.
    Among non-recent donors, use highest surplus.
    Falls back to recent donors if needed.
    """
    fresh = [d for d in eligible if not d.get("recently_donated", False)]
    recent = [d for d in eligible if d.get("recently_donated", False)]

    fresh_sorted = sorted(fresh, key=lambda x: x["transferable"], reverse=True)
    result = _greedy_fill(fresh_sorted, amount_requested)

    filled = sum(d["reduction"] for d in result)
    if filled < amount_requested and recent:
        recent_sorted = sorted(recent, key=lambda x: x["transferable"], reverse=True)
        result += _greedy_fill(recent_sorted, amount_requested - filled)

    return result


def _greedy_fill(
    sorted_donors: List[Dict], amount_requested: float
) -> List[Dict]:
    """Take credits greedily from sorted donor list until request is fulfilled."""
    donors = []
    remaining_need = amount_requested
    for s in sorted_donors:
        if remaining_need <= 0:
            break
        if s["transferable"] <= 0:
            continue
        take = min(s["transferable"], remaining_need)
        donors.append({
            "user": s["user"],
            "current_limit": s["limit"],
            "new_limit": round(s["limit"] - take, 2),
            "reduction": round(take, 2),
            "used_today": s["used_today"],
            "predicted_remaining": s["predicted_remaining"],
        })
        remaining_need -= take
    return donors


def recommend_rebalance(
    hourly_df: pd.DataFrame,
    requester: str,
    cohort_members: List[str],
    surface: str,
    amount_requested: float,
    current_limits: Dict[str, float],
    today_usage: Dict[str, float],
    buffer_pct: int = REBALANCE_DEFAULT_BUFFER_PCT,
    max_transfer_pct: int = REBALANCE_DEFAULT_MAX_TRANSFER_PCT,
    lookback_days: int = REBALANCE_DEFAULT_LOOKBACK_DAYS,
    donor_strategy: str = DEFAULT_DONOR_STRATEGY,
    donor_protection_hours: int = DEFAULT_DONOR_PROTECTION_HOURS,
    recent_donors: Optional[List[str]] = None,
) -> Dict[str, Any]:
    eligible_members = [m for m in cohort_members if m != requester]

    surpluses = calculate_cohort_surplus(
        hourly_df, eligible_members, surface,
        current_limits, today_usage,
        buffer_pct, max_transfer_pct, lookback_days,
        recent_donors=recent_donors,
    )

    eligible = [s for s in surpluses if s["transferable"] > 0]
    total_available = sum(s["transferable"] for s in eligible)
    cold_start_count = sum(1 for s in surpluses if s.get("cold_start", False))

    if total_available < amount_requested:
        reason = (
            f"Only {total_available:.1f} credits available across cohort "
            f"({amount_requested:.1f} requested)"
        )
        if cold_start_count > 0:
            reason += f". {cold_start_count} user(s) excluded (insufficient history)."
        return {
            "feasible": False,
            "available": round(total_available, 2),
            "requested": amount_requested,
            "donors": [],
            "strategy": donor_strategy,
            "reason": reason,
        }

    strategy = donor_strategy.upper()
    if strategy == "HIGHEST_SURPLUS":
        donors = _select_donors_highest_surplus(eligible, amount_requested)
    elif strategy == "MINIMUM_DONORS":
        donors = _select_donors_minimum_donors(eligible, amount_requested)
    elif strategy == "ROUND_ROBIN":
        donors = _select_donors_round_robin(eligible, amount_requested)
    else:
        donors = _select_donors_weighted_random(eligible, amount_requested)

    return {
        "feasible": True,
        "available": round(total_available, 2),
        "requested": amount_requested,
        "donors": donors,
        "strategy": donor_strategy,
        "reason": f"Fulfilled using {strategy} strategy from {len(donors)} donor(s)",
    }
