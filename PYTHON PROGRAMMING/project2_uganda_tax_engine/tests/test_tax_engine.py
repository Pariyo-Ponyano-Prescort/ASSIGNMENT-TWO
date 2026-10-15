from decimal import Decimal

import pytest
from hypothesis import given, strategies as st

from src.tax_engine import (
    Money,
    calculate_paye,
    calculate_vat,
    Invoice,
    calculate_corporate_tax,
    InvalidIncomeError,
)


@pytest.mark.parametrize(
    "income, expected",
    [
        ("335000", "0"),
        ("335001", "0"),
        ("410000", "15000"),
        ("485000", "33750"),
        ("10000000", "2888250"),
        ("10000001", "2888250"),
    ],
)
def test_resident_paye_band_edges(income, expected):
    result = calculate_paye(Money(Decimal(income)))
    assert result.amount == Decimal(expected)


def test_nonresident_schedule():
    result = calculate_paye(
        Money(Decimal("335000")),
        residency="non-resident",
    )
    assert result.amount == Decimal("33500")


def test_negative_income_is_rejected():
    with pytest.raises(InvalidIncomeError):
        calculate_paye(Money(Decimal("-1")))


def test_money_rejects_float():
    with pytest.raises(TypeError):
        Money(0.1)


def test_vat_standard_zero_exempt():
    result = calculate_vat([
        Invoice(Money(Decimal("1000")), "standard"),
        Invoice(Money(Decimal("500")), "zero"),
        Invoice(Money(Decimal("500")), "exempt"),
    ])
    assert result.output_vat.amount == Decimal("180")


def test_corporate_income_tax():
    chargeable, tax = calculate_corporate_tax(
        Money(Decimal("1000000")),
        Money(Decimal("200000")),
    )
    assert chargeable.amount == Decimal("800000")
    assert tax.amount == Decimal("240000")


@given(
    st.integers(min_value=0, max_value=100_000_000),
    st.integers(min_value=0, max_value=100_000_000),
)
def test_paye_nonnegative_monotonic_and_below_income(a, b):
    lower, higher = sorted((a, b))

    lower_tax = calculate_paye(
        Money(Decimal(lower))
    ).amount
    higher_tax = calculate_paye(
        Money(Decimal(higher))
    ).amount

    assert lower_tax >= 0
    assert higher_tax >= lower_tax
    assert higher_tax <= Decimal(higher)
