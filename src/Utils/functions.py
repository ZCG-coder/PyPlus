"""Useful functions"""

from src.constants import textchars
from src.modules import iskeyword

DARK_COLOR = 128


def is_binary_string(byte) -> bool:
    return bool(byte.translate(None, textchars))


def is_valid_name(name) -> bool:
    return name.isidentifier() and not iskeyword(name)
