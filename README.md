# Becuz

> **Track:** The Agent That Can Explain Why
> **Sponsor technology:** Zetaris, Meterless (Nightshift and four engines), NVIDIA Nemotron
> **Run:** `uv run python run.py --input input_examples/example_1.json`, or `uv run python server.py` and `POST /run` on port 8000

Becuz tells a Nigerian mini-mart owner why profit moved this week, in naira, with a receipt for every
claim. A receipt is the SQL that ran, the record IDs it found, and a second agent's independent re-run
of that SQL.

## 1. Problem

The owner asks, "Why is my profit down this week?" The answer is spread across the POS till, the bank
statement, supplier invoices and expenses, and nobody in the shop has time to join them by hand.
Becuz joins those records through Zetaris and reports:

- this week's profit against the average of the 4 weeks before
- ranked causes, each with its naira impact, its receipt and a confidence rating
- causes it tested and ruled out, with the reason
- how much of the change it explained, and how much is left unexplained
- cash gaps, kept apart from profit: transfers recorded at the till that never reached the bank. The
  sale happened, so it still counts as profit, but the money is missing
- causes the owner confirmed in earlier runs, and whether each one happened again
- one action per cause for the owner to take this week

SQL computes every naira figure. The model rates the evidence and writes a note for the owner. It
never computes or changes a number.

## 2. Agents

Four agents share one LangGraph state. The claims themselves live in a shared World Model, so every
agent sees the same claims and every status change is kept.

| Agent | Responsibility | Can block or retry? |
|---|---|---|
| Planner | Opens a signed investigation contract, recalls causes the owner confirmed before, measures the profit tree, and orders the causes to test | Yes: refuses questions outside the contract |
| Investigator | Measures one cause with its SQL template through Zetaris and proposes a claim with its record IDs | Yes: re-tests a claim the Checker sends back |
| Checker | Re-runs the claim's SQL itself, then supports, rejects or sends it back. Asks Nemotron to rate the supported and rejected claims | Yes: sends a claim back up to 2 times, then rejects it |
| Writer | Builds the report from supported claims only. The report schema re-checks that every figure adds up | Yes: an invalid report fails instead of being returned |

```text
            ┌──────────── sent back (max 2) ────────────┐
            ▼                                           │
Planner ─► Investigator ─► Checker ─► next cause? ──────┤
                                          │ no          │ yes
                                          ▼             │
                                        Writer          └─► Investigator
```

## 3. What makes this an agent system

- The Checker does not trust the Investigator. It re-runs the SQL and compares the result to ±₦1.
- A mismatch goes back to the Investigator for a re-test, up to 2 times.
- A claim is rejected when its loss is below ₦1,000, when no records back it, or when it is not a loss.
- A cause the owner confirmed in an earlier run is tested first next time. If it fails, its memory
  loses confidence and is flagged for review.
- A Zetaris timeout, network error or Zetaris internal fault retries only the query that failed, up to 4
  attempts with waits of 10, 20 and 40 seconds, and each retry is written to the trace by the agent that hit it.
- The Checker hands each model rating to a background worker and moves on to the next cause. One
  worker keeps the Markovian chain in order, and the Writer waits for every rating before the report.
- A run stops after 60 steps.
- Every decision goes to a per-run trace with the agent, target agent, confidence, retry count and status.

## 4. Sponsor technology

**Zetaris is where the shop's data is joined and checked.** The four sources (POS, bank, books and
context) are CSV files in S3, registered as Lightning databases. A Unified Semantic Layer (USL) named
`becuz` declares the shop's 12 tables and their keys. Two of them do work inside Zetaris:

- `daily_pnl` computes the profit tree for each day: sales minus cost of goods, wastage and expenses.
  It also keeps the day's missing transfers in their own column, outside profit.
- `transfer_check` matches each transfer sale to a bank credit.

The data-quality rule `transfer_reached_bank` runs on the same match. The agent connects as a
non-admin user with `SELECT` on the USL only, so Zetaris itself refuses any write or raw-source read.

