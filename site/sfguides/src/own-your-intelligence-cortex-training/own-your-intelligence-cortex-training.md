author: Josh Reini
id: own-your-intelligence-cortex-training
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai
language: en
summary: Post-train Qwen3-8B on a company decision policy with Cortex Training, compare it against the base model, and deploy the checkpoint as an OpenAI-compatible endpoint.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfquickstarts/issues

# Own Your Intelligence: Post-Train and Deploy Open Models with Cortex Training

## Overview

Your applications already know how your business makes decisions. This guide shows how to put that knowledge into the weights of an open model with Cortex Training (public preview), so the model follows your policy without the policy in the prompt.

The example is Northwind Supply Co., a fictional distributor. Its planning system computes the numbers for every SKU: days of cover, supplier lead time, suggested quantity, PO cap, supplier status, and flags for the two comparisons. What it needs from an agent is the decision and a planner note in Northwind's house style. You will post-train Qwen3-8B with LoRA on 200 of Northwind's decisions, score the base and tuned models side by side on 20 held-out SKUs, save a checkpoint, and deploy it as an OpenAI-compatible endpoint.

Everything runs in one Snowflake notebook. Your training loop runs on a CPU notebook, and Cortex Training runs the GPU work: forward and backward passes, optimizer steps, weight sync, and generation.

### What You'll Learn
- How to set up a role, secret, PAT, and external access integrations for Cortex Training from a notebook
- How to write a training loop with the Cortex Training primitives `forward_backward`, `step`, `weight_sync`, and `generate`
- How to measure a base model and a tuned model on the same held-out examples
- How to save a weights-only checkpoint and deploy it as an OpenAI-compatible endpoint
- How to call the endpoint with the OpenAI Python SDK, including streaming

### What You'll Build
A Snowflake notebook that teaches Qwen3-8B Northwind's reorder decision policy and house style. It shows the base and tuned scores, a per-SKU results table, and a chart, then calls the deployed model with only a SKU's inputs.

### Prerequisites
- Access to a [Snowflake account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides)
- Cortex Training enabled for the account and the tutorial role
- Model deployments (the OpenAI-compatible endpoint) enabled. This is a separate enablement. Without it, deployment fails with `HTTP 403 (517600): ... model deployments are not enabled for this account`.
- Eight H200 GPUs for training and sampling, then four for the endpoint, used one stage at a time. Expect about 20 to 30 minutes of GPU time.
- A role that can create the tutorial objects (the notebook uses `ACCOUNTADMIN` for setup and teardown only), and an organization policy that allows a role-restricted programmatic access token (PAT)
- A Snowflake Notebook on Container Runtime with Python 3.10 or later and a CPU compute pool such as `SYSTEM_COMPUTE_POOL_CPU`

No OpenAI account, local Python, Docker, or repository checkout is needed.

## Setup

Create a notebook in **Projects > Workspaces** on a CPU Container Runtime with Python 3.10 or later, and give its service a 15-minute idle timeout. Add each code block below as a cell, in order, with the explanation as a markdown cell above it.

One restart is required. Run the configuration, object, and PAT cells first. Then open **Connected > Manage service**, select the secret `CT_QUICKSTART_DB.LAB.CT_PAT`, and enable both `CT_QUICKSTART_API_EAI` and `CT_QUICKSTART_DOWNLOAD_EAI`. Save so the service restarts, rerun the configuration cell, and continue with the install cell.

### Configure the Notebook

Set `ACCOUNT_HOST` to this account's hostname, without `https://`. You can find it under your user menu > Account > View account details. Rerun this cell after every service restart.

```python
# Edit these values. Rerun this cell after every service restart.
ACCOUNT_HOST = "YOUR_ORG-YOUR_ACCOUNT.snowflakecomputing.com"  # exact hostname, no https://
ADMIN_ROLE = "ACCOUNTADMIN"
NOTEBOOK_COMPUTE_POOL = "SYSTEM_COMPUTE_POOL_CPU"
DATABASE = "CT_QUICKSTART_DB"
SCHEMA = "LAB"
ROLE = "CT_QUICKSTART_USER"
WAREHOUSE = "CT_QUICKSTART_WH"
SECRET_NAME = "CT_PAT"
PAT_NAME = "CT_QUICKSTART_NOTEBOOK"
PAT_DAYS = 1

MODEL_NAME = "Qwen/Qwen3-8B"
TOKENIZER_REVISION = "b968826d9c46dd6066d109eabc6255188de91218"
HARDWARE = "H200"
TRAINING_GPUS = 4
SAMPLING_GPUS = 4
SERVING_GPUS = 4
MAX_SEQ_LEN = 1024
STEPS = 60
BATCH_SIZE = 4
LEARNING_RATE = 1e-4

if "YOUR_" in ACCOUNT_HOST:
    raise ValueError("Set ACCOUNT_HOST to your account hostname, for example myorg-myaccount.snowflakecomputing.com")

import os

os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
os.environ.setdefault("HF_HUB_ETAG_TIMEOUT", "30")
os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "60")
```

### Create the Objects

This cell creates the role, database, warehouse, grants, and network rules. Every statement uses `IF NOT EXISTS` or is a grant, so rerunning it is safe.

