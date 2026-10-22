# Scaffold

The base works. The idea is still empty.

This folder is built so one policy file can plug in the product later. You do not
need to change the provider clients, the Zetaris client, the SQL guard, the
ledger, or the server.

## What is fixed

- Nightshift first, direct NVIDIA fallback.
- Zetaris read-only access with the SQL guard.
- One ledger for model, query, and blocked events; one trace file for agent steps.
- Sample mode for offline judging.
- A small JSON API and browser shell.

## What is empty

- **Policy**: what the agent does, step by step.
- **Tools**: anything beyond `query_data`, `ask_model`, `remember`, `recall`.
- **Memory**: what is worth keeping.
- **UI copy**: the page is a shell.

## Plug points

### 1. Policy

Create `becuz/policy.py`:

```python
from base.agent import Action, Policy


class IdeaPolicy(Policy):
    def next(self, state):
        if not state.observations:
            return Action("recall", {"query": state.request})
        if len(state.observations) == 1:
            first = state.observations[0]
            result = first.result if first.ok and isinstance(first.result, dict) else {}
            items = result.get("items", [])
            context = "\n".join(item["text"] for item in items)
            system = ("Use this context if it helps:\n" + context) if context else ""
            return Action("ask_model", {"prompt": state.request, "system": system})
        return None

    def result(self, state):
        return state.observations[-1].result
```

Set it in `.env`:

```env
AGENT_POLICY=becuz.policy:IdeaPolicy
```

Keep state in `RunState`, not on the policy. The server reuses one policy
instance for many requests.

### 2. Tools

A tool is a name, a description, and a function:

```python
from base.agent import Tool


def word_count(args, state):
    text = str(args.get("text", ""))
    return {"ok": True, "words": len(text.split())}


def tools():
    return [Tool("word_count", "Count words in text.", word_count)]
```

If the policy class has a `tools()` method, the runtime registers them
automatically. The policy then returns `Action("word_count", {"text": ...})`.

### 3. Memory

`base/memory.py` defines the slot:

```python
remember(text, metadata=None, namespace="default")
recall(query, limit=5, namespace="default")
all(namespace=None)
clear(namespace=None)
```

`JsonMemory` is the local stand-in. To mount Meterless H-MEM, implement the same
four methods over its store and change `build_memory()` in `base/runtime.py`.
The default tools `remember` and `recall` use this interface.

### 4. Provider seam

`Pipeline.ask_messages(messages, label="", model=None)` is the only model call.
It applies Nightshift first, then direct NVIDIA. An empty or failed Nightshift
answer falls back. Engines and policies should call this or the `ask_model` tool;
they should not build HTTP requests.

Nightshift receipts settle after the call. Run `python verify_receipts.py` to
append `kind=model_receipt` proof events; the model event's `signed` field is a
call-time snapshot.

### 5. UI and API

```powershell
python server.py
```

- `GET /` - browser shell.
- `GET /health` - provider flags and sample mode.
- `POST /ask` - `{"request": "..."}` returns the agent result and trace.

Replace the HTML when the idea is ready. The endpoint can stay.

### 6. Sample mode

```powershell
$env:SAMPLE_MODE="1"
python smoke.py
python run.py "SELECT 1 AS one"
python server.py
```

With `uv`, run `uv sync` once, then prefix commands with `uv run`.
Sample mode makes no Zetaris or model calls. It returns canned rows and answers.
Use it for judge reproduction and UI work. Unset `SAMPLE_MODE` for real runs.

## Meterless mapping

- **Scout Intent**: already live in `base/scout.py`.
- **H-MEM**: the `Memory` interface and `JsonMemory` stand-in.
- **World Model**: add a `World` service and tools when the idea needs shared
  entities. Do not build it before the idea needs it.
- **Markovian**: add a chunked runner when a task is too long for one context.
  Do not build it before the idea needs it.

Mount the smallest set that helps. Document which engines are mounted and where.

## Idea checklist

1. One user, one job, one output.
2. Which Zetaris source and tables?
3. Which tools does the agent need?
4. What must it remember between steps or runs?
5. What does "done" look like?
6. What is the two-minute demo path?
7. What fails safely?

## Rules

- No secrets in code, chat, or commits.
- Only read-only SQL reaches Zetaris.
- Keep `base/` free of product logic. Put the idea in `becuz/`.
- Add a test for every new tool and policy.
- Do not carry over names from earlier drafts.
