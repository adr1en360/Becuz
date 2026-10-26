# Handoff for tmb: the owner-first view

Read this once, do the steps, then **delete this file in the same commit as your changes**.

## Why

Adrien ran Becuz live end to end through the UI and recorded two flags:

1. **The running screen reads like a developer log.** Contract IDs, cause codes (`promo_overrun`), "World Model"
   chips and SQL scroll past a shop owner. His idea: the left side (the question, the badge, the status) stays
   still, and the receipt on the right **scrolls itself to each new step** as it arrives.
2. **"Records and checks" looks built for the demo.** It is the proof judges want (Technical, 20 points), but the
   owner is the intended user (Product and UX, 10 points: "easy to use for its intended users").

The answer is **layers**: the owner sees a simple answer by default, and the proof is one click away. Nothing is
removed; judges can still open every receipt.

## What changed on master (server)

1. **`plain` on trace events.** Owner-facing steps now carry a `plain` sentence, for example:
   - "Profit this week is ₦137,695 below a usual week. Checking 6 possible causes."
   - "Checking: a supplier raised the unit cost of a product. The records show ₦46,992 lost."
   - "Double-checked: the second check matches, so it counts."
   - "Ruled out. The records show no loss from this cause this week."
   - "The data source was busy, so Becuz is trying again."

   Internal steps (the Markovian summary) have **no** `plain`: hide them from the owner.
2. **`summary.outcome`**: one sentence, computed only from the measured figures (never a forecast):
   - s01: "Without these 4 causes, this week would have made about ₦383,743, against ₦379,412 in a usual week, and
     chasing the 6 missing transfers brings ₦28,360 back into your account."
   - s04: "Profit is on track; chasing the 6 missing transfers brings ₦33,100 back into your account."
   - s05: "Nothing to fix this week."
3. **Wider questions, friendly refusals.** "How is my shop doing?", "What happened to my business this week?",
   "Where did my money go?" now run the full investigation. Off-topic questions get `400` at once from `POST /runs`
   with: *Becuz explains what happened to your shop's money this week. Try "Why is my profit down this week?",
   "How is my shop doing?" or "Where did my money go?"* Show that message as is.
4. Naira in the report text now rounds halves up, like the UI ("₦6,563").

## What did not change

The routes (`POST /runs`, `GET /runs/<id>`, `POST /confirm`), the request body, and every other report field.

## What to do

1. `git pull origin master` into your branch, then `cd web` and `npm run types` (the schema has `summary.outcome`).
2. **Running screen (flag 1):**
   - Keep the left column fixed: question, badges, a one-line status.
   - The receipt **auto-scrolls to the newest step** as events arrive.
   - Show each event's `plain` text, newest at the bottom. Hide events with no `plain`.
   - Put the technical detail (agent name, action, cause code, engine and model chips, contract ID) behind a
     **"Show technical details"** toggle, off by default.
3. **Report (flag 2), owner layer by default:** the headline, why, money missing, the outcome, what to do, and
   "This was right".
   - Rename "Records and checks" to **"See the receipt"**, collapsed. Inside it, keep the record IDs and the
     Checker's line; put the SQL one more click down (**"Show the query"**).
   - Collapse **"How I got here"** by default (the plain steps when open; technical details behind the same toggle).
   - Replace "103.1% explained / Pulled the other way" with a plain line from `convergence.explained_pct`:
     95% or more: "These causes explain all of this week's change." Otherwise: "These causes explain N% of the
     change; the rest has no clear cause in the records." Keep the bar if it reads well.
4. **Example questions:** under the question box, 3 tappable chips that fill it: "Why is my profit down this
   week?", "How is my shop doing?", "Where did my money go?".
5. **From the meeting screenshot (the end of the report):**
   - An **"If you act on this"** box showing `summary.outcome`, just before "What to do this week". Only that text;
     no numbers of your own.
   - An **"Export PDF"** button: `window.print()` with a print stylesheet (hide buttons, the composer and the
     technical toggles; the receipt prints on white).
   - A **compact footer** of run facts with Solar icons, for example "7m 49s · 27 Zetaris queries · 6 model calls",
     from `stats.duration_s`, `stats.zetaris_queries`, `stats.model_calls`. Keep "How this was run" for the details.
6. Check s01, s04 and s05 in sample mode, and one live run with Adrien. Then **retake the screenshots**
   (`docs/screenshots/`), live for the headline and the model name, since the deck uses them.
7. Delete this file and commit.
