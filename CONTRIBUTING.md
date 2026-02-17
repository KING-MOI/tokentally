# Contributing

```sh
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
pytest
ruff check src tests && ruff format --check src tests
mypy
```

Parser changes need a fixture in `tests/fixtures/<source>/` that reproduces the
log shape being handled. Keep fixtures small and free of real prompts.
