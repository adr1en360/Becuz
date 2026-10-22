# Zetaris connection guide — Becuz

How Claude Code, OpenCode, and Codex connect to the Zetaris AWS
instance from this agent repository.

This file contains **no credentials**. The live values are in `.env`, which is
gitignored. Never paste those values into a prompt, log, source file, URL, or
commit.

## Quick start

1. Open `Becuz/` as the workspace in Claude Code or OpenCode/Codex.
2. The agent reads `AGENTS.md` (Claude Code reads `CLAUDE.md`, which imports
   `AGENTS.md`).
3. The agent reads this file and uses the values in `.env`.
4. Run the preflight before the first Zetaris query.

The working values are already in `.env`:

| Variable | Meaning |
|---|---|
| `ZETARIS_REST_URL` | Direct REST API base. It must end in `/api/v1.0` and use the `api.<cluster-id>.cloud.zetaris.com` host. |
| `ZETARIS_ORG_ID` | Numeric organisation ID from **Management → Organisation**. |
| `ZETARIS_API_KEY` | API key from **Management → API Tokens**. Shown once. |

The upstream Zetaris repository calls this file `.env.local`. This repository
uses `.env`; the variable names are the same. `.env.example` is the template.

## Protocol choice

Use **REST** for agent work. It needs no Java runtime and no JDBC driver, and
the existing Python client in `base/zetaris.py` already uses it.

Use JDBC only if you specifically need the Zetaris Java driver. This agent does
not require it.

## REST connection

### Preflight endpoint

```http
GET {ZETARIS_REST_URL}/datasource/datasources
```

### Run SQL

```http
POST {ZETARIS_REST_URL}/sql-editor/sqls/run
```

Headers:

```http
Authorization: Bearer <ZETARIS_API_KEY>
X-Org-ID: <ZETARIS_ORG_ID>
X-Request-ID: <fresh uuid4>
Content-Type: application/json
```

Body:

```json
{
  "queryId": "<fresh uuid4>",
  "sql": "SELECT 1 AS one",
  "source": "SqlEditor",
  "limit": 100
}
```

`queryId` and `X-Request-ID` must be valid UUIDs. The API key belongs in the
`Authorization` header, never in a URL.

### Check it from this folder

```powershell
python run.py "SELECT 1 AS one"
```

Expected: `ok: true`, `row_count: 1`.

A real sample query:

```powershell
python run.py "SELECT * FROM NY_TAXI.taxi_zones LIMIT 5"
```

Expected: `row_count: 5`.

### Full preflight

```powershell
python smoke.py
```

Expected: four `PASS` lines:

```text
config   PASS
zetaris  PASS
model    PASS
agent    PASS
```

`smoke.py` checks Zetaris, the model provider, and the agent. Use `run.py` for
a Zetaris-only check.

### Useful read-only commands

```sql
SELECT 1 AS one
SHOW LIGHTNING DATABASES
SHOW DATASOURCES
SHOW NAMESPACES OR TABLES IN lightning.metastore
```

`SHOW DATASOURCES` does not list Lightning-registered sources. Check
`SHOW LIGHTNING DATABASES` too. An empty list is normal on a clean instance.

REST returns values as strings, and decimals may use exponent notation.
Convert them before comparing.

### Common errors

| Symptom | Check |
|---|---|
| `401` | The API key is wrong or expired. Create a fresh key in **Management → API Tokens** and update `.env`. |
| `400 Not Allowed` | `ZETARIS_ORG_ID` is not the numeric organisation ID. |
| `400` on a valid query | `X-Request-ID` and `queryId` must be UUIDs. |
| `Table not found` | Use the qualified name `<source>.<table>`. |
| `Operation not permitted` for a local URL | The command environment may be blocking local network access. For the AWS URL, retry with network permission; do not change the endpoint or key. |

## JDBC connection (optional)

Use JDBC only when you need the Zetaris Java driver. Requirements:

- Java 11 or later
- The Zetaris JDBC driver `.jar` that matches the instance
- Zetaris username and password
- `jaydebeapi` only if you use the Python SQL runner

Environment variables:

