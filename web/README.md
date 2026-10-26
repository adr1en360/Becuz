# Becuz web

The owner-facing UI for Becuz. It renders the Investigation JSON returned by the agent. It computes nothing and shows no invented data.

```bash
npm install
npm run dev      # http://localhost:3000
npm run build
npm run lint
npm run types    # regenerate src/lib/investigation.ts from ../docs/investigation.schema.json
```

`src/lib/investigation.ts` is generated. Change the schema in `becuz/schemas.py`, re-export it to `docs/investigation.schema.json`, then run `npm run types`.

The UI calls the agent server at `NEXT_PUBLIC_API_URL` (default `http://127.0.0.1:8000`). Start it from the repo root with `uv run python server.py`, or `SAMPLE_MODE=1 uv run python server.py` to run on the generated test weeks. In sample mode the form shows a test-week picker.