```python
from snowflake.snowpark.context import get_active_session

session = get_active_session()
USER = session.sql("SELECT CURRENT_USER()").collect()[0][0]
session.use_role(ADMIN_ROLE)

for statement in [
    f"CREATE ROLE IF NOT EXISTS {ROLE}",
    f"GRANT ROLE {ROLE} TO ROLE SYSADMIN",
    f'GRANT ROLE {ROLE} TO USER "{USER}"',
    f"CREATE DATABASE IF NOT EXISTS {DATABASE}",
    f"CREATE SCHEMA IF NOT EXISTS {DATABASE}.{SCHEMA}",
    (f"CREATE WAREHOUSE IF NOT EXISTS {WAREHOUSE} WAREHOUSE_SIZE = 'XSMALL' "
     "AUTO_SUSPEND = 60 AUTO_RESUME = TRUE INITIALLY_SUSPENDED = TRUE"),
    f"GRANT USAGE ON DATABASE {DATABASE} TO ROLE {ROLE}",
    f"GRANT USAGE ON SCHEMA {DATABASE}.{SCHEMA} TO ROLE {ROLE}",
    f"GRANT CREATE EXPERIMENT ON SCHEMA {DATABASE}.{SCHEMA} TO ROLE {ROLE}",
    f"GRANT CREATE SECRET ON SCHEMA {DATABASE}.{SCHEMA} TO ROLE {ROLE}",
    f"GRANT USAGE ON WAREHOUSE {WAREHOUSE} TO ROLE {ROLE}",
    f"GRANT USAGE ON COMPUTE POOL {NOTEBOOK_COMPUTE_POOL} TO ROLE {ROLE}",
    (f"CREATE NETWORK RULE IF NOT EXISTS {DATABASE}.{SCHEMA}.CT_ACCOUNT_RULE MODE = EGRESS "
     f"TYPE = HOST_PORT VALUE_LIST = ('{ACCOUNT_HOST.lower()}:443')"),
    (f"CREATE NETWORK RULE IF NOT EXISTS {DATABASE}.{SCHEMA}.CT_DOWNLOAD_RULE MODE = EGRESS "
     "TYPE = HOST_PORT VALUE_LIST = ('pypi.org:443', 'files.pythonhosted.org:443', "
     "'github.com:443', 'codeload.github.com:443', 'huggingface.co:443', "
     "'us.aws.cdn.hf.co:443', 'cdn-lfs.hf.co:443', 'cdn-lfs-us-1.hf.co:443', "
     "'cas-bridge.xethub.hf.co:443', 'cas-server.xethub.hf.co:443', 'transfer.xethub.hf.co:443')"),
]:
    session.sql(statement).collect()
print(f"Objects ready for {USER}: {DATABASE}.{SCHEMA}, {WAREHOUSE}, role {ROLE}.")
```

### Create the PAT and Integrations

This cell issues a one-day PAT restricted to the tutorial role and writes it straight into the secret. The token is never printed. An active PAT is reused. It then creates the two external access integrations: one for the account API and one for package and tokenizer downloads.

If your organization blocks PAT creation from a notebook session, create one in Snowsight under **Settings > Authentication > Programmatic access tokens**, restrict it to `CT_QUICKSTART_USER`, and store it with `CREATE SECRET`.

```python
SECRET_FQN = f"{DATABASE}.{SCHEMA}.{SECRET_NAME}"
session.use_role(ADMIN_ROLE)
tokens = {row.as_dict()["name"]: row.as_dict()
          for row in session.sql(f'SHOW USER PROGRAMMATIC ACCESS TOKENS FOR USER "{USER}"').collect()}
secret_exists = bool(session.sql(f"SHOW SECRETS LIKE '{SECRET_NAME}' IN SCHEMA {DATABASE}.{SCHEMA}").collect())
active = str(tokens.get(PAT_NAME, {}).get("status", "")).upper() == "ACTIVE"

if active and secret_exists:
    print(f"Reusing active PAT {PAT_NAME}.")
else:
    if PAT_NAME in tokens:
        session.sql(f'ALTER USER "{USER}" REMOVE PROGRAMMATIC ACCESS TOKEN {PAT_NAME}').collect()
    created = session.sql(
        f'ALTER USER "{USER}" ADD PROGRAMMATIC ACCESS TOKEN {PAT_NAME} '
        f"ROLE_RESTRICTION = '{ROLE}' DAYS_TO_EXPIRY = {int(PAT_DAYS)} "
        "COMMENT = 'Cortex Training quickstart notebook'"
    ).collect()[0].as_dict()
    token = {key.lower(): value for key, value in created.items()}["token_secret"]
    session.use_role(ROLE)
    verb = "ALTER SECRET" if secret_exists else "CREATE SECRET"
    clause = "SET SECRET_STRING" if secret_exists else "TYPE = GENERIC_STRING SECRET_STRING"
    session.sql(f"{verb} {SECRET_FQN} {clause} = '{token}'").collect()
    del token, created
    print(f"Stored a new {PAT_DAYS}-day PAT in {SECRET_FQN}.")

session.use_role(ADMIN_ROLE)
for statement in [
    (f"CREATE EXTERNAL ACCESS INTEGRATION IF NOT EXISTS CT_QUICKSTART_API_EAI "
     f"ALLOWED_NETWORK_RULES = ({DATABASE}.{SCHEMA}.CT_ACCOUNT_RULE) "
     f"ALLOWED_AUTHENTICATION_SECRETS = ({SECRET_FQN}) ENABLED = TRUE"),
    (f"CREATE EXTERNAL ACCESS INTEGRATION IF NOT EXISTS CT_QUICKSTART_DOWNLOAD_EAI "
     f"ALLOWED_NETWORK_RULES = ({DATABASE}.{SCHEMA}.CT_DOWNLOAD_RULE) "
     "ALLOWED_AUTHENTICATION_SECRETS = NONE ENABLED = TRUE"),
    f"GRANT USAGE ON INTEGRATION CT_QUICKSTART_API_EAI TO ROLE {ROLE}",
    f"GRANT USAGE ON INTEGRATION CT_QUICKSTART_DOWNLOAD_EAI TO ROLE {ROLE}",
]:
    session.sql(statement).collect()
print("Integrations ready. Attach CT_QUICKSTART_DB.LAB.CT_PAT and both CT_QUICKSTART integrations, save, restart, then rerun configuration.")
```

