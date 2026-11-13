# Contributing

Create a virtual environment, then install the development extras:

```bash
python -m pip install -e ".[dev]"
pytest
ruff check .
```

Versions are derived from Git tags by `setuptools-scm`. Do not edit a version constant for releases.
