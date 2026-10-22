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
