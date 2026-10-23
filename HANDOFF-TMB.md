# Handoff for tmb

Read this once, do the steps, then **delete this file in the same commit as your changes**.

## What changed on master

1. **`base/` is gone.** Everything the agent uses now lives in `becuz/`. Nothing in `web/` imported
   it, so this does not affect you directly.
2. **The server has two routes only:** `POST /run` and `GET /health`. `POST /ask` and the old page
   at `/` are removed. Your `web/src/lib/api.ts` already uses only these two, so no change is needed.
3. **The Checker now asks a real model (Nemotron, through Nightshift) to rate each claim.** That
   changes three things in the report:
   - `causes[].confidence` can be **`null`** when the model was unavailable. Before, it was always
     a number.
   - `status` can be **`"partial"`**, and `errors` then lists what failed. Your `report.tsx` already
     handles this.
   - `evidence[].check` now carries `model` (the Nemotron model that answered, or `null`), `via`
     (`"nightshift"` live, `"sample-rules"` offline) and `signed`. `check.note` now holds the
     Checker's reason plus the model's one-line note.
4. **`stats`** now fills `model_calls` and `models` (model name to call count) on live runs.
   `stats.via` has one entry for the warehouse (`zetaris` or `local`) and one for the judge
   (`nightshift` or `sample-rules`).
5. **A live run takes about 8 minutes** (27 Zetaris queries and 6 model calls). A sample run takes
   about 1 second.

## What did not change

- The request body: `{"question": "...", "scenario": "s01"}`, with an optional `week_start`.
- Every other report field: `headline`, `tree`, `causes` (apart from `confidence`), `ruled_out`,
  `not_tested`, `convergence`, `summary`, `owner_questions`, `limitations`, `trace_file`.
- CORS, port 8000 and `NEXT_PUBLIC_API_URL`.
- The schema file stays at `docs/investigation.schema.json`.

## What to do

1. Merge master into your branch, then regenerate the types:

   ```powershell
   cd web
   npm run types
   ```

2. **Fix the confidence pill** in `web/src/components/cause-block.tsx`. Today it shows `0%` when
   `confidence` is `null`. Hide the pill, or show "Not rated", when it is `null`.
3. **Fix the double full stop** in `cause-block.tsx`. `check.note` already ends with a full stop, and
   the code adds `". "` after it, which renders as `this.. Checked by`. Add only a space.
4. **Show who judged the claim.** In `checkedBy(item.check)`, show `check.model` when it is set,
   for example "Checked by nvidia/nemotron-3-ultra-550b-a55b through Nightshift". In sample mode
   (`via` is `"sample-rules"`), say "Checked by fixed rules (sample mode)".
5. **Tell the user a live run is slow.** While a run is in flight in live mode (`/health` returns
   `sample: false`), show "A live run takes several minutes" next to the spinner, so the page does
   not look frozen.
6. Test against both modes:

   ```powershell
   # terminal 1, offline (from the repo root)
   $env:SAMPLE_MODE = "1"; uv run python server.py
   # terminal 2
   cd web; npm run dev
   ```

   Check s01 (5 causes), s04 (one cause) and s05 (no cause). Then ask Adrien for a live run, and
   check that the model name shows on each cause.

7. Delete this file and commit.
