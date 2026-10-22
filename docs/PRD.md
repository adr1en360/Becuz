# Becuz — Product Requirements

**Track:** Open Agent Hackathon 2026, Track 2: *The Agent That Can Explain Why*
**Team:** Adrien (agent and data), tmb (UI)
**Status:** draft. Items marked **to agree** are open.

---

## 1. Problem and user

**User:** the owner of a Nigerian mini-mart or provisions shop with one or two staff. Customers pay in cash, by bank transfer, or by POS card terminal. There is no analyst.

**Question:** *"Why is my profit down this week?"*

**Why it is hard today:** the answer is spread across separate records. These are the POS till, the bank statement, supplier invoices and expenses. The common causes are local and concrete:

- a supplier raises a price with the exchange rate
- a discount keeps running after it should have ended
- perishables expire
- a transfer recorded at the till never reaches the bank

Finding them means joining records by hand.

**Track 2 fit:** Becuz investigates a complex question across several data sources and connects the findings. Its answer is backed by evidence, and it shows its reasoning, including what it ruled out.

---

## 2. What the owner gets

One investigation per question:

- **Headline:** profit this period compared with the baseline, in naira.
- **Ranked causes**, each with:
  - its naira impact
  - a tag: internal or external, and actionable or temporary
  - a **receipt**: the SQL that was run, the record IDs it found, and the critic's independent re-check
- **Ruled out:** hypotheses that were tested and rejected, with the reason.
- **Convergence:** how much of the drop is explained, and the remainder that isn't.
- **What to do this week:** concrete checks and actions.
- **Owner questions:** points only the owner can confirm, for example "Did this staff member take these transfers as cash?"
- **Caveat:** findings show correlation, not proven causation. The data is synthetic.

Becuz is **not** a dashboard, a chat window over SQL, or a forecaster. It never writes to the owner's systems.

---

## 3. Scope

### In scope

| ID | Cause | Sources | Tag |
|---|---|---|---|
| C1 | `supplier_cost_rise`: a supplier raised the unit cost of a top item | books + pos + context (exchange rate) | external, actionable |
| C2 | `promo_overrun`: a discount kept running after its end date | pos | internal, actionable |
| C3 | `wastage_spike`: perishables expired or were damaged | pos | internal, actionable |
| C5 | `transfer_leakage`: transfer sales by one staff member with no matching bank credit | **pos + bank (cross-source)** | internal, actionable |
| C9 | `pos_charge_rise`: planted as a **red herring** (charges stay flat), so the critic must rule it out | bank | external, actionable |

- **3 scenarios.** `s01` is the demo (C1 + C2 + C3 + C5, with C9 as the red herring). `s02` and `s03` use different cause mixes.
- Everything runs through Zetaris live, and through sample mode offline (§8).

### Out of scope (future work)

- Mix shift, stockouts, diesel cost, public holiday closures
- Live REST context feeds
- A second database engine for the POS
- Automatic weekly monitoring
- PDF invoices
- Scenarios beyond three
- Any write-back to the owner's systems

---

## 4. Data contract

All data is **synthetic**: a seeded generator builds 8 weeks of shop history, and causes are planted in the final week. It is labelled as synthetic everywhere. It is input data for the agent, never a substitute for its output.

Four logical sources, stored as CSV in S3 and registered in Zetaris:

| Source | Tables |
|---|---|
| `pos_files` | `products`, `staff`, `sales`, `sale_lines`, `promos`, `stock_movements` |
| `bank_files` | `bank_statement` |
| `books_files` | `supplier_invoices`, `expenses` |
| `context_files` | `fx_rates` |

- Money is naira with 2 decimals. Every template rounds it.
- Column names are final only after the generator writes them and `DESCRIBE <source>.<table>` confirms them on Zetaris.
- Each scenario ships an `answer_key.json`, used only by the eval. The agent never reads it.

### Metric tree

These definitions live in code as data and are tested:

```text
profit    = net_sales − cogs − wastage − opex − leakage
net_sales = Σ(qty × unit_price) − discounts
cogs      = Σ(qty sold × weighted unit cost from supplier_invoices)
wastage   = Σ(expired or damaged qty × unit cost)
opex      = Σ expenses by category
leakage   = transfer sales with no bank credit matching on reference,
            or on exact amount within 48h
```

The baseline is the average of the previous 4 weeks, unless the question names another period.

---

## 5. Agent design

**Pattern:** a hypothesis-driven investigator over a decomposition tree, with a verifier gate. It is built as a LangGraph state graph in `becuz/`.

```text
intake       Scout Intent: route and safety check
frame        LLM: question → {metric, period, baseline}
recall       memory: owner-confirmed causes for these entities
decompose    SQL: change per node of the profit tree; drill into nodes above the threshold
hypothesize  LLM: candidate causes from the catalogue for the nodes that moved
investigate  SQL: each candidate's evidence templates → EvidenceObject
verify       critic: re-runs the cited SQL independently, checks record IDs, size and contradictions
               reject → investigate again with a revised query (max 2 retries) or mark ruled out
converge     SQL: share of the drop explained, plus the unexplained remainder
report       LLM: Investigation JSON plus an owner-language summary
```

**Core rule:** deterministic SQL does every calculation and every match. The model frames the question, proposes hypotheses, judges the evidence and writes the narrative. **The model never computes a naira figure.**

- The internal/external and actionable/temporary tags are fixed data in the cause catalogue.
- Owner confirmation happens outside the run, so it never blocks one. The run lists `owner_questions`. `python run.py --confirm <run_id> <cause_id>` records the owner's answer, and later runs recall it.
- Model output is JSON checked against a schema. Invalid JSON is retried once, then the step fails with a structured error.

---

## 6. Sponsor technology

