# Open Agent base

Small Python base, Python 3.12. `base/` is standard library only; the Becuz
agent in `becuz/` uses LangGraph.

Nightshift is the primary AI provider. A direct NVIDIA call is the fallback. The fallback runs only when Nightshift fails.

## Agent connection

Cursor, OpenCode, and Codex read `AGENTS.md`. Claude Code reads `CLAUDE.md`,
which imports `AGENTS.md`. Zetaris connection details, the preflight, and the
starter prompt are in `ZETARIS-CONNECTION.md`. Live values belong in `.env`.

## Provider order

1. Nightshift: `http://127.0.0.1:8088/v1`, model `meterless/auto`.
2. Direct NVIDIA: `https://integrate.api.nvidia.com/v1`.
3. Every model call attempts to write `via` to `evidence/ledger.jsonl`:
   `nightshift`, `nvidia-direct`, or `sample`. Queries write `via=zetaris` or
   `sample`. Ledger writes are best effort.

## Live Nemotron models

| Use | Model |
| --- | --- |
| Nightshift lane 1 | `nvidia/nemotron-3.5-lightning-30b-a3b` |
| Nightshift lane 2 | `nvidia/nemotron-3.5-super-vl-120b-a12b` |
| Direct fallback default | `nvidia/nemotron-3.5-lightning-30b-a3b` |
| Spare | `nvidia/nemotron-3-super-120b-a12b` |
| Spare | `nvidia/nemotron-3-ultra-550b-a55b` |

Do not seat `nvidia/nemotron-3-nano-30b-a3b` or `nvidia/llama-3.3-nemotron-super-49b-v1.5`. Both are on the deprecation list.

## Setup

1. Copy `.env.example` to `.env`.
2. Fill `ZETARIS_REST_URL`, `ZETARIS_ORG_ID`, and `ZETARIS_API_KEY`. The REST host is `api.<cluster-id>.cloud.zetaris.com/api/v1.0`, not the `new-ui` browser host.
3. Install Nightshift. Add the NVIDIA key under Providers. This is the primary route.
4. Optional: seat one Nemotron lane in Nightshift. `meterless/auto` works without a pinned lane.
5. Add `NVIDIA_API_KEY` to `.env` only for the fallback. It is a separate copy.
6. Keep `.env` out of git.

The Nightshift token is read from `%LOCALAPPDATA%\ai.meterless.runtime\proxy-token`.

## Run

```powershell
cd Becuz
python smoke.py
python run.py "SELECT 1 AS one"
python run.py "Summarize the latest sales trend in one sentence."
python run.py "SELECT 1 AS one" --trace
python server.py
```

With `uv`, install the empty environment once and prefix the commands:

```powershell
uv sync
uv run python smoke.py
uv run python server.py
```

`smoke.py` prints four lines: `config`, `zetaris`, `model`, `agent`.

See `SCAFFOLD.md` for the plug points. In short: put product code in
`becuz/` and leave the base
alone.

Sample mode runs the whole scaffold without credentials:

```powershell
$env:SAMPLE_MODE="1"
python smoke.py
python run.py "SELECT 1 AS one"
```

The scaffold tests run offline:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
# or: uv run python -m unittest discover -s tests -p "test_*.py" -v
```

## How the fallback works

`Pipeline.ask` tries Nightshift first. It falls back to direct NVIDIA on:

- runtime down or connection refused
- timeout
- HTTP error
- retired model response
- an empty or malformed answer

The fallback does not run on a normal answer. It runs only on a failed provider
or an empty primary answer.

The direct call needs `NVIDIA_API_KEY` in `.env`. A key stored inside Nightshift is not visible to the app.

## Evidence

`evidence/ledger.jsonl` records:

- `via`: `nightshift`, `nvidia-direct`, or `sample`
- `model`
- `request_id`
- `signed`: true when the matching Nightshift receipt has `_proof`
- `tool`: `ask_model`, `query_data`, or `blocked`

The ledger does not store API keys. Known key patterns (`nvapi-...`,
`Bearer ...`) are redacted before writing; do not put secrets in prompts or SQL.
Ledger writes are best effort: a write failure is reported on stderr and does not
fail the answer.

Nightshift writes its receipt after the model call returns. The `signed` field on a
model event is a snapshot at call time. After the runtime settles, run:

```powershell
python verify_receipts.py
```

It appends one `kind=model_receipt` event with `signed=true` for each Nightshift
request whose matching receipt has `_proof`.

`evidence/trace.jsonl` records one line per agent step: run id, step, tool,
arguments, status, error, and duration.

## Safety

- Only read-only SQL reaches Zetaris: `SELECT`, `WITH`, `SHOW`, `DESCRIBE`, `EXPLAIN`.
  `EXPLAIN ANALYZE SELECT` may execute the SELECT while planning; it is still
  restricted to `SELECT`/`WITH`.
- Direct write or destructive requests are blocked before any model call.
  Questions that ask how to update or delete go to the model, which has no write
  tool.
- Quoted strings and comments are blanked in one pass; neither is scanned for SQL
  keywords.
- Multiple statements are rejected.
- The app never downloads local model weights.

## Judge reproduction

Judges do not need Nightshift installed.

Fast offline check:

```powershell
$env:SAMPLE_MODE="1"
python smoke.py
python run.py "SELECT 1 AS one"
python server.py
```

No credentials are needed in sample mode. Unset `SAMPLE_MODE` for real runs.

Real provider check:

1. Create `.env` with the Zetaris values and `NVIDIA_API_KEY`.
2. Run `python smoke.py`.
3. Run one SQL request and one model request from `run.py`.
4. Read `evidence/ledger.jsonl` and check the `via` field.

With Nightshift running, `via` is `nightshift`. Without it, `via` is `nvidia-direct`.
