from __future__ import annotations

from functools import wraps
import re
from typing import TypeAlias

_ExceptionTypes: TypeAlias = type[Exception] | tuple[type[Exception], ...]


def _normalize_message(message: str) -> str:
    return re.sub(r"\s+", " ", message).strip().casefold()


def _expected_type_names(raises: _ExceptionTypes) -> str:
    if isinstance(raises, tuple):
        return ", ".join(exc.__name__ for exc in raises)
    return raises.__name__


def expect_red(*, raises: _ExceptionTypes, message_contains: str, reason: str):
    if not message_contains.strip():
        raise ValueError('message_contains must be a non-empty string')
    if not reason.strip():
        raise ValueError('reason must be a non-empty string')

    normalized_expected_message = _normalize_message(message_contains)
    expected_type_names = _expected_type_names(raises)

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except Exception as exc:
                observed_message = str(exc)
                normalized_observed_message = _normalize_message(observed_message)
                if isinstance(exc, raises) and normalized_expected_message in normalized_observed_message:
                    return
                raise AssertionError(
                    'WRONG FAILURE for expected-red test '
                    f'{func.__name__}: expected {expected_type_names} with normalized message '
                    f'containing {message_contains!r} because {reason}; observed '
                    f'{type(exc).__name__}: {observed_message!r}'
                ) from exc
            raise AssertionError(
                f'XPASS for expected-red test {func.__name__}: {reason}. '
                'Flip this expectation to an ordinary assertion.'
            )

        return wrapper

    return decorator