| Variable | Meaning |
|---|---|
| `ZETARIS_JDBC_URL` | `jdbc:zetaris:lightning@<host>:10000`, or the URL supplied for the AWS instance |
| `ZETARIS_JDBC_JAR` | Full path to the matching driver JAR |
| `ZETARIS_USERNAME` | Zetaris user ID |
| `ZETARIS_PASSWORD` | Zetaris password |
| `ZETARIS_USER_AGENT` | `app_name user@domain.tld` for create scripts that call external APIs |

Driver class: `com.zetaris.lightning.jdbc.LightningDriver`

The Python runner does not search for the JAR. Ask the user for the full path
or set `ZETARIS_JDBC_JAR`.

This agent does not use JDBC. REST is already verified.

## UI proxy (separate route)

The small `query_zetaris.py` / `check_zetaris.py` helpers in the upstream
getting-started repo use the **UI proxy**, not the direct REST API.

- `ZETARIS_BASE_URL` = web UI origin, e.g. `https://<instance>`; no path.
- Calls go to `/api/proxy/...`.
- `ZETARIS_QUERY_LIMIT` defaults to 1000.
- `ZETARIS_ENGINE_ID` is optional.

Do not confuse `ZETARIS_BASE_URL` (UI origin) with `ZETARIS_REST_URL` (direct
API base ending in `/api/v1.0`). This repository uses direct REST.

## Agent rules

- Read this file and `AGENTS.md` before the first Zetaris action.
- Start with read-only SQL: `SELECT`, `SHOW`, `DESCRIBE`.
- Send **one statement per call**. Do not add a trailing semicolon.
- Keep a multi-table `COMPILE USL` together as one statement; do not split it
  at semicolons.
- Use qualified names: `<source>.<table>`.
- Zetaris Lightning SQL only. Do not substitute Hive/Spark SQL and do not start
  a local Spark session.
- Creating, dropping, granting, or writing changes the instance. Run a dry-run
  first and wait for the user's clear go-ahead.
- Do not call port 8889.
- Never ask an agent to create or fetch an API key.
- Never print, log, or commit `.env`, `ZETARIS_API_KEY`,
  `ZETARIS_PASSWORD`, or the Nightshift runtime token.

## Starter prompt

Copy this into Claude Code or OpenCode/Codex:

```text
Read AGENTS.md and ZETARIS-CONNECTION.md and follow them.

Before doing anything else, open a terminal in Becuz/ and run the Zetaris
preflight:
  python smoke.py

Report the four PASS/FAIL lines. Do not print, echo, or paste any value from
.env. Then connect over REST to the instance configured in .env and confirm
with:
  SELECT 1 AS one
  SHOW LIGHTNING DATABASES

Goal: <describe the read-only Zetaris task here>

Start read-only. Do not create, drop, grant, or write anything without my
explicit go-ahead.
```

## Claude Code

1. Open `Becuz/` in Claude Code.
2. Claude Code reads `CLAUDE.md`, which imports `AGENTS.md`.
3. Paste the starter prompt.

## OpenCode / Codex / other agents

1. Open this folder as the workspace.
2. The agent reads `AGENTS.md`.
3. Paste the starter prompt.

## Official references

- Getting-started repository: <https://github.com/zetaris/getting-started>
- Connection index: <https://github.com/zetaris/getting-started/blob/main/docs/connections/README.md>
- Client setup (REST and JDBC): <https://github.com/zetaris/getting-started/blob/main/docs/connections/client-setup.md>
- Codex: <https://github.com/zetaris/getting-started/blob/main/docs/connections/codex-connection.md>
- Claude Code: <https://github.com/zetaris/getting-started/blob/main/docs/connections/claude-code-connection.md>
- Preflight script: <https://github.com/zetaris/getting-started/blob/main/scripts/preflight.py>

## Current verified state

Last checked: 2026-10-22.

- Zetaris AWS cluster reachable.
- `SELECT 1 AS one` returns 1 row.
- `SELECT * FROM NY_TAXI.taxi_zones LIMIT 5` returns 5 rows.
- `smoke.py` passes 4/4.
- Unit tests pass offline.
- Nightshift is running on `127.0.0.1:8088`.

Local Docker and `zetaris-platform.zip` are not needed for the AWS path.
