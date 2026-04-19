"""Core utilities for rprocess."""


def normalize_command(command: str) -> str:
    """Normalize whitespace in a shell command string.

    Args:
        command: Raw command string.

    Returns:
        Command string with single spacing between tokens and trimmed ends.

    Raises:
        TypeError: If command is not a string.
    """
    if not isinstance(command, str):
        raise TypeError("command must be a string")

    return " ".join(command.split())
