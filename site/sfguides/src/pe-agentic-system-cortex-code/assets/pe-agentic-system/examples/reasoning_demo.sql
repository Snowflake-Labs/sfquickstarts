-- =============================================================================
-- PE Agentic System - Live "reasoning vs cheap model" demonstration
-- =============================================================================
-- Runs the SAME PE task through a reasoning-tier model and a cheap/balanced
-- model on the active Snowflake connection (<your connection>), to show where deep
-- reasoning matters vs where a cheaper model is sufficient.
--
-- Confirmed live models on <your account>:
--   reasoning  -> claude-opus-4-6, openai-gpt-5.4
--   cheap/bal  -> claude-sonnet-4-5, openai-gpt-5.1
-- (openai-gpt-5.6, openai-gpt-sol, llama-4.1-nemotron, mistral-large-2-2 are
--  NOT available on this account - they return HTTP 400 "unknown model".)
--
-- Requires: USE WAREHOUSE <your warehouse>;  (or any active warehouse)
-- =============================================================================

USE WAREHOUSE <your warehouse>;

-- ---------------------------------------------------------------------------
-- 1) REASONING TIER  ->  claude-opus-4-6  (deep, step-by-step, flags ambiguity)
-- ---------------------------------------------------------------------------
SELECT AI_COMPLETE(
  'claude-opus-4-6',
  $$A PE fund acquires a company for $500M using $200M equity and $300M debt.
  The target has EBITDA of $50M and capex of $15M/yr. Debt carries 6% interest
  with $10M/yr amortization. If EBITDA grows 5%/yr and the fund exits at year 5
  at 9x EBITDA, estimate (1) year-1 unlevered free cash flow and (2) the equity
  MOIC. Show your reasoning step by step and state any assumptions.$$
) AS reasoning_output;

-- ---------------------------------------------------------------------------
-- 2) CHEAP / BALANCED TIER  ->  claude-sonnet-4-5  (fast, clean, less nuance)
-- ---------------------------------------------------------------------------
SELECT AI_COMPLETE(
  'claude-sonnet-4-5',
  $$A PE fund acquires a company for $500M using $200M equity and $300M debt.
  The target has EBITDA of $50M and capex of $15M/yr. Debt carries 6% interest
  with $10M/yr amortization. If EBITDA grows 5%/yr and the fund exits at year 5
  at 9x EBITDA, estimate (1) year-1 unlevered free cash flow and (2) the equity
  MOIC. Show your reasoning step by step and state any assumptions.$$
) AS cheap_output;

-- ---------------------------------------------------------------------------
-- 3) GPT REASONING TIER  ->  openai-gpt-5.4  (also a strong reasoning model)
-- ---------------------------------------------------------------------------
SELECT AI_COMPLETE(
  'openai-gpt-5.4',
  $$A PE fund acquires a company for $500M using $200M equity and $300M debt.
  The target has EBITDA of $50M and capex of $15M/yr. Debt carries 6% interest
  with $10M/yr amortization. If EBITDA grows 5%/yr and the fund exits at year 5
  at 9x EBITDA, estimate (1) year-1 unlevered free cash flow and (2) the equity
  MOIC. Show your reasoning step by step and state any assumptions.$$
) AS gpt_reasoning_output;

-- ---------------------------------------------------------------------------
-- How to interpret (observed live 2026-08-26 on <your account>):
--   MOIC was robust (~1.62x) across ALL models, but Year-1 UFCF differed by up
--   to ~40% ($26.25M vs $37.5M) purely on ambiguous assumptions (Y1 EBITDA
--   timing convention + tax rate). The reasoning models explicitly surfaced and
--   stress-tested the assumptions (even added sensitivity); the cheap model
--   answered fast but silently picked one convention. => Mechanical math: cheap
--   is fine. Ambiguity-laden judgment: you want the reasoning tier.
-- =============================================================================
