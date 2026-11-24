"""Deterministic, CPU-only reward hooks for Miles weight-edit rollouts (XOR fixture and WSP repair).

The rollout's response is data, never executable code. This hook does not
connect to Snowflake or import Miles; Miles imports it by dotted path.
"""

import json

from weight_space_xor import BASE_NETWORK, apply_edit, truth_table


EDIT_FIELDS = {"layer", "kind", "row", "from_value", "to_value"}


def verify_edit(response):
    """Return a binary reward for an exact, valid, complete XOR repair."""
    if not isinstance(response, str) or len(response) > 2048:
        return 0.0
    try:
        proposed = json.loads(response)
        if not isinstance(proposed, dict) or set(proposed) != EDIT_FIELDS:
            return 0.0
        if (type(proposed["layer"]) is not int or type(proposed["row"]) is not int
                or type(proposed["kind"]) is not str
                or any(type(proposed[key]) not in (int, float) for key in ("from_value", "to_value"))):
            return 0.0
        repaired = apply_edit(BASE_NETWORK, proposed)
    except (TypeError, ValueError):
        return 0.0
    return float(all(row["prediction"] == row["expected"] for row in truth_table(repaired)))


async def xor_reward(args, sample, **kwargs):
    """Miles --custom-rm-path hook; score only the sampled response text."""
    return verify_edit(sample.response)

async def wsp_reward(args, sample, **kwargs):
    """Miles --custom-rm-path hook for the weight-space repair task.

    The task seed comes from the sample's metadata (written by weight_space.write_miles_jsonl).
    The instance is rebuilt from that seed on the worker; the reward is the clipped fraction of
    the planted accuracy loss recovered on the instance's hidden validation split."""
    import weight_space

    metadata = getattr(sample, "metadata", None) or {}
    if metadata.get("task") != "wsp_repair" or not isinstance(metadata.get("seed"), int):
        return 0.0
    return float(weight_space.score_proposal(metadata["seed"], sample.response)["reward"])
