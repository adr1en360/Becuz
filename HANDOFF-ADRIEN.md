# Handoff for Adrien: UI completion and remaining submission tasks

Updated: 27 Oct 2026.
Track: Track 2 (The Agent That Can Explain Why)
Submission deadline: 27 Oct 2026, 23:45 UTC.

---

## 1. What was completed on the UI (tmb)

The entire owner-first layout specified in `HANDOFF-TMB.md` has been built and tested:

### A. Landing page (`/`)
- Hero with staggered word entrance animation and clean copy.
- Interactive example chips that lead straight to `/investigate`.
- Registered s01 receipt preview on the right featuring:
  - Synthetic shop stamp and s01 badge.
  - Headline profit drop: ₦241,717 vs ₦379,412 (−₦137,695, −36.3%).
  - Visual comparison bars with missing profit gap.
  - Concrete cause breakdown from the registered s01 run: supplier cost (−₦46,992), missing transfers (−₦28,360), and POS fee rise (ruled out).
- Proof points, Detect-to-Act pipeline, limits section, and sponsor attribution strip (Zetaris, Meterless Nightshift, NVIDIA Nemotron).

### B. Fixed Ask header (`/investigate`)
- Stays fixed/sticky at the top while the investigation content scrolls below.
- 3 example chips underneath the question box that populate on tap:
  - "Why is my profit down?"
  - "How is my shop doing?"
  - "Where did my money go?"
- Segmented period picker: 1 week active; 2 days, 2 weeks, and Custom disabled until the server supports flexible date ranges.
- Badges: "Synthetic data" and "Sample mode" (or live mode).
- Friendly banner for 400 bad request responses (e.g. off-topic questions).

### C. Live streaming view
- Auto-scrolls to the newest step as events arrive.
- Filters to show each event's `plain` sentence. Events without `plain` stay hidden.
- Zetaris restarts read naturally: "The data source was busy, so Becuz is trying again."
- "Show technical details" toggle (off by default) reveals agent names, cause codes, engines, and models.

### D. Numbered step cards
- **Header**: Strong change summary (`−36.3% · ₦379,412 → ₦241,717`) and a "Play investigation" button that replays the run's steps one by one.
- **Step 1**: The question, baseline comparison (4 previous weeks), and collapsed technical details (run ID, mode, scenario).
- **Step 2**: Where the money went (sales − cost of goods − wastage − running costs) with 4 visual bars and collapsed `daily_pnl` Zetaris source details.
- **Steps 3..n**: One card per supported cause (largest first), tags (`origin`, `nature`), "This was right" confirmation button, collapsed Checker notes/models, and **source chips** (`[1] Supplier invoices · INV-0281`, `[2] Till sales · 26 records`) revealing record IDs and SQL queries on tap.
- **Ruled out**: Struck-through hypotheses with plain reasons and tested values.
- **Money missing**: Cash gap kept strictly separate from profit, with sale IDs and the question for staff.
- **Convergence**: Plain explanation of explained % and breakdown by controllable vs temporary.

### E. Executive summary
- Placed at the end of the report:
  1. What happened (`summary.what_happened`).
  2. Why (cause cards with tags and confirmation).
  3. What to do (interactive action checklist).
  4. "If you act on this" (`summary.outcome` in soft accent panel).
  5. Export PDF (`window.print()` with a print stylesheet in `globals.css` that hides buttons and prints cleanly on white).
  6. Run facts footer (duration, Zetaris queries, model checks, and expandable details).

### F. Verification
- `npm run build` and `npm run lint` pass with 0 errors and 0 warnings.
- Scenarios `s01`, `s04`, and `s05` verified end-to-end.
- Confirmation (`POST /confirm`) tested and recalled on subsequent runs via H-MEM.
- All 170 Python unit tests pass (`uv run python -m unittest discover -s tests -p "test_*.py"`).

---

## 2. What is left for Adrien / the agent and data layer

Before the submission deadline (27 Oct 23:45 UTC):

### Task 1: Run a live Zetaris and Nightshift pass
- Set live credentials in `.env` (`ZETARIS_REST_URL`, `ZETARIS_ORG_ID`, `ZETARIS_API_KEY`, `METERLESS_BASE_URL`, `METERLESS_RUNTIME_TOKEN`).
- Run `python smoke.py` to get four PASS lines.
- Run `BECUZ_LIVE=1 uv run python -m unittest tests/test_zetaris_usl.py` to confirm USL parity with DuckDB.
- Run a live investigation on `s01` via `python run.py --input input_examples/example_1.json`.
- Ensure `output_examples/live_s01_output.json`, `output_examples/live_s01_queries.jsonl`, and `output_examples/live_s01_receipts.jsonl` are refreshed with fresh timestamps and signed Nemotron receipts.

### Task 2: Retake UI screenshots
- With the live or sample server running, take screenshots of the updated UI to replace the ones in `docs/screenshots/`:
  - `report-s01-desktop.png` (1280px wide)
  - `report-s01-phone.png` (360px wide)
  - `report-s04-desktop.png` (1280px wide)
  - `running-desktop.png` (1280px wide)

### Task 3: Record the demo video (1 to 4 minutes)
Follow `demo-video-guide.md`:
- Lead with the user and problem in the first 30 seconds (Nigerian mini-mart owner, profit down, joined records).
- Show the agent querying Zetaris (the `transfer_check` join).
- Show the feature each Meterless engine powers (Scout contract, H-MEM memory, World Model ledger, Markovian chain).
- Show Nightshift and Nemotron visible on screen.
- Show the web UI running live, the numbered steps, and the receipt.
- Do not show any API keys or tokens on screen.

### Task 4: Finalize the 12-slide pitch deck
Follow `deck-brief-for-tmb.md`:
- Slide 1: Becuz (Track 2, promise).
- Slide 2: Problem and users (till, bank, invoices, expenses).
- Slide 3: Solution (naira figures, receipts, missing cash separate).
- Slide 4: Four-agent architecture (Planner, Investigator, Checker, Writer, retry loops).
- Slide 5: What "explain why" looks like (the receipt, independent SQL check).
- Slide 6: Zetaris as the data layer (4 S3 sources, Lightning DBs, USL `daily_pnl` and `transfer_check`).
- Slide 7: Meterless engines and Nightshift (Scout Intent, World Model, H-MEM, Markovian, Nemotron).
- Slide 8: Unique sponsor use (Zetaris computes, model judges; read-only permissions).
- Slide 9: Scorecard on 5 synthetic test weeks (8/8 planted causes found, 6/6 red herrings ruled out).
- Slide 10: Owner in control and H-MEM memory.
- Slide 11: Tech stack, reliability, graceful failures.
- Slide 12: Roadmap and future enhancements.

### Task 5: HackOS submission checklist
- Confirm both Adrien and tmb are on the same team on HackOS.
- Ensure the GitHub repository `https://github.com/adr1en360/Becuz` is set to public.
- Declare pre-existing scaffold commit in the form (committed before 22 Oct 00:00 UTC).
- Ensure README top states Track 2: The Agent That Can Explain Why.
- Submit before 27 Oct 23:45 UTC.
