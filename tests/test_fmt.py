import pytest

from tokentally.fmt import human_tokens, money


@pytest.mark.parametrize(
    ("n", "text"),
    [(0, "0"), (999, "999"), (1_000, "1.0k"), (1_250, "1.2k"), (3_400_000, "3.4M"), (2_000_000_000, "2.0B")],
)
def test_human_tokens(n: int, text: str) -> None:
    assert human_tokens(n) == text


def test_money_has_thousands_separator() -> None:
    assert money(1234.5) == "$1,234.50"


def test_rounding_never_shows_1000k() -> None:
    assert human_tokens(999_960) == "1.0M"


def test_tiny_nonzero_cost_is_not_shown_as_zero() -> None:
    assert money(0.001) == "<$0.01"
    assert money(0) == "$0.00"