## Install and Connect

### Install Packages

After the restart, rerun the configuration cell, then run this cell. It installs the pinned Cortex Training SDK from a checksum-verified public archive and keeps the runtime's PyTorch, Snowpark, and connector versions in place.

```python
import subprocess
import sys
import tempfile
from importlib import metadata
from pathlib import Path

if sys.version_info < (3, 10):
    raise RuntimeError("Use a Container Runtime with Python 3.10 or later (the SDK requires >= 3.10).")

SDK_REVISION = "b4c26d57bcd741dce4cd63a6ed8f51cff6ba8829"
SDK_SHA256 = "a7860f487ad542204cc0f2c39137ac1be0ef97d9845942d11021e991d839b4df"
SDK_URL = f"https://github.com/snowflakedb/cortex-training/archive/{SDK_REVISION}.zip"

constraints = [f"{package}=={metadata.version(package)}" for package in
               ("torch", "snowflake-snowpark-python", "snowflake-connector-python", "numpy")]
requirements = [
    f"cortex-training @ {SDK_URL}#sha256={SDK_SHA256}",
    "transformers==4.57.6",
    "openai==2.6.1",
    "ipywidgets==8.1.7",  # Ray (loaded by Snowflake ML) uses it for rich notebook output.
    f"snowflake-ml-python=={metadata.version('snowflake-ml-python')}",
    f"matplotlib=={metadata.version('matplotlib')}",
]

with tempfile.TemporaryDirectory(prefix="ct-install-") as directory:
    constraint_path = Path(directory) / "constraints.txt"
    constraint_path.write_text("\n".join(constraints) + "\n", encoding="utf-8")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--disable-pip-version-check",
         "--constraint", str(constraint_path), *requirements],
        check=True,
    )
print("Packages installed.")
```

### Connect to Cortex Training

This cell reads the PAT from the attached secret and opens the Cortex Training client. The token is kept in memory only.

```python
import math
import random
import time
from copy import deepcopy
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import torch
from cortex_training import CortexTrainingClient, wire
from IPython.display import Markdown, display
from openai import OpenAI
from snowflake.ml.experiment import ExperimentTracking
from snowflake.snowpark.context import get_active_session
from snowflake.snowpark.secrets import get_generic_secret_string
from transformers import AutoTokenizer

session = get_active_session()
session.use_role(ROLE)
session.use_warehouse(WAREHOUSE)
session.use_database(DATABASE)
session.use_schema(SCHEMA)

pat = None
for reference in (f"{DATABASE}/{SCHEMA}/{SECRET_NAME}".lower(), f"{DATABASE}.{SCHEMA}.{SECRET_NAME}"):
    try:
        pat = get_generic_secret_string(reference)
        break
    except Exception:
        pass
if pat is None:
    # Not attached: the secret is mounted only after it is selected in the service settings.
    pat = (Path("/secrets") / f"{DATABASE}/{SCHEMA}/{SECRET_NAME}".lower() / "secret_string").read_text().strip()

client = CortexTrainingClient.from_pat(
    host=ACCOUNT_HOST, pat=pat, database=DATABASE, schema=SCHEMA,
    poll_timeout=1800,
    poll_interval=1.0, request_timeout=(10.0, 120.0), max_retries=0,
)
print(f"Connected as {session.get_current_role()} in {DATABASE}.{SCHEMA}.")
```

## Define the Policy

The planning system supplies every number and flags both comparisons, so the model never calculates. It only decides and writes. Northwind's policy is checked in this order:

| Condition | Decision | Policy |
|---|---|---|
| Suggested quantity is 0 | `HOLD` | NW-1 |
| Supplier status is WATCH | `BACKUP SUPPLIER` | NW-4 |
| Cover vs lead time is SHORT | `EXPEDITE` | NW-2 |
| Quantity vs PO cap is OVER | `SPLIT PO` (first PO at the cap) | NW-3 |
| Otherwise | `ORDER` | NW-5 |

Every answer uses the house format `DECISION: ... | QTY: ... | POLICY: NW-n | NOTE: ...`, with a one-line note for the site planner. The quantity is copied from the input or the cap.

