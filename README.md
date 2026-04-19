# rprocess

`rprocess` is a tiny pure-Python module for process-related utility helpers.

## Installation

```bash
pip install rprocess
```

## Quick start

```python
from rprocess import normalize_command

print(normalize_command("  python   -m   http.server  "))
# python -m http.server
```

## Development

```bash
python -m pip install --upgrade build twine pytest
python -m pytest
python -m build
python -m twine check dist/*
```

## Upload to PyPI

```bash
python -m twine upload dist/*
```

Use `--repository testpypi` to test first:

```bash
python -m twine upload --repository testpypi dist/*
```
