# Becuz — Build Plan

This plan builds `docs/PRD.md` in small slices. Each slice has a fixed scope and a "done when" check. When a slice hits a contradiction, the builder stops and reports it rather than building past it.

**Deadline:** submissions close 27 Oct 2026, 23:45 UTC. Internal target: submit on 26 Oct.
**Owners:** Adrien (agent and data), tmb (UI).

---

## Working rules

**Always**
- Run a read-only audit before writing code. Report the findings, then build.
- Before writing code against a table, show its DDL (`DESCRIBE <source>.<table>`). Before editing any file over 50 lines, show its first 10 lines.
- Install packages with `uv add` and run code with `uv run`.
- Send every model call through `Pipeline.ask_messages`, and pass every SQL statement through `is_read_only`.
- Give every non-trivial node, tool and template a test. Run the full suite before handing off.
- Back browser claims with screenshots.

**Ask first**
- Any Zetaris write (`CREATE`, `REGISTER`, `CACHE`). Show a dry run first.
- A new dependency.
- Any change to `base/`.
- Anything outside the PRD scope, or anything that changes what judges see.

**Never**
- Mock data, canned answers or saved outputs presented as a run. The only generated data is the shop's input records.
- Model arithmetic on money.
- `QUALIFY`, `dayofweek`, or `ORDER BY` without a unique tiebreaker in templates.
- Hand-written or edited traces.
- Secrets in code, logs, chat or commits.

**Code shape**
- `base/` stays domain-free and standard library only. Product code lives in `becuz/`.
- Small files with one job each. State and schemas are typed. Each sponsor service sits behind its own adapter.
- Write the least code that works. No speculative options or layers.

---

## Slices

| # | Slice | Owner | Scope | Done when |
|---|---|---|---|---|
| 0a | Choose the build skills: the best agent-building skills, and LangGraph's official skill or docs | Adrien | research only | A short list of the skills used at each stage |
| 0b | Meterless engine placement: work through the engines, then agree where each one goes | Adrien | `docs/PRD.md` §6, §11 | The PRD engine table has no "to agree" left |
| 0c | Dependencies and model routing: add `duckdb==1.5.6` and `sqlglot==30.21.0`, and probe `meterless/fast` against `meterless/deep` | Adrien | `pyproject.toml`, `uv.lock` | Tests pass; the ledger shows which model each mode reached |
| 1 | Generator: seeded `data/generator.py` → s01 CSVs plus `answer_key.json` | Adrien | `data/`, `tests/` | The same seed gives byte-identical files; answer-key impacts match the metric SQL to ±₦1 |
| 2 | Zetaris sources: upload s01 to S3 and register the four sources | Adrien | `scripts/` (placeholders only in committed SQL) | `DESCRIBE` succeeds on every table; the transfers-vs-bank join returns the planted rows |
| 3 | SQL layer: `becuz/sql.py` runs the guard, then Zetaris, or DuckDB via sqlglot in sample mode; `becuz/metrics.py` holds the metric tree templates | Adrien | `becuz/`, `tests/` | One parity test per template; the transpiled SQL text is pinned in a test |
| 4 | Cause catalogue: `becuz/catalogue.py` with evidence templates and tags for C1, C2, C3, C5, C9 | Adrien | `becuz/`, `tests/` | Each planted cause is found on s01; C9 comes back flat |
| 5 | Graph golden path: `becuz/schemas.py`, the state, the nodes and the graph; per-run trace; sample-rules for model steps | Adrien | `becuz/`, `tests/` | s01 runs live and with an empty `.env`; the trace shows a critic rejection and a retry |
| 6 | Entry points and engines: `run.py --input`, `POST /run` with CORS, `--confirm`, and the agreed Meterless engines wired in | Adrien | `run.py`, `server.py`, `becuz/` | 3 `input_examples` with real saved outputs; a confirmed cause is recalled on a re-run |
| 7 | Eval: s02, s03 and `python -m becuz.eval` | Adrien | `data/`, `becuz/eval.py` | The metrics table is produced and reported as measured |
| 8 | UI: Next.js in `web/`, built on real saved outputs and then on live `POST /run` | tmb | `web/` | A screenshot of each screen; it works against the live server |
| 9 | Submission pack: README, `metadata.json`, Dockerfile, `.env.example`, clean-clone test, deck, demo video | Adrien + tmb | repo root, `docs/` | The full validation flow passes from a fresh clone with an empty `.env` |

### Dependencies between slices

```text
0a, 0b, 0c ──► 1 ──► 2 ──► 3 ──► 4 ──► 5 ──► 6 ──► 7 ──► 9
                                       └────► 8 (needs a real s01 output) ──► 9
```

---

## Days

| Day | Adrien | tmb |
|---|---|---|
| 22 Oct | 0a, 0b, 0c, 1 | Next.js app shell, layout and design tokens |
| 23 Oct | 2, 3, 4 | Screen components |
| 24 Oct | 5 | UI on s01's first real output |
| 25 Oct | 6, 7 | UI on live `POST /run` |
| 26 Oct | 9, **submit** | 9, **submit** |
| 27 Oct | buffer | buffer |

---

## Existing code to reuse

| Need | Use |
|---|---|
| Model calls (Nightshift first, NVIDIA fallback, ledger) | `Pipeline.ask_messages` in `base/pipeline.py` |
| Zetaris queries | `Pipeline.query` in `base/pipeline.py` |
| Read-only SQL check | `is_read_only` in `base/tools.py` |
| Event ledger | `ledger.write` in `base/ledger.py` |
| Memory interface | the `Memory` protocol in `base/memory.py` |
| Intake routing and safety | Scout in `base/scout.py` |
| HTTP server | the `Handler` in `server.py` (add `/run`) |

`base/sample.py` returns fixed rows and answers. Becuz does not use it. Sample mode goes through `becuz/sql.py` and the sample-rules instead, so `base/` stays unchanged.