The test for each sponsor: if we removed it, would the agent still work? It must not.

| Sponsor | Role in Becuz |
|---|---|
| **Zetaris** | The data layer and the only path to the data. It runs every metric, evidence and critic query across the four sources, including the transfers-vs-bank join. |
| **Meterless Nightshift** | The app's only model provider (`127.0.0.1:8088/v1`). Every model call goes through it and gets a signed receipt in the ledger. The NVIDIA key lives in Nightshift's Providers tab, not in this project. |
| **Meterless engines** | All four, each powering a working feature with a passing conformance test. Placement is in the table below and in `docs/diagrams/architecture.html`. |
| **NVIDIA Nemotron** | Lighter steps run on the fast lane (Nemotron 3.5 Lightning). The critic runs on the deep lane (Nemotron 3.5 Super). Every model event logs the model that actually handled the request, so the trace shows where Nemotron did the work. We are competing for the NVIDIA Nemotron award. The routing mode is **to confirm** (§11). |

### Meterless engine placement (agreed)

Each engine is built in `becuz/engines/` from the Meterless open specs. Each one has its own conformance test in `tests/`.

| Engine | Where it works | What it does in Becuz |
|---|---|---|
| **Scout Intent** | intake, investigate, verify | Turns the owner's question into a **signed investigation contract** (metric, period, allowed sources and tables, query budget). Every query and every critic check is tested against that contract. The current `base/scout.py` is only a local router and does not count as this engine. |
| **H-MEM** | recall, hypothesize, owner confirmation | Stores **owner-confirmed causes** and **the checks that found them**. They are recalled before each investigation, so a later run tests them first. It writes only facts the owner has confirmed. |
| **World Model** | recall, investigate, report | Gives products, suppliers, staff and payment channels one canonical ID each, linked to their source rows. Every cause points to these entities. Confirmed facts are copied into H-MEM. |
| **Markovian** | verify | The critic carries a compact summary of accepted and rejected evidence forward, instead of the full history, and logs the tokens saved. |

Night mode (overnight multi-attempt runs) is future work. Meterless has not published its job API yet.

---

## 7. Interfaces

- **CLI:** `python run.py --input input_examples/example_N.json` prints the Investigation JSON.
- **HTTP:** `POST /run` on `server.py` takes the same input and returns the same JSON. CORS is enabled for the UI.
- **Owner confirmation:** `python run.py --confirm <run_id> <cause_id>`.
- **Trace:** one file per run, `logs/trace-<run_id>.jsonl`, plus readable stdout. Each line carries `timestamp, run_id, agent_name, action, input_summary, output_summary, target_agent, confidence, retry_count, status`. Model and query events also carry `via` and `signed`, and model events carry the `model` that handled the request.
- **Investigation JSON fields:**
  - `run_id`, `question`, `frame`, `headline`, `tree`
  - `causes[]`, each with `evidence[]` and `verified`
  - `ruled_out[]`, `convergence`, `summary`, `owner_questions[]`
  - `limitations[]`, `stats`, `trace_file`
  
  Exact field types are set in `becuz/schemas.py` and tested.

---

## 8. Guardrails

All of these are enforced in code, not in prompts:

- Read-only SQL guard (`base/tools.py:is_read_only`) on every statement, plus an allowlist of sources and tables.
- Templates aggregate in SQL, because Zetaris returns at most 100 rows per call.
- A step budget (40) and a retry cap (2) for the graph.
- No claim without record IDs; the critic rejects it.
- Key redaction in every log.
- Templates use only SQL that both Zetaris (Spark 3.5.3) and the local engine run identically. No `QUALIFY`, no `dayofweek`, no `ORDER BY` without a unique tiebreaker.

### Sample mode (`SAMPLE_MODE=true`)

- Runs the whole agent with an **empty `.env`, no network, and Zetaris and Nightshift stopped**.
- Queries use the same Spark SQL templates, translated by sqlglot, on in-memory DuckDB over the scenario CSVs.
- Model steps switch to **rule-based logic computed from that run's data**. Every candidate in the catalogue is tested for the nodes that moved, and the summary is filled from the computed numbers. They are labelled `via=sample-rules` in the trace and the output.
- It **never** replays a saved output. Different inputs give different results.

---

## 9. Success criteria

The eval runs over the 3 scenarios (`python -m becuz.eval`).

| Metric | Target |
|---|---|
| Cause recall (planted causes found) | ≥ 0.8 |
| False cause rate (reported causes not planted) | ≤ 0.1 |
| Red herring rejected | 3 of 3 |
| Determinism: same cause set and ranks over 5 runs | 5 of 5 |
| Impact error against the answer key | within ±10% |
| Run time | under 2 minutes |

Results are reported as measured, including any misses.

---

## 10. UI brief (tmb)

- A Next.js app in `web/`. It reads only the Investigation JSON from `POST /run`, or a **real saved output** from `output_examples/`. No mock data.
- **UI library:** [OpenUI by Thesys](https://github.com/thesysdev/openui), a generative UI library. Its components render the Investigation JSON, so tmb doesn't need to hand-build each component.
- **Screens:**
  - the question
  - the decomposition tree
  - cause cards with receipts (SQL, record IDs, critic check, `via`/`signed`)
  - the ruled-out list
  - convergence (explained vs unexplained)
  - the "what to do" summary
  - the "how I got here" trace
- **Design rules:**
  - fully rounded buttons
  - no box shadows
  - Solar icons: Bold for active, Outline for inactive
  - no Ciscela font
  - works at phone width

---

## 11. Open questions

1. **Nightshift routing:** do the `meterless/fast` and `meterless/deep` modes map to the Lightning and Super lanes? To confirm with a live probe.
2. **Pass marks** in §9: to confirm.
