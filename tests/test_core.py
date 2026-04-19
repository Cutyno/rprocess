from rprocess import normalize_command


def test_normalize_command_basic() -> None:
    assert (
        normalize_command("  python   -m   http.server  ")
        == "python -m http.server"
    )


def test_normalize_command_empty() -> None:
    assert normalize_command("   ") == ""
