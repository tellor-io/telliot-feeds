# Telliot Feeds

This package contains reporting tools and datafeeds for Tellor oracles.

[Documentation](https://tellor-io.github.io/telliot-feeds/) (the hosted docs are just a pointer to this README).

## Prerequisites

Install [uv](https://docs.astral.sh/uv/) — it manages the Python 3.12 interpreter and the project venv for you:

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Install

```
uv sync
```

This creates `.venv`, resolves everything from the committed `uv.lock`, and installs the dev tools (pytest, mypy, pre-commit, ape, mkdocs) plus `terra-sdk` — the old manual `pip install terra-sdk` step is gone.

## Run

```
uv run telliot --help
uv run telliot report -a myacct
```

## Development

```
uv run pytest                    # tests
uv run mypy --strict src --implicit-reexport --ignore-missing-imports --disable-error-code misc --exclude src/telliot_feeds/proto/
uv run pre-commit run --all-files
uv run mkdocs build
```

When dependencies change: `uv lock && uv sync`. CI uses `uv sync --frozen` (never edits the lock).