The cell below generates 200 training decisions, 40 per decision, with half of them right at a threshold. It also creates 20 held-out SKUs, including five showcase SKUs with one per decision. NW-1005 has two triggers, a supplier on watch and short cover, so it tests the priority order. The model never sees the policy in a prompt.

```python
import random
import re

WAREHOUSES = ["Dallas", "Chicago", "Atlanta", "Denver", "Seattle", "Newark"]
HOUSE_STYLE = re.compile(
    r"DECISION: (HOLD|BACKUP SUPPLIER|EXPEDITE|SPLIT PO|ORDER) \| QTY: \d+ \| POLICY: NW-[1-5] \| NOTE: .+"
)


def sku_prompt(sku, s):
    return (
        f"Reorder check for {sku} at {s['warehouse']}. Days of cover: {s['cover_days']}. "
        f"Supplier lead time: {s['lead_days']} days. Suggested quantity: {s['suggested_qty']}. "
        f"PO cap: {s['po_cap']}. Supplier status: {s['supplier']}. "
        # The planning system flags both comparisons, so the model never compares numbers.
        f"Cover vs lead time: {'SHORT' if s['cover_days'] < s['lead_days'] else 'OK'}. "
        f"Quantity vs PO cap: {'OVER' if s['suggested_qty'] > s['po_cap'] else 'WITHIN'}."
    )


def expected_decision(s):
    site = s["warehouse"]
    if s["suggested_qty"] == 0:
        return ("HOLD", 0, "NW-1", f"Stock covers the plan. No PO; recheck {site} next cycle.")
    if s["supplier"] == "WATCH":
        return ("BACKUP SUPPLIER", s["suggested_qty"], "NW-4",
                f"Primary supplier is on watch. Place with the backup supplier and copy {site} procurement.")
    if s["cover_days"] < s["lead_days"]:
        return ("EXPEDITE", s["suggested_qty"], "NW-2",
                f"Cover runs out before the next delivery. Request air freight and alert the {site} planner.")
    if s["suggested_qty"] > s["po_cap"]:
        return ("SPLIT PO", s["po_cap"], "NW-3",
                f"Above the PO cap. Release the first PO at the cap and queue the remainder for {site}.")
    return ("ORDER", s["suggested_qty"], "NW-5", f"Standard replenishment for {site}. Release on the normal cycle.")


def expected_order(s):
    decision_name, qty, policy, note = expected_decision(s)
    return f"DECISION: {decision_name} | QTY: {qty} | POLICY: {policy} | NOTE: {note}"


def decision(answer):
    found = re.search(r"DECISION:\s*([A-Z ]+?)\s*\|.*?POLICY:\s*(NW-\d)", answer)
    return (found.group(1), found.group(2)) if found else None


def is_correct(answer, s):
    return decision(answer) == decision(expected_order(s))


def in_house_style(answer):
    return bool(HOUSE_STYLE.fullmatch(answer.strip()))


SHOWCASE = [
    ("NW-1001", {"warehouse": "Dallas", "cover_days": 30, "lead_days": 14, "suggested_qty": 144, "po_cap": 500, "supplier": "OK"}),
    ("NW-1002", {"warehouse": "Chicago", "cover_days": 5, "lead_days": 14, "suggested_qty": 240, "po_cap": 500, "supplier": "OK"}),
    ("NW-1003", {"warehouse": "Atlanta", "cover_days": 21, "lead_days": 7, "suggested_qty": 768, "po_cap": 500, "supplier": "OK"}),
    ("NW-1004", {"warehouse": "Denver", "cover_days": 60, "lead_days": 14, "suggested_qty": 0, "po_cap": 500, "supplier": "OK"}),
    ("NW-1005", {"warehouse": "Seattle", "cover_days": 9, "lead_days": 21, "suggested_qty": 360, "po_cap": 500, "supplier": "WATCH"}),
]
assert [expected_decision(s)[0] for _, s in SHOWCASE] == ["ORDER", "EXPEDITE", "SPLIT PO", "HOLD", "BACKUP SUPPLIER"]

rng = random.Random(7)
DECISIONS = ["HOLD", "BACKUP SUPPLIER", "EXPEDITE", "SPLIT PO", "ORDER"]


def random_sku(target):
    # Half of the examples sit right at a threshold, so the model learns where each rule flips.
    lead_days = rng.choice([7, 14, 21])
    edge = rng.random() < 0.5
    sku = {"warehouse": rng.choice(WAREHOUSES), "lead_days": lead_days, "po_cap": 500, "supplier": "OK",
           "cover_days": lead_days if edge else rng.randint(lead_days, 60),
           "suggested_qty": 492 if edge else 12 * rng.randint(1, 41)}
    if target == "HOLD":
        sku.update(suggested_qty=0, supplier=rng.choice(["OK", "WATCH"]), cover_days=rng.randint(0, 60))
    elif target == "BACKUP SUPPLIER":
        sku.update(supplier="WATCH", suggested_qty=12 * rng.randint(1, 75),
                   cover_days=rng.randint(0, lead_days - 1) if edge else rng.randint(0, 60))
    elif target == "EXPEDITE":
        sku.update(cover_days=lead_days - 1 if edge else rng.randint(0, lead_days - 1),
                   suggested_qty=12 * rng.randint(1, 75))
    elif target == "SPLIT PO":
        sku.update(suggested_qty=504 if edge else 12 * rng.randint(42, 80))
    assert expected_decision(sku)[0] == target
    return sku


TRAIN = [(f"NW-{2000 + i}", random_sku(DECISIONS[i % 5])) for i in range(200)]
rng.shuffle(TRAIN)
HELD_OUT = SHOWCASE + [(f"NW-{3000 + i}", random_sku(DECISIONS[i % 5])) for i in range(15)]
TRAIN_CHATS = [
    [{"role": "user", "content": sku_prompt(sku, s)}, {"role": "assistant", "content": expected_order(s)}]
    for sku, s in TRAIN
]
HELD_PROMPTS = [sku_prompt(sku, s) for sku, s in HELD_OUT]
assert len(TRAIN_CHATS) == 200 and len(HELD_OUT) == 20
print(f"{len(TRAIN_CHATS)} training decisions and {len(HELD_OUT)} held-out SKUs (5 showcase, 15 random).")
```

