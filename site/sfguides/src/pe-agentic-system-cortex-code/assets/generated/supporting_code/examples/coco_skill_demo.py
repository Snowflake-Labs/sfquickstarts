import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from assurance.contracts import BoundaryRejection, cross_boundary
from examples.assurance_boundary_demo import CASES, FIRM_TERMINAL_GROWTH, FIRM_WACC


def review_inputs(raw_output, *, wacc, terminal_growth, projection_years):
    try:
        report = cross_boundary(
            raw_output, wacc=Decimal(wacc), terminal_growth=Decimal(terminal_growth),
            projection_years=projection_years, strict=True,
        )
    except BoundaryRejection as rejection:
        report = rejection.report
    status = 'blocked'
    if report.accepted and report.validated_inputs is not None:
        status = 'review_required' if report.warnings else 'checks_passed'
    return {'status': status, 'input_hash': report.raw_input_sha256,
            'findings': [finding.model_dump(mode='json') for finding in report.findings]}


def run_demo():
    expected = ['checks_passed', 'blocked', 'blocked', 'review_required', 'blocked']
    results = []
    for (title, _, payload, overrides), expected_status in zip(CASES, expected):
        parameters = {'wacc': str(FIRM_WACC), 'terminal_growth': str(FIRM_TERMINAL_GROWTH),
                      'projection_years': 5}
        parameters.update({key: str(value) for key, value in overrides.items()})
        result = review_inputs(payload, **parameters)
        if result['status'] != expected_status:
            raise AssertionError(f"Unexpected result for {title}: {result['status']}")
        results.append({'case': title, 'synthetic': True,
                        'execution_kind': 'direct_supporting_code_not_coco_invocation',
                        'parameters': parameters, **result})
    return {'skill': 'valuation-input-review', 'cases': results,
            'sources_sha256': {
                relative: hashlib.sha256((PROJECT_ROOT / relative).read_bytes()).hexdigest()
                for relative in ('assurance/contracts.py', 'examples/assurance_boundary_demo.py',
                                 'examples/coco_skill_demo.py')},
            'limitations': 'No model call, CoCo invocation, evidence authentication, valuation or payment approval.'}


if __name__ == '__main__':
    print(json.dumps(run_demo(), indent=2))