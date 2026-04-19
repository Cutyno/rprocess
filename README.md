# rprocess

rprocess provides glob_rprocessor, a utility to process files matched by a glob pattern with persistent savepoints.

The savepoint file stores per-file results keyed by content hash. This makes reruns faster when files are unchanged, and supports incremental recovery when interruptions happen.

## Installation

```bash
pip install rprocess
```

## Quick Start

```python
from rprocess import glob_rprocessor


def parse_file(path: str) -> int:
	with open(path, "r", encoding="utf-8") as f:
		return len(f.read())


def collect(total, current):
	if total is None:
		return current
	return total + current


total_chars = glob_rprocessor(
	pathname="data/**/*.txt",
	file_function=parse_file,
	safepoint_path=".rprocess.savepoint.pkl",
	cumulative_function=collect,
	recursive=True,
	increment_savepoint=True,
)

print(total_chars)
```

## How Savepoints Work

1. Each matched file is hashed using SHA-256.
2. If the hash already exists in the savepoint, the previous result is reused.
3. If it is new, file_function(path) runs and the result is cached.
4. Savepoint entries for files that no longer exist in the glob result are removed.

This enables fast incremental processing because unchanged files are skipped.

## Interruption and Incremental Recovery

Use increment_savepoint=True to write the savepoint after each newly processed file.

This is useful for long-running jobs:
- If execution is interrupted, progress from already-processed files is preserved.
- The next run resumes with cached results for files completed before the interruption.

If increment_savepoint=False (default), savepoint updates are written at the end when changes occurred.

## API

```python
glob_rprocessor(
	pathname,
	file_function,
	safepoint_path,
	cumulative_function=None,
	root_dir=None,
	dir_fd=None,
	recursive=False,
	verbose=False,
	increment_savepoint=False,
)
```

- pathname: glob pattern to select files.
- file_function: function called per file path.
- safepoint_path: pickle file path used to persist cached results.
- cumulative_function: optional reducer that combines per-file outputs.
- recursive: enable recursive glob patterns like **.
- verbose: print progress and savepoint maintenance messages.
- increment_savepoint: write savepoint after each new file result.

## Development

```bash
python -m pip install --upgrade build twine pytest
python -m pytest
python -m build
python -m twine check dist/*
```