## Prepare Training

### Tokenize the Examples

Only the assistant's decision is trained; prompt tokens are masked from the loss. The check at the end stops the run before any GPU work if the tokenizer's chat template differs from this formatter.

```python
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, revision=TOKENIZER_REVISION, trust_remote_code=False)


def prompt_token_ids(prompt):
    return tokenizer.apply_chat_template(
        [{"role": "user", "content": prompt}], tokenize=True,
        add_generation_prompt=True, enable_thinking=False,
    )


def encode_example(messages):
    prompt, answer = messages[0]["content"], messages[1]["content"]
    prefix = prompt_token_ids(prompt)
    answer_ids = tokenizer.encode(answer, add_special_tokens=False)
    end_id = tokenizer.convert_tokens_to_ids("<|im_end|>")
    ids = prefix + answer_ids + [end_id]
    if not answer_ids or len(ids) > MAX_SEQ_LEN:
        raise ValueError("Empty answer or example exceeds MAX_SEQ_LEN.")
    weights = [0.0] * len(prefix) + [1.0] * (len(answer_ids) + 1)
    return ids, weights[1:] + [0.0]


def to_batch(conversations):
    sequences = [encode_example(messages) for messages in conversations]
    width = max(len(ids) for ids, _ in sequences)
    pad_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id
    ids_batch = [ids + [pad_id] * (width - len(ids)) for ids, _ in sequences]
    attention = [[1] * len(ids) + [0] * (width - len(ids)) for ids, _ in sequences]
    masks = [mask + [0.0] * (width - len(mask)) for _, mask in sequences]
    input_ids = torch.tensor(ids_batch, dtype=torch.long)
    kwargs = {
        "input_ids": input_ids,
        "attention_mask": torch.tensor(attention, dtype=torch.long),
        "position_ids": torch.arange(width).expand(len(sequences), -1).contiguous(),
        "use_cache": False,
    }
    context = {"input_ids": input_ids, "loss_mask": torch.tensor(masks, dtype=torch.float32)}
    return kwargs, context


for messages in TRAIN_CHATS:
    ids, mask = encode_example(messages)
    expected = tokenizer.apply_chat_template(messages, tokenize=False, enable_thinking=False)
    # The HF template adds a trailing newline after end-of-turn; it is not part of the target.
    if tokenizer.decode(ids, skip_special_tokens=False) + "\n" != expected:
        raise RuntimeError("Pinned tokenizer template differs from the formatter; stop before allocating GPUs.")
print(f"Tokenizer template matches for all {len(TRAIN_CHATS)} examples.")
```

### Configure the Job

The job uses LoRA on the attention and MLP projections, with four GPUs for sampling and four for training.

```python
LORA_CONFIG = {
    "peft_type": "Lora", "r": 32, "lora_alpha": 32, "lora_dropout": 0.0, "bias": "none",
    "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
}
JOB_BODY = {
    "hardware": HARDWARE,
    "idle_timeout_seconds": 1800,
    "sub_job_configs": [
        {
            "job_type": "sampling", "model_name": MODEL_NAME, "dtype": "bfloat16", "seed": 42,
            "inference_config": {
                "max_seq_len": MAX_SEQ_LEN, "n_gpus": SAMPLING_GPUS,
                "vllm_config": {"tensor_parallel_size": SAMPLING_GPUS, "gpu_memory_utilization": 0.8},
                "peft_config": deepcopy(LORA_CONFIG),
            },
        },
        {
            "job_type": "training", "model_name": MODEL_NAME, "dtype": "bfloat16", "seed": 42,
            "training_config": {
                "n_gpus": TRAINING_GPUS, "max_seq_len": MAX_SEQ_LEN,
                "train_batch_size": BATCH_SIZE, "gradient_clipping": 1.0,
                "model_provider": "huggingface", "attn_implementation": "flash_attention_3",
                "optimizer": {"name": "AdamW", "lr": LEARNING_RATE, "weight_decay": 0.0,
                              "betas": [0.9, 0.95], "eps": 1e-8},
                "ds_config": {"zero_optimization": {"stage": 2, "reduce_scatter": True},
                              "bf16": {"enabled": True}},
                "peft_config": deepcopy(LORA_CONFIG),
            },
        },
    ],
}
print(f"Training job: {TRAINING_GPUS + SAMPLING_GPUS} {HARDWARE} GPUs, {STEPS} steps.")
```