**Meterless Nightshift runs every model call.** The Checker asks for `meterless/judge`, and Nightshift
routes it to an NVIDIA Nemotron model. Each call is recorded with the model that answered it and its
Nightshift receipt ID.

**Which agent uses which Nemotron model:**

| Agent | Nemotron model | What it does | Calls per run |
|---|---|---|---|
| Checker | `nvidia/nemotron-3.5-lightning-30b-a3b` (Nightshift Race lane) | Rates the evidence for each supported or rejected claim and writes a note for the owner | One per tested cause (6 on `s01`) |
| Planner, Investigator, Writer | none | SQL only; they never call a model | 0 |

Nightshift also has a Judge lane (`nvidia/nemotron-3-ultra-550b-a55b`) for its own scoring. **Receipts:**
[`output_examples/live_s01_receipts.jsonl`](output_examples/live_s01_receipts.jsonl) is the receipt log
from a real live run: one `model` line per call with the model that answered and its request ID, and one
`model_receipt` line per call once Nightshift signed it. The report and trace from the same run are
[`live_s01_output.json`](output_examples/live_s01_output.json) and
[`live_s01_trace.jsonl`](output_examples/live_s01_trace.jsonl), and its 27 Zetaris queries against the
`becuz` USL are in [`live_s01_queries.jsonl`](output_examples/live_s01_queries.jsonl). Your own runs write the same log to
`logs/ledger.jsonl`; run `uv run python verify_receipts.py` to add the signed receipts.

**Four Meterless engines, implemented in `becuz/engines/`:**

| Engine | What it does in Becuz | Log |
|---|---|---|
| Scout Intent | Turns the question into a signed contract: the intent, the 10 tables the agent may read, a budget of 80 queries, and a 5-minute expiry. Every query passes through the contract | `logs/scout.jsonl` |
| World Model | The shared list of claims. Each verdict is a new status edge, so a claim's full history is kept | `logs/world.jsonl` |
| H-MEM | Remembers causes the owner confirmed and how they were found. They are recalled and tested first in later runs | `logs/hmem.json`, `logs/hmem.jsonl` |
| Markovian | Runs the Checker's model calls as a chain. Each call carries one short summary of earlier verdicts instead of the whole history, so every call stays the same size | `logs/markovian.jsonl` |

## 5. Tech stack

| Component | Technology |
|---|---|
| Language | Python 3.12, managed with uv |
| Orchestration | LangGraph |
| Data access | Zetaris REST API and USL |
| Model runtime | Meterless Nightshift |
| Models | NVIDIA Nemotron, through Nightshift |
| Report contract | Pydantic, exported to `docs/investigation.schema.json` |
| Sample mode | DuckDB, with the same Spark SQL translated by sqlglot |
| API | Standard-library HTTP server (`server.py`) |
| Logging | JSONL in `logs/` and stdout |
| Container | Docker, sample mode |

## 6. Setup

