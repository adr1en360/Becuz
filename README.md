# Becuz

> **Track:** The Agent That Can Explain Why
> **Sponsor technology:** Zetaris, Meterless Nightshift, NVIDIA Nemotron
> **Run:** `uv run python run.py "<request>"`, or `uv run python server.py` and `POST /ask` on port 8000

Becuz tells a Nigerian mini-mart owner why profit moved this week, in naira,
with a receipt for every claim. A receipt is the SQL that ran, the record IDs it
found, and an independent re-check by a critic step.

## Problem

The owner asks, "Why is my profit down this week?" The answer is spread across
the POS till, the bank statement, supplier invoices and expenses, and nobody in
the shop has time to join them by hand. Becuz joins those records through
Zetaris and reports:

- profit for the period against a 4-week baseline
- ranked causes, each with its naira impact and a receipt
- hypotheses it tested and ruled out, with the reason
- how much of the drop it explained, and what is left unexplained
- checks for the owner to make this week, and questions only the owner can answer

SQL does every calculation. The model frames the question, proposes causes,
judges evidence and writes the summary. It never computes a naira figure.

## Tech stack

| Component | Technology |
| --- | --- |
| Language | Python 3.12, managed with uv |
| Data access | Zetaris REST API |
| Model runtime | Meterless Nightshift |
| Models | NVIDIA Nemotron, through Nightshift |
| API | Standard-library HTTP server (`server.py`) |
| Logging | JSONL in `logs/` |

## Setup

You need Python 3.12 and [uv](https://docs.astral.sh/uv/).

```powershell
git clone <repo-url> Becuz
cd Becuz
uv sync
copy .env.example .env
```

Fill in `.env`, which is already in `.gitignore`:

1. **Zetaris.** Set `ZETARIS_REST_URL`, `ZETARIS_ORG_ID` and `ZETARIS_API_KEY`.
   The URL is the API host, `https://api.<cluster-id>.cloud.zetaris.com/api/v1.0`,
   not the browser host. The org ID is a number.
2. **Meterless Nightshift.** Install and start Nightshift, then add your NVIDIA
   key in its Providers tab. The NVIDIA key never goes in `.env`. The app reads
   the Nightshift token from `%LOCALAPPDATA%\ai.meterless.runtime\proxy-token`;
   set `METERLESS_RUNTIME_TOKEN` only to override it.

Then check every connection:

```powershell
uv run python smoke.py
```

It prints four lines, `config`, `zetaris`, `model` and `agent`, each `PASS` or
`FAIL`.

## Usage

Send one request from the command line:

```powershell
uv run python run.py "SELECT 1 AS one"
uv run python run.py "Summarize the latest sales trend in one sentence."
uv run python run.py "SELECT 1 AS one" --trace
```

`--trace` prints the agent steps. `--full` prints the whole query response
instead of a three-row preview.

Or start the server, which listens on `127.0.0.1:8000`:

```powershell
uv run python server.py
```

| Route | Returns |
| --- | --- |
| `GET /` | A browser page with a request box |
| `GET /health` | The sample-mode flag, and whether Zetaris and Nightshift are configured |
| `POST /ask` | `{"request": "..."}` in, the agent result and trace out |

```powershell
curl.exe -X POST http://127.0.0.1:8000/ask -H "Content-Type: application/json" -d '{\"request\": \"SELECT 1 AS one\"}'
```

## Sample mode

Sample mode runs with an empty `.env`, no network, and Zetaris and Nightshift
stopped.

```powershell
$env:SAMPLE_MODE="1"
uv run python smoke.py
uv run python run.py "SELECT 1 AS one"
```

`SAMPLE_MODE` accepts `1`, `true`, `yes` or `on`. Today it returns fixed rows
and fixed answers, and the ledger marks those events `via=sample`.

## Configuration

`.env.example` lists every setting with placeholder values.

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
| `MAX_STEPS` | `6` | Step limit per run |
| `SERVER_HOST`, `SERVER_PORT` | `127.0.0.1`, `8000` | Server address |

### Models

Every model call goes to Nightshift. There is no second provider. If Nightshift
is down, times out, returns an error, or sends an empty answer, the call fails
with a clear error and the ledger records it.

`meterless/auto` works without a pinned model. To pin one, seat it as a lane in
Nightshift.

| Use | Model |
| --- | --- |
| Fast lane | `nvidia/nemotron-3.5-lightning-30b-a3b` |
| Deep lane | `nvidia/nemotron-3.5-super-vl-120b-a12b` |
| Spare | `nvidia/nemotron-3-super-120b-a12b` |
| Spare | `nvidia/nemotron-3-ultra-550b-a55b` |

Do not seat `nvidia/nemotron-3-nano-30b-a3b` or
`nvidia/llama-3.3-nemotron-super-49b-v1.5`. Both are deprecated.

## Logs and receipts

The app creates `logs/` on first write.

`logs/ledger.jsonl` has one line per model call, query, blocked request or
error. Each line records:

- `kind`: `model`, `query`, `blocked`, `error` or `model_receipt`
- `via`: `nightshift`, `zetaris` or `sample`
- `model`: the model that handled the request
- `request_id`: the Nightshift request ID
- `signed`: true when the Nightshift receipt carries a proof

Nightshift writes its receipt after the call returns. Once it settles, run:

```powershell
uv run python verify_receipts.py
```

It adds a `model_receipt` line for each signed request.

`logs/trace.jsonl` has one line per agent step: run ID, step, tool, arguments,
status, error and duration.

## Safety

- Only read-only SQL reaches Zetaris: `SELECT`, `WITH`, `SHOW`, `DESCRIBE` and
  `EXPLAIN`.
- The guard rejects multiple statements, unreadable quoting, Spark functions
  that run Java or raise errors, and script transforms.
- Questions go to the model, which has no write tool.
- Logs redact key patterns before writing.
- No model weights are downloaded and no local GPU is needed.

## Tests

The tests run offline and need no credentials.

```powershell
uv run python -m unittest discover -s tests -p "test_*.py" -v
```

## Limitations

- Nightshift is the only model provider. If it is down, live model calls fail.
- Sample mode returns fixed rows and answers.