### Define the Primitives

Cortex Training runs the GPU work. Your loop sends each batch to `forward_backward`, applies an optimizer step, and syncs the LoRA weights to the sampler before generating answers. `release_job` cancels the training job and waits until its GPUs are free.

```python
import math

CAUSAL_CROSS_ENTROPY = {"loss_fn": "causal_cross_entropy", "post": ["compute_logprobs"], "config": {}}
TERMINAL_JOB = {"cancelled", "failed", "done", "terminated"}


def job_status(job_id):
    return str(client.get_job(job_id).get("status", "")).lower().removeprefix("job_state_")


def forward_backward(job_id, kwargs, context):
    payload = wire.dumps(
        {"args": (), "kwargs": kwargs, "context": context, "processing": CAUSAL_CROSS_ENTROPY},
        metadata={"response_options": {"format": "dssst1", "delivery": "chunked"}},
    )
    request_id = client.forward_backward(job_id, payload)
    loss = float(client.poll_request(job_id, request_id)["avg_loss"])
    if not math.isfinite(loss):
        raise RuntimeError("Non-finite loss; stop training and inspect the job.")
    return loss


def optim_step(job_id):
    client.poll_request(job_id, client.step(job_id, learning_rate=LEARNING_RATE))


def sync_weights(job_id):
    request_id = client.weight_sync(
        job_id, source_sub_job_id=f"{job_id}:training:0",
        target_sub_job_ids=[f"{job_id}:sampling:0"], weight_format="lora",
    )
    client.poll_request(job_id, request_id)


def ask(job_id, prompts):
    request_id = client.generate(
        job_id, prompts=[prompt_token_ids(prompt) for prompt in prompts],
        # max_tokens is the Cortex Training generate parameter, not the OpenAI endpoint's.
        sampling_params={"max_tokens": 96, "temperature": 0.0,
                         "stop_token_ids": [tokenizer.convert_tokens_to_ids("<|im_end|>")]},
    )
    results = client.poll_request(job_id, request_id).get("results") or []
    if len(results) != len(prompts):
        raise RuntimeError("Sampling returned an unexpected number of results.")
    return [str(result.get("text", "")).strip() if isinstance(result, dict) else str(result)
            for result in results]


def release_job(job_id, experiment_status):
    global run_open
    # Free the GPUs first, so an experiment-tracking error cannot leave the job running.
    if job_status(job_id) not in TERMINAL_JOB:
        client.cancel_job(job_id)
    deadline = time.monotonic() + 300
    while job_status(job_id) not in TERMINAL_JOB:
        if time.monotonic() > deadline:
            raise TimeoutError(f"Training job {job_id} has not stopped.")
        time.sleep(5)
    print(f"Training job {job_id} released.")
    if run_open:
        try:
            tracker.end_run(run_name, status=experiment_status)
        except TypeError:  # snowflake-ml-python before 1.54 has no status argument
            tracker.end_run(run_name)
        run_open = False
```

## Train and Compare

### Run the Training Loop

This cell creates the job, scores the untouched base model on the 20 held-out SKUs, runs 60 optimizer steps on batches of the 200 training decisions, and scores the tuned model on the same SKUs. If anything fails, it releases the training job before raising the error.

```python
run_open, run_name, tracker = False, None, None
job_id = None
try:
    job_id = client.create_job_from_body(deepcopy(JOB_BODY))["job_id"]
    client.wait_for_job(job_id)
    info = client.get_experiment_run(job_id)
    run_name = info["experiment_run_name"]
    tracker = ExperimentTracking(session=session)
    tracker.set_experiment(info["experiment_name"].split(".")[-1].strip('"'))
    tracker.start_run(run_name)
    run_open = True
    tracker.log_params({"model": MODEL_NAME, "steps": STEPS, "batch_size": BATCH_SIZE,
                        "learning_rate": LEARNING_RATE, "tokenizer_revision": TOKENIZER_REVISION})

    base_answers = ask(job_id, HELD_PROMPTS)

    losses = []
    rng = random.Random(0)
    for step in range(1, STEPS + 1):
        kwargs, context = to_batch(rng.sample(TRAIN_CHATS, BATCH_SIZE))
        loss = forward_backward(job_id, kwargs, context)
        optim_step(job_id)
        losses.append(loss)
        tracker.log_metrics({"train_loss": loss}, step=step)
        print(f"Step {step:02d}/{STEPS}: loss {loss:.3f}")
    sync_weights(job_id)
    tuned_answers = ask(job_id, HELD_PROMPTS)
except BaseException:
    if job_id:
        release_job(job_id, "FAILED")
    raise
```

### See the Effect

Each row is a held-out SKU the model never trained on. The cell prints two scores for each model: whether the decision and policy code match Northwind's policy, and whether the answer follows the house format. It then shows a table with green and red results, and a chart of the training loss and both scores.

