# Agent instructions — Becuz

This folder is the agent repository. OpenCode, Codex, and other agents that
read `AGENTS.md` start here. Claude Code reads `CLAUDE.md`, which imports
this file.

## Read first

- `README.md` — setup, provider order, and run commands.
- `SCAFFOLD.md` — what is fixed and what is still empty.
- `ZETARIS-CONNECTION.md` — Zetaris REST/JDBC connection, preflight, starter
  prompt, and safety rules.

## Workspace rules

- Keep `Becuz/` self-contained. Do not depend on files outside this folder.
- `.env` holds the live values and is gitignored. `.env.example` is the
  template. Never print, log, or commit secrets.
- Product logic goes in `becuz/`. Keep `base/` domain-free.
- `base/` is standard library only. `becuz/` may use LangGraph.
- A policy is stateless across runs. Keep per-run state in `RunState`.
- Every model call goes through `Pipeline.ask_messages`.
- Every Zetaris SQL call goes through `base.tools.is_read_only` first.
- New tools and policies need unit tests.

## Zetaris connection

Use **REST**; it is already working. JDBC is optional and is not needed here.

Live values are in `.env`:

- `ZETARIS_REST_URL` — direct API base ending in `/api/v1.0`
- `ZETARIS_ORG_ID` — numeric organisation ID
- `ZETARIS_API_KEY` — API key from the Zetaris GUI

Never print, echo, log, paste, or commit those values. Never ask an agent to
create or fetch the API key.

Before the first Zetaris query, open a terminal in `Becuz/` and run the preflight:

```powershell
python smoke.py
```

Expected: four `PASS` lines (`config`, `zetaris`, `model`, `agent`).

For a Zetaris-only check:

```powershell
python run.py "SELECT 1 AS one"
```

Then confirm the instance with:

```sql
SHOW LIGHTNING DATABASES
```

## SQL rules

- Start read-only: `SELECT`, `SHOW`, `DESCRIBE`.
- Send one statement per call. Do not add a trailing semicolon.
- Keep a multi-table `COMPILE USL` together as one statement.
- Use qualified names: `<source>.<table>`.
- Zetaris Lightning SQL only. Do not use Spark/Hive SQL or start a local Spark
  session.
- Creating, dropping, granting, or writing changes the instance. Run a dry-run
  first and wait for the user's explicit go-ahead.
- Do not call port 8889.

## Starter prompt

```text
Read AGENTS.md and ZETARIS-CONNECTION.md and follow them.

Run the Zetaris preflight from this folder and report the PASS/FAIL lines. Do
not print or echo any value from .env. Then connect over REST and confirm with
SELECT 1 AS one and SHOW LIGHTNING DATABASES.

Goal: <read-only Zetaris task>

Start read-only. Do not create, drop, grant, or write anything without my
explicit go-ahead.
```

## Current state

- The idea is Becuz (Track 2). The base scaffold works; `becuz/` is being
  built on LangGraph.
- Zetaris AWS is the active path; local Docker and `zetaris-platform.zip` are
  not needed.
- Add tests for every `becuz/` node and tool before expanding the graph.
