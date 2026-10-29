sidebar: true
sidebar_json: ai-cookbook
author: Cal Jepson
id: ai-cookbook-coco-user-budget-sizing
categories: snowflake-site:taxonomy/product/ai
language: en
summary: Tiered per-user CoCo quotas, daily limits, and alert-only team budgets, starting from conservative defaults and sized from your own ACCOUNT_USAGE.
environments: web
status: Published
fork_repo_link: https://github.com/Snowflake-Labs/cortex-ai-cookbook/tree/main/site/cortex-ai-cookbook/src/coco-user-budget-sizing

# Size Cortex Code per-user limits from real usage

## Overview

Give every Cortex Code (CoCo) user room to work, stop runaway spend before it hits the bill, and know which numbers to pick. This recipe deploys tiered per-user quotas and an alert-only team budget with conservative starting limits, gives you the SQL to size those limits from your own account, and makes blocking a deliberate step you take once the numbers have been reviewed.

| At a glance | |
|---|---|
| Status | GA |
| Stage | Operate |
| Topics | AI Observability, Cortex Code |
| Time | 30 min |
| Edition | Enterprise |
| Regions | Any region with Cortex Code and SNOWFLAKE_COCO_USAGE_HISTORY |
| Privileges | ACCOUNTADMIN for 01_setup.sql, the optional 05_account_backstop.sql (account parameters), and 99_teardown.sql; 02, 03, and 04 run as the COOKBOOK_* role |
| Last verified | 2026-10-13 |
| Code | [Recipe folder on GitHub](https://github.com/Snowflake-Labs/cortex-ai-cookbook/tree/main/site/cortex-ai-cookbook/src/coco-user-budget-sizing) · [Teardown script](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/site/cortex-ai-cookbook/src/coco-user-budget-sizing/sql/99_teardown.sql) |
| Problems | [Open an issue](https://github.com/Snowflake-Labs/cortex-ai-cookbook/issues/new?template=recipe-problem.yml&title=%5Bcoco-user-budget-sizing%5D%20&recipe=site%2Fcortex-ai-cookbook%2Fsrc%2Fcoco-user-budget-sizing) |

## When to use this

- You are about to turn CoCo on and want sensible per-user limits in place from day one, before you have any usage history.
- You are rolling CoCo out beyond a pilot and need per-user limits that most people will never notice.
- You have a few heavy users and want them governed separately from everyone else.
- Finance wants alerts on team-level spend without anyone being blocked by them.

Not the right fit if you only need to report on CoCo spend after the fact. For that, start with [AI usage and cost attribution](https://www.snowflake.com/en/developers/guides/ai-cookbook/ai-usage-cost-attribution/).

## How it works

![How it works: Size Cortex Code per-user limits from real usage](https://raw.githubusercontent.com/Snowflake-Labs/sfquickstarts/master/journeys/ai-cookbook/coco-user-budget-sizing/assets/coco-user-budget-sizing-01.png)

This recipe owns the per-user quotas for CoCo. It builds on [AI usage and cost attribution](https://www.snowflake.com/en/developers/guides/ai-cookbook/ai-usage-cost-attribution/) for reporting. Don't also add the `CORTEX CODE` shared resource to that recipe's quota: CoCo users would then sit under two independent quotas, each of which can block them.

Four ideas shape the setup:

1. **Two audiences, two quotas.** CoCo spend is usually uneven: a few people who use it every day account for much of it. One limit can't fit both groups. Tag power users with `USAGE_TIER = 'power'`. A General quota covers everyone except that tag; a Power quota covers only that tag. In this recipe, a power user is anyone active on 15 or more of the last 30 days, which is a working pattern, not a spending level.
2. **The monthly limit is the budget; the daily limit is the safety net.** The daily limit sits well below the monthly one. For General users, 35 a day is under a quarter of the 150 monthly limit, so it catches a runaway loop or a mistake within hours, and one bad day can't use up the month.
3. **Alert first, block deliberately.** The first deployment only observes. Admins get summaries, and quotas record who would cross a limit, but nobody is blocked and, by default, no user gets emailed. You turn on user notices and blocking as separate, explicit steps once you have reviewed the numbers.
4. **Team budgets watch, quotas enforce.** A budget scoped by a `COST_CENTER` tag alerts when a team's total CoCo spend crosses a threshold. It has no action attached, so it never blocks anyone.

### Starting limits

These are conservative defaults to start with, not measured recommendations. Your own usage, measured by `sql/02_size_your_limits.sql`, is the evidence for adjusting them.

| Control | General | Power |
|---|---|---|
| Monthly quota (per user) | 150 | 1,500 |
| Daily limit inside the quota (per user) | 35 | 150 |
| Blocking at the limit | off until you turn it on | off until you turn it on |
| Account daily parameter (optional backstop, each surface) | 300 | 300 |
| Team budget | alert only | alert only |

## Prerequisites

| Requirement | Notes |
|---|---|
| Enterprise edition or higher | Per-user quotas and budgets for shared resources require it. |
| ACCOUNTADMIN | To create the recipe role, grant the `SNOWFLAKE.USAGE_VIEWER`, `QUOTA_CREATOR`, and `BUDGET_CREATOR` database roles, tag users, and (optionally) set account parameters. |
| Verified admin email addresses | Admin summaries and team budget alerts go to these addresses. Set them in `sql/03`. |
| CoCo usage history (optional) | You need a few weeks of usage only to size limits from your own data. Without it, start with the defaults. |

## Quickstart

1. `snow sql -f sql/01_setup.sql` as ACCOUNTADMIN: role, warehouse, database, and tags.
2. If you already use CoCo, `snow sql -f sql/02_size_your_limits.sql`: your percentiles, a back-test of the candidate limits, and suggested power users. Review and run the generated `ALTER USER ... SET TAG` statements. Skip this step if you have no usage yet; everyone starts in the General quota.
3. Set `admin_emails` in `sql/03_quotas_and_budget.sql`, then `snow sql -f sql/03_quotas_and_budget.sql`: quotas, team budget, scope, and alerts.
4. Wait 5 to 10 minutes for scope to propagate, then `snow sql -f sql/04_limits.sql`: limits, with blocking off.
5. Optional: `snow sql -f sql/05_account_backstop.sql` as ACCOUNTADMIN, if you want an account-wide daily limit. Read [Add the account-wide backstop](#walkthrough) first.
6. After two to four weeks of alerts, [turn on enforcement](#walkthrough).

## Walkthrough

### 1. Measure your own usage

`02_size_your_limits.sql` creates one view, `SIZING.USER_DAILY`, over `SNOWFLAKE.ACCOUNT_USAGE.SNOWFLAKE_COCO_USAGE_HISTORY`, labels each user General or Power by active days, and returns the monthly and daily percentiles:

```sql
SELECT tier,
       COUNT(*) AS users,
       ROUND(PERCENTILE_CONT(0.50)  WITHIN GROUP (ORDER BY credits), 1) AS p50,
       ROUND(PERCENTILE_CONT(0.99)  WITHIN GROUP (ORDER BY credits), 1) AS p99,
       ROUND(PERCENTILE_CONT(0.995) WITHIN GROUP (ORDER BY credits), 1) AS p995
FROM (SELECT user_name, tier, SUM(credits) AS credits FROM SIZING.USER_DAILY GROUP BY 1, 2)
GROUP BY tier;
```

Size the limits from the results:

- **Monthly limit:** about 2 times the p99 for small groups (under 200 users), or about the p99.5 for large ones.
- **Daily limit:** about 3 to 4 times the daily p99 for General users, and about 1.5 to 2 times for Power users, whose usual day is already heavy. Keep it well below the monthly limit, at a quarter or less, so one runaway day can't use up the month.

Then set the candidate values at the top of the script and rerun the back-test. Aim for under 1% of users blocked in a month.

### 2. Tag power users

The last query in `02` lists suggested power users and generates the statement for each:

```sql
ALTER USER "JDOE" SET TAG COOKBOOK_COCO_USER_BUDGET_SIZING.GOVERNANCE.USAGE_TIER = 'power';
```

Review the list before running it. Power is a working pattern, not a reward, so revisit it monthly. Tag team members with `COST_CENTER` the same way if you want team budget alerts.

### 3. Create the quotas and the team budget

`03_quotas_and_budget.sql` creates both quotas against the `CORTEX CODE` shared resource, sets scope, and adds the alerts:

```sql
CREATE SNOWFLAKE.CORE.QUOTA IF NOT EXISTS COCO_GENERAL_QUOTA();
CALL COCO_GENERAL_QUOTA!ADD_SHARED_RESOURCE('CORTEX CODE');
CALL COCO_GENERAL_QUOTA!EXCLUDE_USERS('TAG',
  [[(SELECT SYSTEM$REFERENCE('TAG', $tier_tag, 'SESSION', 'APPLYBUDGET')), 'power']]);
CALL COCO_GENERAL_QUOTA!ADD_NOTIFICATION_THRESHOLD(80,  'PROJECTED', $notify_user, 'MONTHLY');
CALL COCO_GENERAL_QUOTA!ADD_NOTIFICATION_THRESHOLD(100, 'ACTUAL',    $notify_user, 'MONTHLY');
CALL COCO_GENERAL_QUOTA!SET_ADMIN_EMAILS($admin_emails);
```

`notify_user` defaults to `FALSE`, so admins get summaries but individual users get no email while you review the numbers. Set it to `TRUE` and rerun `03` when you want every CoCo user in scope to be told when they are projected to reach 80% of their limit and when they reach 100%.

The Power quota uses `SET_USER_TAGS(..., 'UNION')` with the same tag instead of `EXCLUDE_USERS`. The team budget uses `SET_SPENDING_LIMIT`, `SET_USER_TAGS` on `COST_CENTER`, and `SET_NOTIFICATION_THRESHOLD(80)`, with no custom action, so it only alerts.

### 4. Set the limits

After scope has propagated, `04_limits.sql` sets the limits with blocking off:

```sql
CALL COCO_GENERAL_QUOTA!SET_PER_USER_LIMIT(150);            -- monthly
CALL COCO_GENERAL_QUOTA!SET_PER_USER_LIMIT(35, 'DAILY');
CALL COCO_GENERAL_QUOTA!SET_BLOCK_ENFORCEMENT_ENABLED(FALSE, TRUE);
```

### 5. Turn on enforcement

Leave blocking off for the first two to four weeks. During that time, check who crosses a limit in the admin summaries and in Snowsight, and rerun the back-test in `02` against the new usage. When the share of users who would be blocked is acceptable, set `block_enabled = TRUE` in `04_limits.sql` and rerun it. Blocked users are emailed unless you set `notify_blocked = FALSE`. To go back to alert only, set `block_enabled = FALSE` and rerun; blocked users are released within about 5 to 10 minutes.

### 6. Optional: add the account-wide backstop

`05_account_backstop.sql` is a separate, opt-in step because it changes account-level state. It backs up the current values, then sets the account-wide daily parameters, which apply to every user on each surface, including anyone a quota does not cover:

```sql
ALTER ACCOUNT SET CORTEX_CODE_CLI_DAILY_EST_CREDIT_LIMIT_PER_USER       = 300;
ALTER ACCOUNT SET CORTEX_CODE_DESKTOP_DAILY_EST_CREDIT_LIMIT_PER_USER   = 300;
ALTER ACCOUNT SET CORTEX_CODE_SNOWSIGHT_DAILY_EST_CREDIT_LIMIT_PER_USER = 300;
```

These parameters block as soon as they are set, whatever `block_enabled` says.

### 7. Extend it

The quotas, tags, and budget are a foundation to keep, not a test fixture. Add a team budget for each team by tagging its members with `COST_CENTER` and creating another budget like `COCO_TEAM_BUDGET`. Revisit the power-user list and the limits monthly with `02`, and rerun `04` when they change.

### Where to see it in Snowsight

Go to **Admin » Cost management » Budgets**. Quotas and budgets are listed together. Open a quota to see its enforcement breakdown (users near or over their limits) and per-user spend by day.

## Verify

```sql
CALL COOKBOOK_COCO_USER_BUDGET_SIZING.GOVERNANCE.COCO_GENERAL_QUOTA!GET_QUOTA_SCOPE();
CALL COOKBOOK_COCO_USER_BUDGET_SIZING.GOVERNANCE.COCO_POWER_QUOTA!GET_CONFIG();
CALL COOKBOOK_COCO_USER_BUDGET_SIZING.GOVERNANCE.COCO_GENERAL_QUOTA!GET_NOTIFICATION_THRESHOLDS();
CALL COOKBOOK_COCO_USER_BUDGET_SIZING.GOVERNANCE.COCO_GENERAL_QUOTA!GET_ACTIVE_BLOCKS_V2();
SHOW PARAMETERS LIKE 'CORTEX_CODE_%_DAILY_EST_CREDIT_LIMIT_PER_USER' IN ACCOUNT;
```

A tagged power user appears in the Power scope and not in the General scope. `GET_CONFIG` shows the limits you set. Until you turn on enforcement, `GET_ACTIVE_BLOCKS_V2` returns no rows. The parameters stay at their original values unless you ran `05`.

## Gotchas

| Symptom | Cause | Fix |
|---|---|---|
| A newly tagged user is still in the wrong quota | Scope changes take 5 to 10 minutes; new tag assignments can take up to about 2 hours | Check `GET_QUOTA_SCOPE` before setting limits, and wait before rerunning `04`. |
| A user is blocked earlier or later than the quota daily limit suggests | A quota's daily cycle resets at 00:00 UTC; the account parameters use a rolling 24-hour window per surface | Keep the `05` backstop well above the quota daily limits so the two never compete. |
| A team budget alert arrives hours after the spend | Budgets refresh up to every 6.5 hours by default | Use budgets for alerts and quotas for enforcement, or call `SET_REFRESH_TIER('TIER_1H')` on the budget for hourly refresh at higher cost. |
| `02` shows no recent usage or a short tail | `SNOWFLAKE_COCO_USAGE_HISTORY` lags by up to an hour, and fewer than two weeks of data understates the tail | Size on at least two weeks, ideally 30 days. |
| Every user is blocked from CoCo | An account parameter was set to `0`, which blocks all use (`-1` means unlimited) | Rerun `05` with a positive `backstop_daily`, or restore with `99_teardown.sql`. |
| Users are blocked even though `block_enabled = FALSE` | `05` was run; the account parameters block independently of the quotas | Raise `backstop_daily`, or restore the originals with teardown. |

## Teardown

```bash
snow sql -f sql/99_teardown.sql
```

Teardown drops the quotas and the budget, restores the original daily limit parameters if you ran `05`, and drops the role, database, and warehouse. Dropping the database drops the `USAGE_TIER` and `COST_CENTER` tags, which removes their assignments from users. Use it to back out the recipe completely; if you are keeping per-user limits, extend the deployment instead.

## Run it with a coding agent

Clone the repository first (`git clone https://github.com/Snowflake-Labs/cortex-ai-cookbook`) and run the prompt from its root.

```text
Help me size and set per-user Cortex Code limits using the recipe in
site/cortex-ai-cookbook/src/coco-user-budget-sizing.
1. Run SELECT CURRENT_ACCOUNT(), CURRENT_REGION(), CURRENT_ROLE(), CURRENT_WAREHOUSE();
   and confirm the target with me before changing anything.
2. Use the cost-intelligence skill to summarize my current Cortex Code spend.
   If there is little or no usage yet, skip to step 4 and use the starting
   limits (General 150 monthly / 35 daily, Power 1,500 / 150).
3. Run sql/01_setup.sql as ACCOUNTADMIN, then sql/02_size_your_limits.sql.
   Show me the percentiles and back-test, and propose monthly and daily limits for
   General and Power users. Ask me to approve the limits and the power-user list
   before tagging anyone.
4. Run sql/01_setup.sql if not already run. Set my admin emails. Show me the quota
   and budget statements in sql/03_quotas_and_budget.sql, including notify_user,
   and get my confirmation before running it.
5. Wait 10 minutes, confirm the scope with GET_QUOTA_SCOPE, show me sql/04_limits.sql
   with the approved limits and block_enabled = FALSE, and get my confirmation
   before running it.
6. Ask whether I want the account-wide backstop. Only if I say yes, show me the
   ALTER ACCOUNT statements in sql/05_account_backstop.sql and get my
   confirmation before running it.
7. Don't turn on blocking now. Remind me to set block_enabled = TRUE and rerun
   sql/04_limits.sql after two to four weeks of alerts and a back-test.
8. Only if I ask to remove the recipe, run sql/99_teardown.sql.
```

## Related skills

- `cost-intelligence` (bundled): analyze CoCo and other AI spend, budgets, and quotas in your account.

## References

- [Cortex Code cost controls](https://docs.snowflake.com/en/user-guide/cortex-code/cost-controls)
- [Per-user quotas](https://docs.snowflake.com/en/user-guide/budgets/per-user-quotas)
- [Cortex Code daily credit usage limits](https://docs.snowflake.com/en/user-guide/cortex-code/credit-usage-limit)
- [Budgets for shared resources](https://docs.snowflake.com/en/user-guide/budgets/budget-shared-resources)
- [SNOWFLAKE_COCO_USAGE_HISTORY view](https://docs.snowflake.com/en/sql-reference/account-usage/snowflake_coco_usage_history)
- [AI cost management and governance](https://docs.snowflake.com/en/user-guide/snowflake-cortex/governance-and-availability/ai-cost-management-and-governance)
