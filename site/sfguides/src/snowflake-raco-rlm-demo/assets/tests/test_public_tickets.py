import csv
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from support import PUBLIC_COLUMNS, PUBLIC_STATUSES, public_ticket_sample


def write_csv(path, records):
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=PUBLIC_COLUMNS)
        writer.writeheader()
        writer.writerows(records)


def sample_records():
    return [dict(zip(PUBLIC_COLUMNS, (f'CONV-{index}', 'Issue', 'Suggested step',
                                      '10 minutes', 'Network', status)))
            for index, status in enumerate(PUBLIC_STATUSES)]


def test_public_preview_selects_each_status_without_inventing_messages(tmp_path):
    path = tmp_path / 'tickets.csv'
    write_csv(path, sample_records())
    selected = public_ticket_sample(path, per_status=1)
    assert [record['Issue_Status'] for record in selected] == list(PUBLIC_STATUSES)
    assert all('POSTED_AT' not in record and 'MESSAGE_ID' not in record for record in selected)


@pytest.mark.parametrize('change', [
    lambda rows: rows.append(rows[0].copy()),
    lambda rows: rows[0].update({'Issue_Status': 'Unknown'}),
    lambda rows: rows[0].update({'Tech_Response': ''}),
])
def test_public_preview_rejects_invalid_records(tmp_path, change):
    path = tmp_path / 'tickets.csv'
    rows = sample_records()
    change(rows)
    write_csv(path, rows)
    with pytest.raises(ValueError):
        public_ticket_sample(path, per_status=1)


def test_checked_in_public_csv_has_expected_structure():
    path = Path(__file__).resolve().parents[1] / 'tech_support_dataset.csv'
    selected = public_ticket_sample(path)
    assert len(selected) == 8
    assert len({record['Conversation_ID'] for record in selected}) == 8