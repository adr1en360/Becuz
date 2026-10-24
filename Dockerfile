# Sample mode only: the full investigation on the bundled synthetic shop data, with no accounts,
# no keys and no network. Live mode needs Nightshift on the host machine, so run it outside Docker.
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.10.8 /uv /bin/uv

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-install-project

COPY . .

ENV PATH="/app/.venv/bin:$PATH" SAMPLE_MODE=1 SERVER_HOST=0.0.0.0 SERVER_PORT=8000
EXPOSE 8000
CMD ["python", "server.py"]
