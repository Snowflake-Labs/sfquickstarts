"""
Assurance layer — the validated boundary between reasoning and computation.

    from assurance import cross_boundary, BoundaryRejection

    try:
        report = cross_boundary(llm_json, wacc=Decimal("0.12"),
                                terminal_growth=Decimal("0.03"))
        inputs = report.validated_inputs.dcf   # safe for the engine
    except BoundaryRejection as rej:
        print(rej.report.summary())
"""

from assurance.contracts import (
    AssuranceReport,
    BoundaryRejection,
    CIMExtraction,
    DCFAssumptions,
    ExtractedValue,
    Finding,
    LBOAssumptions,
    Provenance,
    Severity,
    ValidatedModelInputs,
    cross_boundary,
)

__all__ = [
    "AssuranceReport",
    "BoundaryRejection",
    "CIMExtraction",
    "DCFAssumptions",
    "ExtractedValue",
    "Finding",
    "LBOAssumptions",
    "Provenance",
    "Severity",
    "ValidatedModelInputs",
    "cross_boundary",
]