You need Python 3.12 and [uv](https://docs.astral.sh/uv/).

```powershell
git clone https://github.com/adr1en360/Becuz.git
cd Becuz
uv sync
copy .env.example .env
```

### Sample mode (no accounts needed)

```powershell
$env:SAMPLE_MODE = "1"
uv run python run.py --input input_examples/example_1.json
```

This runs the whole investigation offline. See [Sample mode](#8-sample-mode).

### Docker (sample mode)

```powershell
docker build -t becuz .
docker run --rm -p 8000:8000 becuz
curl.exe -X POST http://127.0.0.1:8000/run -H "Content-Type: application/json" -d "@input_examples/example_1.json"
```

The image runs sample mode only and never contains `.env`. Live mode needs Nightshift running on your
machine, so run it outside Docker.

### Live mode

Fill in `.env`, which is in `.gitignore`.

1. **Nightshift.** Install and start Meterless Nightshift, then add your NVIDIA key in its Providers
   tab. The NVIDIA key never goes in `.env`. Becuz reads the Nightshift token from
   `%LOCALAPPDATA%\ai.meterless.runtime\proxy-token`. Then seat two cloud lanes in **Lanes**:
   - a **Race** lane with `nvidia/nemotron-3.5-lightning-30b-a3b` (for example the job "Extract structured
     data"). It answers the Checker's ratings. Without any lane, Nightshift falls back to its own routing
     and ignores the model Becuz asks for.
   - a **Judge** lane with `nvidia/nemotron-3-ultra-550b-a55b` ("Score different answers"). Nightshift
     keeps one non-racing judge in every setup.
2. **Shop data in S3.** Upload one scenario's CSVs to `s3://<bucket>/becuz/<scenario>/`, without
   `answer_key.json`:

   ```powershell
   aws s3 cp data/scenarios/s01 s3://<bucket>/becuz/s01/ --recursive --exclude answer_key.json
   ```

3. **Zetaris, as admin.** Set `ZETARIS_REST_URL`, `ZETARIS_ORG_ID`, `ZETARIS_ADMIN_API_KEY`,
   `S3_BUCKET`, `AWS_REGION`, `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`. Each script prints its
   statements first and sends nothing until you add `--apply`:

   ```powershell
   uv run python -m scripts.zetaris_setup s01            # dry run
   uv run python -m scripts.zetaris_setup s01 --apply    # register the 4 sources and 10 tables
   uv run python -m scripts.zetaris_usl --apply          # build the becuz USL and its data-quality rule
   ```

   If a statement fails, fix the cause and resume with `--apply --start <n>`.
4. **Zetaris, agent user.** Create a non-admin user, grant it `SELECT` on the `becuz` USL in Access
   Control, and put its key in `ZETARIS_API_KEY`.

Then check every connection:

```powershell
uv run python smoke.py
```

```text
config   PASS  zetaris=ok nightshift=ok
zetaris  PASS  daily_pnl up to 2026-10-18 via=zetaris
model    PASS  via=nightshift model=nvidia/nemotron-3-ultra-550b-a55b
agent    PASS  sample s01: 4 cause(s) supported
```

## 7. Usage

From the command line:

```powershell
uv run python run.py --input input_examples/example_1.json
```

Or start the server on `127.0.0.1:8000`:

```powershell
uv run python server.py
curl.exe -X POST http://127.0.0.1:8000/run -H "Content-Type: application/json" -d "@input_examples/example_1.json"
```

| Route | Returns |
|---|---|
| `POST /run` | Runs the investigation and returns the report as JSON. `400` with a message for a bad request |
| `POST /runs` | Starts the investigation in the background and returns `202` with its `run_id` at once. Use this for a live run, which takes minutes |
| `GET /runs/<run_id>` | The run's `status` (`running`, `complete` or `failed`), its trace `events` so far, and the `report` once complete |
| `POST /confirm` | `{"run_id": "...", "cause_id": "..."}`: the owner confirms a supported cause, and H-MEM stores it for the next run |
| `GET /health` | Whether sample mode is on and which providers are configured |

**Request:**

```json
{
  "question": "Why is my profit down this week?",
  "scenario": "s01"
}
```

`question` is required. `week_start` (like `2026-10-12`) is optional and starts the 7-day week to explain;
without it Becuz takes the latest full week in the data. `scenario` (`s01` to `s05`) applies to sample mode only.

**Response (abridged, from `output_examples/example_1_output.json`):**

```json
{
  "status": "complete",
  "mode": "sample",
  "headline": {"current_ngn": 241717.0, "baseline_ngn": 379411.75, "change_ngn": -137694.75, "change_pct": -36.3},
  "causes": [
    {
      "rank": 1,
      "cause_id": "supplier_cost_rise",
      "title": "A supplier raised the unit cost of a product",
      "impact_ngn": -46992.0,
      "confidence": 0.7,
      "evidence": [{
        "table": "becuz.supplier_invoices",
        "sql": "SELECT ROUND(-COALESCE(SUM(q.qty * (c.final_cost - c.base_cost)), 0), 2) AS effect_ngn ...",
        "row_ids": ["INV-0281"],
        "value_ngn": -46992.0,
        "check": {"match": true, "rerun_value_ngn": -46992.0, "via": "sample-rules"}
      }]
    }
  ],
  "cash_gaps": [
    {"cause_id": "transfer_leakage", "title": "Transfers recorded at the till never reached the bank",
     "impact_ngn": -28360.0, "evidence": [{"table": "becuz.transfer_check", "row_ids": ["SL-03043", "SL-03067", "..."]}]}
  ],
  "ruled_out": [{"cause_id": "pos_charge_rise", "reason": "The records show no loss from this cause this week."}],
  "convergence": {"explained_ngn": -142026.0, "explained_pct": 103.1, "unexplained_ngn": 4331.25},
  "summary": {
    "what_happened": "Profit this week was ₦241,717, which is ₦137,695 less than a usual week (₦379,412).",
    "why": ["A supplier raised the unit cost of a product. This cost you ₦46,992.", "..."],
    "cash": ["₦28,360 from 6 transfer sales was recorded at the till but never reached the bank. The sales still count toward your profit, but this money is missing from your account."]
  },
  "stats": {"zetaris_queries": 27, "model_calls": 0, "retries": 0}
}
```

The full contract is in `docs/investigation.schema.json`.

### Web UI

`web/` holds the owner-facing report, a Next.js app that renders the Investigation JSON and computes
nothing itself. With the server running (sample or live), start it in a second terminal:

```powershell
cd web
npm install
npm run dev      # http://localhost:3000
```

See `web/README.md` for building and regenerating its types from the schema.

### Confirming a cause

After a run, the owner can confirm a cause it found:

```powershell
uv run python run.py --confirm <run_id> transfer_leakage
```

Only a cause the Checker supported in that run can be confirmed. H-MEM stores it, and the next run
tests it first and reports what happened in `memory`:

```powershell
$env:SAMPLE_MODE = "1"
uv run python run.py --input input_examples/example_2.json      # note the run_id
uv run python run.py --confirm <run_id> transfer_leakage
uv run python run.py --input input_examples/example_1.json
```

```json
"memory": [{
  "cause_id": "transfer_leakage", "held_again": true, "confidence_before": 0.7, "confidence_after": 0.75,
  "message": "You confirmed that transfers recorded at the till never reached the bank after an earlier run, so Becuz checked it first this time. It happened again this week."
}]
```

If a remembered cause does not happen again, its memory loses confidence and is flagged for review.

### Examples

| Input | Scenario | What the agent finds |
|---|---|---|
| `input_examples/example_1.json` | `s01`: three planted profit causes, missing transfers, and natural day-to-day noise | 4 profit causes and a ₦28,360 cash gap; POS charges ruled out |
| `input_examples/example_2.json` | `s04`: missing transfers only | Profit did not fall, but ₦33,100 in transfers never reached the bank; falling sales and POS charges ruled out |
| `input_examples/example_3.json` | `s05`: a normal week | Nothing to explain; every cause ruled out |

Each output and its trace are in `output_examples/`, saved from real sample-mode runs. The live run of
`s01` through Zetaris and Nightshift is saved too (`live_s01_*`): it returned the same findings and naira
figures as sample mode, with each rating from Nemotron 3.5 Lightning.

## 8. Sample mode

**Judges can run all of Becuz in sample mode, with no accounts, keys or network.** Every sample-mode
run does the real work again; nothing is replayed.

`SAMPLE_MODE=1` runs the full investigation with an empty `.env` and no network. The same Spark SQL runs
on DuckDB over the scenario's CSVs: the USL tables, including `daily_pnl` and `transfer_check`, are
built locally from the same activation queries Zetaris runs. The Checker's rating comes from fixed rules
instead of a model, and the report and trace label it `sample-rules`. Nothing is read from
`output_examples/`.

## 9. Failure handling

| Failure | Behaviour |
|---|---|
| Zetaris timeout, network error, or Zetaris internal fault (`Could not create ResultSet`, `TTransportException`) | That query is retried, up to 4 attempts with waits of 10, 20 and 40 seconds, with a `retry_query` line in the trace. The ledger records each query's `query_id` and `duration_ms` |
| Zetaris refuses a query | The run stops with an error. It is not retried |
| A re-check does not match the claim | The Checker sends it back. After 2 retries it is rejected |
| Data missing for a cause | The cause is listed as not tested, never read as zero |
| Nightshift fails or returns an unusable reply | One retry. Then the SQL verdict stands, the confidence is empty, and the report status is `partial` |
| A question outside the contract | `400`: "Becuz answers questions about why your profit changed" |
| Malformed input | `400` with a validation message |
| Query budget used up, or contract expired | The query is refused; an expired contract is re-issued and linked to the first |
| A run that loops | Stopped after 60 steps |

## 10. Logs

The app creates `logs/` on first write.

`logs/trace-<run_id>.jsonl` has one line per agent decision, also printed to stderr. Each line has
`timestamp`, `run_id`, `agent_name`, `action`, `input_summary`, `output_summary`, `target_agent`,
`confidence`, `retry_count` and `status`, plus the engine, model and route where they apply.

`logs/ledger.jsonl` has one line per Zetaris query, model call or error, with the model that answered
and its Nightshift request ID. Nightshift signs its receipt after the call returns. Once it settles, run:

```powershell
uv run python verify_receipts.py
```

It adds a `model_receipt` line for each signed request.

## 11. Safety

- Every SQL statement passes a read-only check first: `SELECT`, `WITH`, `SHOW`, `DESCRIBE` and
  `EXPLAIN` only. Multiple statements, unreadable quoting, Spark functions that run Java and script
  transforms are rejected.
- The agent's Zetaris user can read only the `becuz` USL. Only the setup scripts use the admin key.
- The model is told to treat record text as data, never as instructions, and its reply is used only
  as a rating and a note.
- Logs redact key patterns before writing. `.env` is never committed.
- No model weights are downloaded and no local GPU is needed.

## 12. Data

All shop data is synthetic, generated from a fixed seed by `data/generator.py`. No real shop, customer
or bank data is used. See `data/README.md` for the five scenarios.

## 13. Configuration

`.env.example` lists every setting with placeholder values.

| Variable | Default | Purpose |
|---|---|---|
| `ZETARIS_REST_URL` | none | Zetaris REST base: `https://api.<cluster-id>.cloud.zetaris.com/api/v1.0` |
| `ZETARIS_ORG_ID` | none | Zetaris organisation ID, a number |
| `ZETARIS_API_KEY` | none | The agent user's key |
| `ZETARIS_ADMIN_API_KEY` | none | Admin key, used only by the setup scripts |
| `S3_BUCKET`, `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | none | Used only by `scripts.zetaris_setup` |
| `METERLESS_BASE_URL` | `http://127.0.0.1:8088/v1` | Nightshift endpoint |
| `METERLESS_RUNTIME_TOKEN` | read from the Nightshift token file | Override for the Nightshift token |
| `LEDGER_PATH` | `logs/ledger.jsonl` | Event ledger; `none` turns it off |
| `TRACE_PATH` | `logs/trace.jsonl` | Traces and engine logs go in this file's folder; `none` turns them off |
| `SAMPLE_MODE` | `0` | `1` runs offline on the bundled shop data |
| `SERVER_HOST`, `SERVER_PORT` | `127.0.0.1`, `8000` | Server address |

## 14. Tests

The tests run offline and need no credentials.

```powershell
uv run python -m unittest discover -s tests -p "test_*.py"
```

They cover the generator, the SQL templates against the answer keys, the read-only guard, the report
schema, the server, and the four engines. The H-MEM, World Model and Markovian tests port the Meterless
conformance cases by ID; the Scout Intent tests check the rules in its spec, which has no conformance suite.
`BECUZ_LIVE=1` adds a test that compares the profit tree from live Zetaris with sample mode.

## 15. Limitations

- Findings show correlation, not proven causation.
- The shop data is synthetic.
- A live run is slow: the `s01` run took about 7 minutes (the report records 411 seconds). The Zetaris work finishes in about 3
  minutes; the rest is the six Nemotron ratings, which take 40 to 75 seconds each through Nightshift and
  run one after another because each carries the earlier verdicts (Markovian). Sample mode takes about a
  second.
- The Markovian token savings are estimates (4 characters per token), not measured counts, and they are
  small or negative when a run judges only a few claims.

## 16. License

MIT. See `LICENSE`.