```python
base_ok = [is_correct(answer, s) for answer, (_, s) in zip(base_answers, HELD_OUT, strict=True)]
tuned_ok = [is_correct(answer, s) for answer, (_, s) in zip(tuned_answers, HELD_OUT, strict=True)]
base_style = [in_house_style(answer) for answer in base_answers]
tuned_style = [in_house_style(answer) for answer in tuned_answers]

headline = (f"Correct decisions: base {sum(base_ok)}/20, tuned {sum(tuned_ok)}/20. "
            f"House style: base {sum(base_style)}/20, tuned {sum(tuned_style)}/20.")
print(headline)
for (sku, s), tuned in zip(HELD_OUT, tuned_answers, strict=True):
    print(f"{sku}: expected {' '.join(decision(expected_order(s)))}; tuned {decision(tuned)}")
display(Markdown(f"## {headline}"))

rows = []
for (sku, s), base, tuned, b_ok, t_ok in zip(HELD_OUT, base_answers, tuned_answers, base_ok, tuned_ok, strict=True):
    expected_name, _, expected_policy, _ = expected_decision(s)
    rows.append({
        "SKU": sku,
        "Expected": f"{expected_name} ({expected_policy})",
        "Base model": base[:70],
        "Base": "correct" if b_ok else "wrong",
        "Tuned model": tuned[:70],
        "Tuned": "correct" if t_ok else "wrong",
    })
frame = pd.DataFrame(rows)


def colour(value):
    return {"correct": "background-color: #d4edda", "wrong": "background-color: #f8d7da"}.get(value, "")


display(frame.style.map(colour, subset=["Base", "Tuned"]))

fig, (loss_ax, score_ax) = plt.subplots(1, 2, figsize=(12, 3.6))
loss_ax.plot(range(1, STEPS + 1), losses, marker="o", color="#29B5E8")
loss_ax.set(title="Training loss", xlabel="Optimizer step", ylabel="Loss")
labels = ["Correct decision", "House style"]
positions = range(len(labels))
base_scores = [sum(base_ok), sum(base_style)]
tuned_scores = [sum(tuned_ok), sum(tuned_style)]
base_bars = score_ax.bar([p - 0.2 for p in positions], base_scores, width=0.4, color="#9AA0A6", label="Base Qwen3-8B")
tuned_bars = score_ax.bar([p + 0.2 for p in positions], tuned_scores, width=0.4, color="#1F77B4", label="Northwind-tuned")
score_ax.set(ylim=(0, 22), ylabel="Held-out SKUs (of 20)", title="Base vs tuned on 20 held-out SKUs")
score_ax.set_xticks(list(positions), labels)
for bar in [*base_bars, *tuned_bars]:
    score_ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.4,
                  f"{int(bar.get_height())}", ha="center", fontsize=11, weight="bold")
score_ax.legend(loc="upper left")
plt.tight_layout()
plt.show()
plt.close(fig)
```

In one test run, the base model scored 0 of 20 on both measures, and the tuned model scored 19 of 20 on decisions and 20 of 20 on house style. The one miss had the right decision with the wrong policy code. Your results can differ.

## Save a Checkpoint

This cell saves a weights-only checkpoint, then releases the training GPUs. The checkpoint stays in Cortex Training after the job ends, and the deployment uses it.

```python
checkpoint_id = None
if job_status(job_id) in TERMINAL_JOB:
    # Rerun after the job was released: a released job cannot save, so reuse its checkpoint.
    saved = [item["checkpoint_id"] for item in client.list_checkpoints(job_id)
             if item.get("checkpoint_type") == "weights-only"]
    if len(saved) != 1:
        raise RuntimeError(f"Expected one saved checkpoint for {job_id}, found {len(saved)}. Retrain to save one.")
    checkpoint_id = saved[0]
    print("Training job already released; reusing checkpoint", checkpoint_id)
try:
    if checkpoint_id is None:
        previous = {item["checkpoint_id"] for item in client.list_checkpoints(job_id)}
        save_result = client.poll_request(job_id, client.save(job_id, checkpoint_type="weights-only"))
        deadline = time.monotonic() + 300
        while checkpoint_id is None:
            checkpoint_id = save_result.get("checkpoint_id")
            if checkpoint_id is None:
                new = [item["checkpoint_id"] for item in client.list_checkpoints(job_id)
                       if item.get("checkpoint_type") == "weights-only" and item["checkpoint_id"] not in previous]
                checkpoint_id = new[0] if len(new) == 1 else None
            if checkpoint_id is None:
                if time.monotonic() > deadline:
                    raise TimeoutError("Save finished, but its checkpoint could not be identified.")
                time.sleep(5)
except BaseException:
    release_job(job_id, "FAILED")
    raise
release_job(job_id, "FINISHED")
print("Checkpoint retained:", checkpoint_id)
```

## Deploy the Model

### Create the Deployment

This cell creates a four-GPU evaluation deployment from the checkpoint and exposes an OpenAI-compatible endpoint. Training and serving share the account's GPU cap, so it first makes sure the training job is released. If the deployment fails to start, it is dropped.

