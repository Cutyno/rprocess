from hashlib import sha256
from pathlib import Path
from pickle import load
import sys

from rprocess import glob_rmprocessor

# Import the module
core = sys.modules['rprocess.glob_rmprocessor']


def _collect(result, current):
    if result is None:
        return [current]
    return [*result, current]


def _hash_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


class FakeAsync:
    def __init__(self, func, args):
        self.func = func
        self.args = args

    def get(self):
        return self.func(*self.args)


class FakePool:
    def __init__(self, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def apply_async(self, func, args=(), error_callback=None):
        try:
            return FakeAsync(func, args)
        except Exception as e:
            if error_callback:
                error_callback(e)
            raise


def test_processes_files_and_persists_savepoint(tmp_path, monkeypatch) -> None:
    file_a = tmp_path / "a.txt"
    file_b = tmp_path / "b.txt"
    file_a.write_text("alpha", encoding="utf-8")
    file_b.write_text("beta", encoding="utf-8")
    savepoint_path = tmp_path / "savepoint.pkl"

    ordered_files = [str(file_a), str(file_b)]
    monkeypatch.setattr(core, "glob", lambda *args, **kwargs: ordered_files)
    monkeypatch.setattr(core, "Pool", FakePool)

    def file_function(path: str) -> str:
        return Path(path).read_text(encoding="utf-8")

    result = glob_rmprocessor(
        "*.txt",
        file_function,
        savepoint_path,
        cumulative_function=_collect,
    )

    assert result == ["alpha", "beta"]
    with savepoint_path.open("rb") as handle:
        savepoint = load(handle)
    assert len(savepoint) == 2
    assert set(savepoint.values()) == {"alpha", "beta"}


def test_reuses_savepoint_for_unchanged_files(tmp_path, monkeypatch) -> None:
    file_a = tmp_path / "a.txt"
    file_b = tmp_path / "b.txt"
    file_a.write_text("alpha", encoding="utf-8")
    file_b.write_text("beta", encoding="utf-8")
    savepoint_path = tmp_path / "savepoint.pkl"

    ordered_files = [str(file_a), str(file_b)]
    monkeypatch.setattr(core, "glob", lambda *args, **kwargs: ordered_files)
    monkeypatch.setattr(core, "Pool", FakePool)

    calls: list[str] = []

    def file_function(path: str) -> str:
        calls.append(path)
        return Path(path).read_text(encoding="utf-8")

    glob_rmprocessor(
        "*.txt",
        file_function,
        savepoint_path,
        cumulative_function=_collect,
    )
    calls.clear()

    result = glob_rmprocessor(
        "*.txt",
        file_function,
        savepoint_path,
        cumulative_function=_collect,
    )

    assert calls == []
    assert result == ["alpha", "beta"]


def test_removes_stale_savepoint_entries(tmp_path, monkeypatch) -> None:
    file_a = tmp_path / "a.txt"
    file_b = tmp_path / "b.txt"
    file_a.write_text("alpha", encoding="utf-8")
    file_b.write_text("beta", encoding="utf-8")
    savepoint_path = tmp_path / "savepoint.pkl"

    monkeypatch.setattr(
        core,
        "glob",
        lambda *args, **kwargs: [str(file_a), str(file_b)],
    )
    monkeypatch.setattr(core, "Pool", FakePool)

    def file_function(path: str) -> str:
        return Path(path).read_text(encoding="utf-8")

    glob_rmprocessor("*.txt", file_function, savepoint_path)

    file_b.unlink()
    monkeypatch.setattr(core, "glob", lambda *args, **kwargs: [str(file_a)])
    glob_rmprocessor("*.txt", file_function, savepoint_path)

    with savepoint_path.open("rb") as handle:
        savepoint = load(handle)
    assert len(savepoint) == 1
    assert _hash_file(file_a) in savepoint


def test_continues_after_file_errors_and_saves_successes(
    tmp_path,
    monkeypatch,
) -> None:
    file_a = tmp_path / "a.txt"
    file_b = tmp_path / "b.txt"
    file_c = tmp_path / "c.txt"
    file_a.write_text("alpha", encoding="utf-8")
    file_b.write_text("beta", encoding="utf-8")
    file_c.write_text("gamma", encoding="utf-8")
    savepoint_path = tmp_path / "savepoint.pkl"

    monkeypatch.setattr(
        core,
        "glob",
        lambda *args, **kwargs: [str(file_a), str(file_b), str(file_c)],
    )
    monkeypatch.setattr(core, "Pool", FakePool)

    def file_function(path: str) -> str:
        if Path(path).name == "b.txt":
            raise ValueError("bad file")
        return Path(path).read_text(encoding="utf-8").upper()

    result = glob_rmprocessor(
        "*.txt",
        file_function,
        savepoint_path,
        cumulative_function=_collect,
    )

    assert result == ["ALPHA", "GAMMA"]
    with savepoint_path.open("rb") as handle:
        savepoint = load(handle)
    assert len(savepoint) == 2
