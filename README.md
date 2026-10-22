# Becuz

Becuz is an agent that tells a Nigerian mini-mart owner why profit moved this
week, in naira, with a receipt for every claim. A receipt is the SQL that ran,
the record IDs it found, and an independent re-check by a critic step.

Open Agent Hackathon 2026, Track 2: The Agent That Can Explain Why.
Team: Adrien (agent and data) and tmb (UI).

> **Status.** The base works today. It queries Zetaris over REST behind a
> read-only SQL guard, calls models through Meterless Nightshift, and logs every
> call to a JSONL ledger. The Becuz investigation agent in `becuz/` (LangGraph)
> is not built yet. Sections marked "planned" describe work in progress.

## Contents

- [What it does](#what-it-does)
- [Install](#install)
- [Run](#run)
- [Sample mode](#sample-mode)
- [Configuration](#configuration)
- [Logs and receipts](#logs-and-receipts)
- [Safety](#safety)
- [Sponsor technology](#sponsor-technology)
- [Tests](#tests)
- [Limitations](#limitations)
- [Further reading](#further-reading)

## What it does

The owner asks a question like "Why is my profit down this week?" The answer
is spread across the POS till, the bank statement, supplier invoices and
expenses. Becuz joins those records through Zetaris and reports:

- profit for the period against a 4-week baseline
- ranked causes, each with its naira impact and a receipt
- hypotheses it tested and ruled out, with the reason
- how much of the drop it explained, and what is left unexplained
- checks for the owner to make this week, and questions only the owner can answer

SQL does every calculation. The model frames the question, proposes causes,
judges evidence and writes the summary. It never computes a naira figure.
The full design is in [docs/PRD.md](docs/PRD.md).

### Working now

- Zetaris REST client with a read-only SQL guard (`base/zetaris.py`, `base/tools.py`).
- Nightshift as the only model provider (`base/nightshift.py`, `base/pipeline.py`).
- A JSONL ledger of every model call, query and blocked request, plus a step trace.
- Intent routing in `base/scout.py`. It sends each request to SQL, to the model, or blocks it.
- Sample mode, so the base runs with no credentials.
- An HTTP server with `GET /`, `GET /health` and `POST /ask`.

### Planned

- The LangGraph investigation graph in `becuz/`: intake, frame, recall,
  decompose, hypothesize, investigate, verify, converge, report.
- Synthetic shop data for three scenarios, registered as four Zetaris sources.
- `run.py --input`, `POST /run`, and owner confirmation with `run.py --confirm`.
- An eval over the three scenarios (`python -m becuz.eval`).
- A Next.js UI in `web/`.

The build order is in [docs/PLAN.md](docs/PLAN.md).

## Install

You need Python 3.12 and [uv](https://docs.astral.sh/uv/).

```powershell
git clone <repo-url> Becuz
cd Becuz
uv sync
```

For live runs you also need:

1. A Zetaris instance and API key. Copy `.env.example` to `.env` and fill in
   `ZETARIS_REST_URL`, `ZETARIS_ORG_ID` and `ZETARIS_API_KEY`. Use the
   `api.<cluster-id>.cloud.zetaris.com/api/v1.0` host, not the browser host.
   Details are in [ZETARIS-CONNECTION.md](ZETARIS-CONNECTION.md).
2. Meterless Nightshift running locally. Add your NVIDIA key in Nightshift's
   Providers tab. The key does not go in `.env` or anywhere in this repo.
   The app reads the Nightshift token from
   `%LOCALAPPDATA%\ai.meterless.runtime\proxy-token`. Set
   `METERLESS_RUNTIME_TOKEN` only to override it.

Keep `.env` out of git. It is already in `.gitignore`.

## Run

Check every connection first:

```powershell
uv run python smoke.py
```

It prints four lines, `config`, `zetaris`, `model` and `agent`, each `PASS` or
`FAIL`.

Send one request from the command line:

```powershell
uv run python run.py "SELECT 1 AS one"
uv run python run.py "Summarize the latest sales trend in one sentence."
uv run python run.py "SELECT 1 AS one" --trace
```

`--trace` prints the agent steps. `--full` prints the whole query response
instead of a three-row preview.

Start the server:

```powershell
uv run python server.py
```

It listens on `127.0.0.1:8000` by default.

| Route | What it returns |
| --- | --- |
| `GET /` | A browser page with a request box |
| `GET /health` | Sample-mode flag and whether Zetaris and Nightshift are configured |
| `POST /ask` | `{"request": "..."}` in, the agent result and trace out |

```powershell
curl.exe -X POST http://127.0.0.1:8000/ask -H "Content-Type: application/json" -d '{\"request\": \"SELECT 1 AS one\"}'
```

TODO: three sample inputs in `input_examples/` and their real outputs in `output_examples/`.

TODO: demo video link.

## Sample mode

Sample mode runs with an empty `.env`, no network, and Zetaris and Nightshift
stopped.

```powershell
$env:SAMPLE_MODE="1"
uv run python smoke.py
uv run python run.py "SELECT 1 AS one"
uv run python server.py
```

`SAMPLE_MODE` accepts `1`, `true`, `yes` or `on`. Unset it for live runs.

Today, sample mode in the base returns fixed rows and fixed answers, and the
ledger marks those events `via=sample`. The planned Becuz sample mode runs the
same SQL templates on DuckDB over the scenario CSVs and replaces model steps
with rules computed from that run's data. It never replays a saved output.

## Configuration

All settings come from environment variables. `.env.example` lists them with
placeholder values.

| Variable | Default | Purpose |
| --- | --- | --- |
| `ZETARIS_REST_URL` | none | Zetaris REST base, ending in `/api/v1.0` |
| `ZETARIS_ORG_ID` | none | Zetaris organisation ID |
| `ZETARIS_API_KEY` | none | Zetaris API key |
| `METERLESS_BASE_URL` | `http://127.0.0.1:8088/v1` | Nightshift endpoint |
| `METERLESS_MODEL` | `meterless/auto` | Model or routing mode sent to Nightshift |
| `METERLESS_RUNTIME_TOKEN` | read from the Nightshift token file | Override for the Nightshift token |
| `SAMPLE_MODE` | `0` | Run without Zetaris or Nightshift |
| `LEDGER_PATH` | `logs/ledger.jsonl` | Event ledger; `none` turns it off |
| `TRACE_PATH` | `logs/trace.jsonl` | Agent step trace; `none` turns it off |
| `MEMORY_PATH` | `logs/memory.json` | Local memory; `none` turns it off |
| `AGENT_POLICY` | empty | Policy as `module:Class`; empty uses the Scout policy |
| `MAX_STEPS` | `6` | Step limit per run |
| `SERVER_HOST`, `SERVER_PORT` | `127.0.0.1`, `8000` | Server address |

### Provider order

Every model call goes to Nightshift at `METERLESS_BASE_URL` with
`METERLESS_MODEL`. There is no second provider. If Nightshift is down, times
out, returns an HTTP error, reports a retired model, or sends an empty answer,
the call raises `ProviderError` and the ledger records the failure. Use
sample mode to run without Nightshift.

### Nemotron models

`meterless/auto` works without a pinned model. To pin one, seat it as a lane in
Nightshift.

| Use | Model |
| --- | --- |
| Fast lane | `nvidia/nemotron-3.5-lightning-30b-a3b` |
| Deep lane (critic) | `nvidia/nemotron-3.5-super-vl-120b-a12b` |
| Spare | `nvidia/nemotron-3-super-120b-a12b` |
| Spare | `nvidia/nemotron-3-ultra-550b-a55b` |

Do not seat `nvidia/nemotron-3-nano-30b-a3b` or
`nvidia/llama-3.3-nemotron-super-49b-v1.5`. Both are on the deprecation list.

## Logs and receipts

The app creates `logs/` on first write.

`logs/ledger.jsonl` has one line per model call, query, blocked request or
error. Each line includes:

- `kind`: `model`, `query`, `blocked`, `error` or `model_receipt`
- `tool`: `ask_model`, `query_data` or `blocked`
- `via`: `nightshift`, `zetaris` or `sample`
- `model`: the model that handled the request
- `request_id`: the Nightshift request ID
- `signed`: true when the matching Nightshift receipt carries a `_proof`

The ledger redacts known key patterns (`nvapi-...`, `Bearer ...`) before
writing. A failed ledger write prints to stderr and does not fail the answer.

Nightshift writes its receipt after the model call returns, so `signed` on a
model event reflects the moment of the call. Once the runtime settles, run:

```powershell
uv run python verify_receipts.py
```

It appends one `kind=model_receipt` line with `signed=true` for each Nightshift
request whose receipt has a `_proof`.

`logs/trace.jsonl` has one line per agent step with the run ID, step, tool,
arguments, status, error and duration.

## Safety

- Only read-only SQL reaches Zetaris: `SELECT`, `WITH`, `SHOW`, `DESCRIBE`,
  `EXPLAIN`. `EXPLAIN ANALYZE` is limited to `SELECT` and `WITH`, and may run
  the query while planning it.
- The guard rejects multiple statements. It blanks quoted strings and comments
  before scanning for keywords.
- Scout blocks direct write or delete requests before any model call. A
  question about how to update data goes to the model, which has no write tool.
- The app never downloads model weights and needs no local GPU.

## Sponsor technology

| Sponsor | Role in Becuz | State |
| --- | --- | --- |
| Zetaris | The data layer. Every query goes through the Zetaris REST API after the read-only guard. The planned investigation runs all metric, evidence and critic queries there, including the join of till transfers against bank credits. | REST client and guard working; Becuz data sources planned |
| Meterless Nightshift | The only AI provider. Every model call goes through `Pipeline.ask_messages` to Nightshift, and the ledger records the model and receipt. | Working |
| Meterless engines | Scout Intent (signed investigation contract), H-MEM (owner-confirmed causes), World Model (shop entities linked to source rows) and Markovian (compact critic state). Placement is in [docs/PRD.md](docs/PRD.md) §6. | Planned |
| NVIDIA Nemotron | Reached through Nightshift only. The plan puts light steps on Nemotron 3.5 Lightning and the critic on Nemotron 3.5 Super, with the model logged on every request. | Routing to be confirmed |

TODO: engine test results and the Nemotron models seen in the ledger.

## Tests

The tests run offline and need no credentials.

```powershell
uv run python -m unittest discover -s tests -p "test_*.py" -v
```

`tests/test_scout.py` checks Scout routing against the cases in
`scout_cases.json`.

TODO: eval results for the three scenarios.

## Limitations

- The Becuz agent is not built yet. Today the base answers single SQL or model
  requests.
- Base sample mode returns fixed rows and answers, not a real investigation.
- Shop data will be synthetic, and findings will show correlation, not proven
  causation.
- Nightshift has no fallback provider. If it is down, live model calls fail.

TODO: architecture diagram.

## Further reading

- [docs/PRD.md](docs/PRD.md): problem, scope, data contract and agent design
- [docs/PLAN.md](docs/PLAN.md): build slices and schedule
- [SCAFFOLD.md](SCAFFOLD.md): how to plug a policy and tools into the base
- [ZETARIS-CONNECTION.md](ZETARIS-CONNECTION.md): Zetaris REST setup and preflight
- [AGENTS.md](AGENTS.md): rules for coding agents working in this repo