```python
release_job(job_id, "FINISHED")  # Training and serving share the GPU cap; free training first. No-op if released.
deployment_id = client.create_model_deployment({
    "deployment": {"class": "EVALUATION", "min_replicas": 1,
                   "gpus_per_replica": SERVING_GPUS, "gpu_type": HARDWARE},
    "source": {"type": "checkpoint", "job_id": job_id, "checkpoint_id": checkpoint_id},
    "inference": {"max_seq_len": MAX_SEQ_LEN},
})["deployment"]
try:
    base_url = client.wait_for_model_deployment(deployment_id)["base_url"].rstrip("/")
    if not base_url.startswith(f"https://{ACCOUNT_HOST.lower()}/"):
        raise RuntimeError("Unexpected inference URL; refusing to send the PAT there.")
except BaseException:
    client.drop_model_deployment(deployment_id)
    raise
print("base_url:", base_url)
print("model:", deployment_id)
```

### Call the Model

That's the whole client. Any OpenAI-compatible SDK works: point it at your `base_url`, use the deployment ID as the model, and send your PAT with the `X-Snowflake-Authorization-Token-Type` header. The prompt carries only the SKU's facts, no policy, so the decision comes from the tuned weights. For token-by-token output, add `stream=True`.

```python
from openai import OpenAI

northwind = OpenAI(
    base_url=base_url,
    api_key=pat,
    default_headers={"X-Snowflake-Authorization-Token-Type": "PROGRAMMATIC_ACCESS_TOKEN"},
)
response = northwind.chat.completions.create(
    model=deployment_id,
    messages=[{"role": "user", "content": "Reorder check for NW-1005 at Seattle. Days of cover: 9. Supplier lead time: 21 days. Suggested quantity: 360. PO cap: 500. Supplier status: WATCH. Cover vs lead time: SHORT. Quantity vs PO cap: WITHIN. /no_think"}],
    max_completion_tokens=128,
    temperature=0,
)
print(response.choices[0].message.content)
```

In one test run, the endpoint answered `DECISION: BACKUP SUPPLIER | QTY: 360 | POLICY: NW-4 | NOTE: Primary supplier is on watch. Place with the backup supplier and copy Seattle procurement.`, which matches the policy.

### Drop the Deployment

Evaluation deployments hold their GPUs until they are dropped. Run this cell when you finish calling the model, even if the call failed.

```python
client.drop_model_deployment(deployment_id)
print(f"Deployment {deployment_id} dropped; serving GPUs released.")
```

## Clean Up

The training job and the deployment are released by the cells above; make sure you ran the drop cell. To remove the tutorial setup, set `RUN_TEARDOWN = True` in this cell and run it. It stops if a training job or deployment is still active. Otherwise it revokes the PAT and drops both integrations, the database (which removes the secret and experiments), the warehouse, and the role. A saved checkpoint is not recoverable after teardown. Suspend or delete the notebook service when you are done.

```python
RUN_TEARDOWN = False  # Set True only when finished. This permanently deletes the setup.

if not RUN_TEARDOWN:
    print("Teardown skipped. Set RUN_TEARDOWN = True to remove the tutorial setup.")
else:
    active_jobs = [j for j in client.list_jobs()
                   if str(j.get("status", "")).lower().removeprefix("job_state_") not in TERMINAL_JOB]
    active_deployments = [d for d in client.list_model_deployments()
                          if d.get("status") not in {"DROPPED", "FAILED", "TERMINATED"}]
    if active_jobs or active_deployments:
        raise RuntimeError(f"{len(active_jobs)} job(s) and {len(active_deployments)} deployment(s) still active; nothing was dropped.")
    session.use_role(ADMIN_ROLE)
    remaining = []
    for statement in [
        f'ALTER USER "{USER}" REMOVE PROGRAMMATIC ACCESS TOKEN IF EXISTS {PAT_NAME}',
        "DROP EXTERNAL ACCESS INTEGRATION IF EXISTS CT_QUICKSTART_API_EAI",
        "DROP EXTERNAL ACCESS INTEGRATION IF EXISTS CT_QUICKSTART_DOWNLOAD_EAI",
        f"DROP DATABASE IF EXISTS {DATABASE}",
        f"DROP WAREHOUSE IF EXISTS {WAREHOUSE}",
        f"DROP ROLE IF EXISTS {ROLE}",
    ]:
        try:
            session.sql(statement).collect()
            print("Done:", statement)
        except Exception as exc:
            remaining.append(statement)
            print(f"Failed ({type(exc).__name__}): {statement}")
    if remaining:
        print("Run these in a worksheet as", ADMIN_ROLE + ":")
        print(";\n".join(remaining) + ";")
    else:
        print("Tutorial setup removed. Delete the notebook service when you are done.")
```

## Conclusion And Resources

Congratulations! You've successfully post-trained an open-weight model on a company decision policy with Cortex Training, measured it against the base model, and deployed it as an OpenAI-compatible endpoint.

### What You Learned
- Cortex Training runs the GPU work while your notebook controls the training loop
- A small set of policy examples can teach an open model a company's decisions and house style without the policy in the prompt
- Scoring the base and tuned models on the same held-out examples shows what post-training changed
- A weights-only checkpoint can be deployed as an OpenAI-compatible endpoint and called with the OpenAI SDK

### Related Resources
- [Cortex Training SDK source](https://github.com/snowflakedb/cortex-training)
