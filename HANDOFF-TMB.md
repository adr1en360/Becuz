# Handoff for tmb: the investigation as a story an owner can read

Read this once, build it, then **delete this file in the same commit as your changes**.

## The goal

A small or medium business owner asks a question about their shop and gets back an **investigation they can read
in one minute**: what happened, why, what was ruled out, and what to do, with the proof one click away. Not a
developer log, not a wall of text, and not a generic analytics chatbot. Every number on screen comes from the
report; the UI never invents one.

The layout follows a proven pattern for root-cause reports: **a header, numbered steps, then an executive summary**.
Each step leads with one plain sentence and keeps its technical detail collapsed.

## 1. The page, top to bottom

### A. The ask (stays fixed)

- The question box with **3 example chips** under it that fill it on tap: "Why is my profit down?", "How is my shop
  doing?", "Where did my money go?".
- **The period picker** (see section 3). The question, period, badges ("Synthetic data", "Sample mode") and the
  Investigate button stay fixed at the top while the investigation scrolls in its own pane below.
- An off-topic question gets the server's friendly 400 message, shown as is.

### B. While it runs

- The investigation pane **auto-scrolls to the newest step** as events arrive.
- Each step shows its event's `plain` sentence (new on master), e.g. "Checking: a supplier raised the unit cost of a
  product. The records show ₦46,992 lost." Events without `plain` stay hidden.
- "The data source was busy, so Becuz is trying again." appears when Zetaris restarts; it reads as normal, not as
  an error.
- Agent names, cause codes, engine and model chips sit behind **"Show technical details"**, off by default.

### C. The header (when the report arrives)

- Title "Profit investigation", the period ("12 to 18 Oct" from `frame.period_start` and `period_end`), and the
  change as one strong line: **"−36.3% · ₦379,412 → ₦241,717"** (`headline.change_pct`, `baseline_ngn`,
  `current_ngn`).
- A **"Play investigation"** button that replays the run's steps (the trace `events`) one by one, as in the live
  view. Good for demos and for owners who want to see how the answer was reached.

### D. Numbered steps

Each step is one card: a number, a title, **one plain sentence**, at most one small visual, then a collapsed
**"Technical details"**.

| Step | Title | Plain sentence and visual | Technical details (collapsed) |
|---|---|---|---|
| 1 | The question | The question, the period, and what it is compared with ("the 4 periods before") | The run ID, mode |
| 2 | Where the money went | Profit = sales − cost of goods − wastage − running costs, as 4 bars with each part's effect (`tree[].profit_effect_ngn`), negative shares labelled "offset by" | The `daily_pnl` source in Zetaris |
| 3..n | One per supported cause, largest first | The cause title, its impact ("−₦46,992"), its share, and **two tags** from the report: `origin` (Inside the shop / Outside the shop) and `nature` (You can act on it / Likely to pass). Then **source chips** (section 2) and "This was right" | The Checker's line, the model and rating, the SQL ("Show the query") |
| Ruled out | What we checked and ruled out | One line per `ruled_out` entry with its reason, struck through | The value tested |
| Money missing | Cash, kept apart from profit | `summary.cash`, the amount, the sale IDs, the owner question | The transfer-check source |
| Convergence | How much is explained | One plain line from `convergence.explained_pct` (95% or more: "These causes explain all of the change"), then the split by tag: what you can act on vs what is likely to pass, summed from the causes' `impact_ngn` | The figures behind it |

### E. Executive summary (the end of the page)

In this order, matching the reference screenshot:

1. **What happened**: `summary.what_happened`.
2. **Why**: one card per cause: the title, impact, tags, and a status: "You can act on it" or "Likely to pass", with
   "This was right" on each.
3. **What to do**: `summary.what_to_do`, one checkbox line per action.
4. **"If you act on this"** (the screenshot's "Expected outcome" box): `summary.outcome`, in a soft accent panel with
   a mono label, exactly as the screenshot shows. Only that text: no numbers of your own.
5. **Export PDF** button: `window.print()` with a print stylesheet that hides buttons, chips, the composer and the
   technical toggles, and prints the receipt on white.
6. **Run facts footer**, one line with Solar icons, like the screenshot's "⏱ 4m 12s · 🗄 23 queries · 🔍 4 web
   searches":
   - clock: `stats.duration_s` as "7m 49s"
   - database: `stats.zetaris_queries` "Zetaris queries"
   - checks: `stats.model_calls` "model checks"
   Keep "How this was run" (mode, models) behind a link for the detail.

## 2. Source chips (citations instead of raw SQL)

Each finding cites its sources the way assistants cite web pages: small numbered chips with plain names, for example
**[1] Supplier invoices · INV-0281** or **[2] Till sales · 26 records**. Tapping a chip shows the record IDs; the SQL
stays behind "Show the query". Plain names for the table names already in each evidence row (`evidence[].table`):

| Table | Chip name |
|---|---|
| `supplier_invoices` | Supplier invoices |
| `sales`, `sale_lines` | Till sales |
| `stock_movements` | Stock records |
| `bank_statement` | Bank statement |
| `transfer_check` | Till transfers vs bank |
| `promos` | Promotions |
| `expenses` | Expense book |
| `products` | Product list |

## 3. The period picker

A slider or segmented control: **2 days · 1 week · 2 weeks**, plus custom dates. Each choice sends `week_start`
today, and a `days` field once the server supports any length (pending, see below). The header and step 1 always
say the period in words.

**Pending on the server (Adrien and the agent):** the server still assumes a 7-day period compared with the 4
before it. Any length up to about 11 days fits the test data (8 weeks of history); a month or more needs longer test
data. Until that lands, the picker shows 1 week only, with the other options disabled.

## 4. What did not change

The routes (`POST /runs`, `GET /runs/<id>`, `POST /confirm`), the request body, and the report fields above.

## 5. Check before you commit

1. `git pull origin master`, then `cd web` and `npm run types`.
2. s01, s04 and s05 in sample mode read top to bottom in about a minute, with nothing technical open by default.
3. One live run with Adrien; then retake the screenshots in `docs/screenshots/` (live for the header and the model
   name).
4. Delete this file and commit.
