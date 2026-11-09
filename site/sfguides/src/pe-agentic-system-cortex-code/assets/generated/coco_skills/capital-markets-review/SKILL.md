---
name: capital-markets-review
description: "Review capital-markets operations evidence. Use for trade reconciliation, settlements, corporate actions, stale prices or independent valuation controls."
---
# Capital-Markets Review

## Workflow
1. Identify instrument, trade identifier, lifecycle event, counterparty scope, valuation timestamp, calendar and units. Confirm the authorized source-of-record for each field.
2. For trade reconciliation match execution, confirmation, position, cash and settlement records at the correct grain. Separate amendments, cancellations, partial fills and partial settlements.
3. For corporate actions inspect announced terms, ex/record/pay dates, elections and entitlements. Treat absent elections and unmatched instruments as exceptions.
4. For valuation control compare authorized prices and approved independent calculations using stated stale-price and tolerance policies. Do not net offsetting breaks across instruments.
5. Record discrepancies with evidence and route to operations or valuation reviewers. Use deterministic tools only where configured; otherwise return a blocker.

## Stopping Points
Source-system and calculator integrations are not implemented here. Stop for missing mappings, timestamps, calendars or permitted tools. No trade amendments, elections, orders, settlement release or limit overrides are authorized.

## Output
Instrument/event-scoped break ledger, source values, applicable policy, supporting records, and escalation owner.