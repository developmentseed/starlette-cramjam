# Contributing

Issues and pull requests are more than welcome.

We recommand using [`uv`](https://docs.astral.sh/uv) as project manager for development.

See https://docs.astral.sh/uv/getting-started/installation/ for installation 

### dev install

```bash
git clone https://github.com/developmentseed/starlette-cramjam.git
cd starlette-cramjam

uv sync
```

You can then run the tests with the following command:

```python
uv run pytest --cov starlette_cramjam --cov-report xml --cov-report term-missing
```

### pre-commit

This repo is set to use `pre-commit` to run *isort*, *flake8*, *pydocstring*, *black* ("uncompromising Python code formatter") and mypy when committing new code.

```bash
pre-commit install
```
