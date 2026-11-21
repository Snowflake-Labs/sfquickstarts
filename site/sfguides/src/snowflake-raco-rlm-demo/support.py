"""Validation boundary for synthetic thread mining and public ticket preview."""

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Literal


class Classification(BaseModel):
    status: Literal['resolved', 'unresolved', 'escalated']
    evidence_ids: list[str] = Field(min_length=1)


class Issue(BaseModel):
    title: str = Field(min_length=5, max_length=120)
    symptom: str = Field(min_length=5)
    resolution: str = Field(min_length=5)
    evidence_ids: list[str] = Field(min_length=1)


def ordered_threads(rows):
    groups = defaultdict(list)
    for row in rows:
        thread_id, message_id, posted_at, body = row
        groups[str(thread_id)].append({'message_id': str(message_id), 'posted_at': str(posted_at), 'body': str(body)})
    return {key: sorted(items, key=lambda item: (item['posted_at'], item['message_id'])) for key, items in groups.items()}


def validate_evidence(evidence_ids, messages):
    ids = {message['message_id'] for message in messages}
    if not evidence_ids or len(evidence_ids) != len(set(evidence_ids)) or not set(evidence_ids) <= ids:
        raise ValueError('Evidence must use distinct message IDs in this thread')


def validated_issue(classification, issue, messages):
    classification = Classification.model_validate(classification)
    validate_evidence(classification.evidence_ids, messages)
    if classification.status != 'resolved':
        return None
    issue = Issue.model_validate(issue)
    validate_evidence(issue.evidence_ids, messages)
    if not set(classification.evidence_ids) & set(issue.evidence_ids):
        raise ValueError('Classification and issue must share supporting evidence')
    return issue


def publish_chunks(thread_id, issue, max_chars=400):
    if max_chars < 80:
        raise ValueError('max_chars too small')
    title = issue.title.replace('\n', ' ').strip()
    text = f'# {title}\n\nSymptom: {issue.symptom}\n\nResolution: {issue.resolution}'
    words = text.split()
    chunks, current = [], ''
    for word in words:
        if len(word) > max_chars:
            raise ValueError('Word longer than chunk limit')
        if len(current) + len(word) + 1 > max_chars and current:
            chunks.append(current)
            current = ''
        current = f'{current} {word}'.strip()
    if current:
        chunks.append(current)
    return [
        {'chunk_id': hashlib.sha256(f'{thread_id}:{index}:{text}'.encode()).hexdigest(),
         'thread_id': thread_id, 'title': title, 'chunk_text': chunk,
         'evidence_ids': issue.evidence_ids, 'chunk_index': index}
        for index, chunk in enumerate(chunks)
    ]


def serialize_thread(messages):
    return json.dumps(messages, ensure_ascii=True)


PUBLIC_COLUMNS = (
    'Conversation_ID', 'Customer_Issue', 'Tech_Response',
    'Resolution_Time', 'Issue_Category', 'Issue_Status',
)
PUBLIC_STATUSES = ('Resolved', 'Resolved after follow-up', 'Pending', 'Escalated')


def public_ticket_sample(path, per_status=2):
    """Read a bounded, deterministic preview; never convert labels into verified fixes."""
    if not isinstance(per_status, int) or isinstance(per_status, bool) or not 1 <= per_status <= 5:
        raise ValueError('per_status must be between 1 and 5')
    source = Path(path)
    if source.stat().st_size > 1_000_000:
        raise ValueError('Unexpectedly large public CSV')
    selected = {status: [] for status in PUBLIC_STATUSES}
    seen = set()
    with source.open(newline='', encoding='utf-8-sig') as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != PUBLIC_COLUMNS:
            raise ValueError('Unexpected public CSV columns')
        for record in reader:
            if None in record or any(value is None or not value.strip() or len(value) > 2000
                                     for value in record.values()):
                raise ValueError('Incomplete or oversized public CSV record')
            identifier, status = record['Conversation_ID'], record['Issue_Status']
            if identifier in seen or status not in selected:
                raise ValueError('Duplicate ID or unknown publisher status')
            seen.add(identifier)
            if len(selected[status]) < per_status:
                selected[status].append(record)
    if any(len(group) < per_status for group in selected.values()):
        raise ValueError('Missing publisher status examples')
    return [record for status in PUBLIC_STATUSES for record in selected[status]]