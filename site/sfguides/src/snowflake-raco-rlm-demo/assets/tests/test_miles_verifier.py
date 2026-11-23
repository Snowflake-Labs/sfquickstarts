import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from miles_verifier import verify_edit, xor_reward


GOOD = {"layer": 1, "kind": "bias", "row": 0, "from_value": -1.5, "to_value": -0.5}


def test_complete_truth_table_is_rewarded():
    response = json.dumps(GOOD)
    assert verify_edit(response) == 1.0
    assert asyncio.run(xor_reward(None, SimpleNamespace(response=response))) == 1.0


def test_bad_edits_and_untrusted_payloads_fail_closed():
    bad_bias = {**GOOD, "to_value": -2}
    wrong_location = {**GOOD, "layer": 0}
    for response in (
        json.dumps(bad_bias), json.dumps(wrong_location), json.dumps({**GOOD, "extra": 1}),
        json.dumps({**GOOD, "to_value": float("nan")}),
        "```json\n" + json.dumps(GOOD) + "\n```", "print('hello')", "x" * 2049,
        json.dumps([GOOD]), json.dumps({**GOOD, "layer": True}),
        json.dumps({**GOOD, "to_value": "-0.5"}), "", None,
    ):
        assert verify_edit(response) == 0.0

def test_wsp_reward_hook():
    import asyncio
    import json
    from types import SimpleNamespace

    import weight_space
    from miles_verifier import wsp_reward

    good = SimpleNamespace(response=weight_space.oracle_response(90002), metadata={"task": "wsp_repair", "seed": 90002})
    assert asyncio.run(wsp_reward(None, good)) > 0.5
    assert asyncio.run(wsp_reward(None, SimpleNamespace(response=good.response, metadata={}))) == 0.0
    assert asyncio.run(wsp_reward(None, SimpleNamespace(response=json.dumps({"edits": []}), metadata=good.metadata))) == 0.0
