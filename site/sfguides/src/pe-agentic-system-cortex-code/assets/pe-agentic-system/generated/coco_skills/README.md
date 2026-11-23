# Financial CoCo Skills

Project-local Cortex Code instruction packages. Open this project in CoCo and use its skill picker to select the relevant skill after discovery/reload. A notebook can inspect these files and run supporting code, but does not invoke CoCo merely by reading Markdown. Discovery in the current Desktop session has not been verified.

| Skill | Scope | Implementation status |
|---|---|---|
| pe-financial-modeling | DCF, leveraged buyouts, comparable companies, capitalization tables, distributions | Instructions; existing kernels require validation and approved adapters |
| pe-due-diligence | Disclosure-backed claim review and diligence questions | Instructions; retrieval/extraction integration required |
| pe-portfolio-monitoring | Operating metrics, investment-case comparisons and exceptions | Instructions; governed metrics and data integration required |
| advanced-financial-modeling | Real options, physics-informed models, trajectory optimization | Instructions; approved model-specific implementations required |
| capital-markets-review | Trades, settlements, corporate actions, valuation controls | Instructions; source systems and calculators required |
| hedge-fund-review | Investor fees, NAV and regulatory preparation | Instructions; contractual calculators and mappings required |
| quant-model-validation | Model invariants, parity, backtest integrity and benchmarking | Instructions; existing tests/benchmarks are scoped evidence only |
| private-credit-fund-operations | Covenants, debt service, cash and investor reporting | Instructions; agreement-specific tools required |
| valuation-input-review | Extraction contract, warnings and economic consistency | Python supporting-code demo available; not evidence authentication |
| distribution-reconciliation-review | Allocation conservation and completeness | Snowflake SQL demo available; not deployed or evaluated |
| financial-evaluation-review | Dataset, scores, failures, traces and release evidence | Notebook/evaluation configuration available; no live evaluation yet |

Every package has Workflow, Stopping Points, and Output sections. No package authorizes payments, trades, filings, publication, or its own policy exceptions. A missing tool produces a blocker, not an invented result.

## Supporting-Code Demo

From this project, run `python3 examples/coco_skill_demo.py`. It calls the existing assurance boundary on five synthetic extractions and reports statuses and findings. It needs Pydantic 2 and does not use Snowflake, a model, or native kernels. This is a direct supporting-code run, not a CoCo invocation transcript. The notebook bundle includes the same source files, skill inventory, and file hashes.

## Capturing Actual CoCo Invocation

Select a discovered project skill in CoCo, request the relevant review, and retain the conversation showing skill loading, invoked tools, arguments, outputs, and blockers. For example: `Use valuation-input-review to run the five synthetic boundary cases in examples/coco_skill_demo.py; retain exact statuses and hashes and do not calculate a valuation.` Skill availability must be confirmed by the client; these instructions do not register unavailable tools. The separate Cortex Agent runtime skill has its own stage attachment and trace requirements.