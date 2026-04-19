import pytest

from rprocess import normalize_command


def test_normalize_command_type_error() -> None:
    with pytest.raises(TypeError):
        normalize_command(123)  # type: ignore[arg-type]
