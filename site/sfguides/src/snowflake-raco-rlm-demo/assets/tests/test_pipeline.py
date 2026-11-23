import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from support import Issue, ordered_threads, publish_chunks, validated_issue
from vision import covariance_is_valid, rotation_repeatability


MESSAGES = [
    {'message_id': 'm1', 'body': 'failed'},
    {'message_id': 'm2', 'body': 'fixed'},
]


def test_thread_order():
    rows = [('t', 'm2', '2026-01-02', 'fixed'), ('t', 'm1', '2026-01-01', 'failed')]
    assert [message['message_id'] for message in ordered_threads(rows)['t']] == ['m1', 'm2']


def test_status_gate_and_evidence():
    raw = {'title': 'Warehouse missing', 'symptom': 'Task fails on run',
           'resolution': 'Set authorized warehouse', 'evidence_ids': ['m2']}
    assert validated_issue({'status': 'unresolved', 'evidence_ids': ['m1']}, None, MESSAGES) is None
    assert validated_issue({'status': 'resolved', 'evidence_ids': ['m2']}, raw, MESSAGES).title == 'Warehouse missing'
    with pytest.raises(ValueError):
        validated_issue({'status': 'resolved', 'evidence_ids': ['invented']}, raw, MESSAGES)
    with pytest.raises(ValueError):
        validated_issue({'status': 'resolved', 'evidence_ids': ['m1']}, raw, MESSAGES)


def test_chunks_are_stable_and_bounded():
    issue = Issue(title='Warehouse missing', symptom='Task fails on run',
                  resolution='Set authorized warehouse ' * 10, evidence_ids=['m2'])
    chunks = publish_chunks('t', issue, 80)
    assert chunks == publish_chunks('t', issue, 80)
    assert all(len(chunk['chunk_text']) <= 80 for chunk in chunks)
    assert all(chunk['thread_id'] == 't' for chunk in chunks)


def test_covariance_and_rotation():
    assert covariance_is_valid([[2, 0], [0, 1]])
    assert not covariance_is_valid([[1, 3], [3, 1]])
    assert rotation_repeatability([(2, 3)], [(3, 7)], 10, 10, 0) == 1