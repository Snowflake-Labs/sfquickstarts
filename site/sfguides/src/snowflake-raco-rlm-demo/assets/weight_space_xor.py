"""Bounded direct-weight edit on an analytic 2-2-1 ReLU XOR network."""

import copy
import hashlib
import json
import math

from pydantic import BaseModel, Field, field_validator


BASE_NETWORK = {
    "layers": [
        {"weights": [[1.0, -1.0], [-1.0, 1.0]], "bias": [0.0, 0.0], "activation": "relu"},
        {"weights": [[1.0, 1.0]], "bias": [-1.5], "activation": "linear"},
    ]
}
INPUTS = ((0, 0), (0, 1), (1, 0), (1, 1))


class BiasEdit(BaseModel):
    """Allow only the output bias of this fixed toy network to change."""

    layer: int = Field(ge=1, le=1)
    kind: str
    row: int = Field(ge=0, le=0)
    from_value: float
    to_value: float

    @field_validator("kind")
    @classmethod
    def only_bias(cls, value):
        if value != "bias":
            raise ValueError("Only a bias edit is allowed")
        return value

    @field_validator("from_value", "to_value")
    @classmethod
    def finite_value(cls, value):
        if not math.isfinite(value) or abs(value) > 10:
            raise ValueError("Bias must be finite and bounded")
        return value


def validate_network(network):
    if set(network) != {"layers"} or len(network["layers"]) != 2:
        raise ValueError("Expected a two-layer network")
    for layer, expected_inputs, expected_outputs, activation in zip(
        network["layers"], (2, 2), (2, 1), ("relu", "linear")
    ):
        if set(layer) != {"weights", "bias", "activation"} or layer["activation"] != activation:
            raise ValueError("Unexpected layer structure")
        if len(layer["weights"]) != expected_outputs or len(layer["bias"]) != expected_outputs:
            raise ValueError("Unexpected output shape")
        if any(len(row) != expected_inputs for row in layer["weights"]):
            raise ValueError("Unexpected input shape")
        values = [*layer["bias"], *(item for row in layer["weights"] for item in row)]
        if any(isinstance(item, bool) or not isinstance(item, (int, float)) or
               not math.isfinite(item) or abs(item) > 10 for item in values):
            raise ValueError("Weights must be finite numeric values in [-10, 10]")
    return network


def forward(network, inputs):
    validate_network(network)
    activations = list(inputs)
    if len(activations) != 2 or any(value not in (0, 1) for value in activations):
        raise ValueError("Expected two binary inputs")
    for layer in network["layers"]:
        activations = [
            sum(weight * value for weight, value in zip(row, activations)) + bias
            for row, bias in zip(layer["weights"], layer["bias"])
        ]
        if layer["activation"] == "relu":
            activations = [max(0.0, value) for value in activations]
    return activations[0]


def truth_table(network):
    return [
        {"inputs": list(inputs), "logit": forward(network, inputs),
         "prediction": int(forward(network, inputs) > 0),
         "expected": inputs[0] ^ inputs[1]}
        for inputs in INPUTS
    ]


def apply_edit(network, proposed):
    validate_network(network)
    edit = BiasEdit.model_validate(proposed)
    current = network["layers"][1]["bias"][0]
    if edit.from_value != current or edit.to_value == current:
        raise ValueError("Edit must change the exact current output bias")
    updated = copy.deepcopy(network)
    updated["layers"][1]["bias"][0] = edit.to_value
    validate_network(updated)
    return updated


def fingerprint(network):
    validate_network(network)
    return hashlib.sha256(json.dumps(network, sort_keys=True, separators=(",", ":")).encode()).hexdigest()