
"""Uganda Tax Engine: money handling and tax calculations.

This module uses the sample tax bands and contribution rates
specified in the assignment. They should not be treated as
verified current Ugandan tax rules.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable


# ==================================================
# 1. Custom exceptions
# ==================================================

class TaxError(Exception):
    """Base exception for tax-related errors."""


class InvalidIncomeError(TaxError):
    """Raised when income or a monetary amount is invalid."""


class NoScheduleForDateError(TaxError):
    """Raised when no tax schedule is available for a date."""


# ==================================================
# 2. Money representation
# ==================================================

def decimal_value(value) -> Decimal:
    """Convert a value to Decimal without allowing floats."""
    if isinstance(value, float):
        raise TypeError("Use Decimal or a string instead of float.")

    try:
        result = value if isinstance(value, Decimal) else Decimal(str(value))
    except Exception as exc:
        raise ValueError("Invalid monetary or numeric value.") from exc

    if not result.is_finite():
        raise ValueError("Monetary values must be finite.")

    return result


@dataclass(frozen=True)
class Money:
    """Represent UGX rounded to the nearest whole shilling."""

    amount: Decimal

    def __post_init__(self):
        amount = decimal_value(self.amount)
        object.__setattr__(
            self,
            "amount",
            amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP),
        )

    def __add__(self, other: "Money") -> "Money":
        if not isinstance(other, Money):
            return NotImplemented
        return Money(self.amount + other.amount)

    def __sub__(self, other: "Money") -> "Money":
        if not isinstance(other, Money):
            return NotImplemented
        return Money(self.amount - other.amount)

    def __mul__(self, factor) -> "Money":
        return Money(self.amount * decimal_value(factor))

    def __lt__(self, other: "Money") -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount < other.amount

    def __le__(self, other: "Money") -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount <= other.amount

    def __eq__(self, other) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount == other.amount

    def __repr__(self) -> str:
        return f"UGX {self.amount:,.0f}"


ZERO_MONEY = Money(Decimal("0"))


# ==================================================
# 3. Tax context, results and abstract interface
# ==================================================

@dataclass(frozen=True)
class TaxContext:
    """Inputs required by a tax calculator."""

    income: Money
    residency: str = "resident"
    tax_date: str | date = "2026-10-01"
    allowances: Money = field(
        default_factory=lambda: Money(Decimal("0"))
    )
    local_service_tax: Money = field(
        default_factory=lambda: Money(Decimal("0"))
    )


@dataclass(frozen=True)
class TaxResult:
    """Result returned by a tax calculator."""

    name: str
    amount: Money
    explanation: str


class Tax(ABC):
    """Abstract interface for tax calculation strategies."""

    @abstractmethod
    def calculate(self, ctx: TaxContext) -> TaxResult:
        """Calculate tax from the supplied context."""
        raise NotImplementedError


# ==================================================
# 4. PAYE calculation
# ==================================================

def validate_tax_date(tax_date: str | date) -> date:
    """Validate the tax date and return a date object."""

    if isinstance(tax_date, datetime):
        raise TypeError(
            "tax_date must be a date object or YYYY-MM-DD string, "
            "not a datetime object."
        )

    if isinstance(tax_date, str):
        try:
            effective_date = date.fromisoformat(tax_date)
        except ValueError as exc:
            raise ValueError(
                "tax_date must use YYYY-MM-DD format."
            ) from exc

        if effective_date.isoformat() != tax_date:
            raise ValueError("tax_date must use YYYY-MM-DD format.")

    elif isinstance(tax_date, date):
        effective_date = tax_date

    else:
        raise TypeError(
            "tax_date must be a date object or YYYY-MM-DD string."
        )

    if effective_date < date(2026, 7, 1):
        raise NoScheduleForDateError(
            "This project implements the sample tax schedule "
            "effective 1 July 2026 onward only."
        )

    return effective_date


def calculate_paye(
    income: Money,
    residency: str = "resident",
    tax_date: str | date = "2026-10-01",
) -> Money:
    """Calculate monthly PAYE using the assignment's sample bands."""

    if not isinstance(income, Money):
        raise TypeError("income must be a Money object.")

    if income.amount < 0:
        raise InvalidIncomeError("Income cannot be negative.")

    validate_tax_date(tax_date)

    if not isinstance(residency, str):
        raise TypeError("residency must be a string.")

    residency = residency.strip().lower()
    x = income.amount

    if residency == "resident":
        if x <= Decimal("335000"):
            tax = Decimal("0")

        elif x <= Decimal("410000"):
            tax = (
                x - Decimal("335000")
            ) * Decimal("0.20")

        elif x <= Decimal("485000"):
            tax = Decimal("15000") + (
                x - Decimal("410000")
            ) * Decimal("0.25")

        else:
            tax = Decimal("33750") + (
                x - Decimal("485000")
            ) * Decimal("0.30")

            if x > Decimal("10000000"):
                tax += (
                    x - Decimal("10000000")
                ) * Decimal("0.10")

    elif residency == "non-resident":
        if x <= Decimal("335000"):
            tax = x * Decimal("0.10")

        elif x <= Decimal("410000"):
            tax = Decimal("33500") + (
                x - Decimal("335000")
            ) * Decimal("0.20")

        else:
            tax = Decimal("48500") + (
                x - Decimal("410000")
            ) * Decimal("0.30")

            if x > Decimal("10000000"):
                tax += (
                    x - Decimal("10000000")
                ) * Decimal("0.10")

    else:
        raise ValueError(
            "Residency must be resident or non-resident."
        )

    return Money(tax)


class PAYE(Tax):
    """PAYE calculator for resident and non-resident employees."""

    def calculate(self, ctx: TaxContext) -> TaxResult:
        """Calculate PAYE on income plus allowances."""

        if ctx.income.amount < 0:
            raise InvalidIncomeError("Income cannot be negative.")

        if ctx.allowances.amount < 0:
            raise InvalidIncomeError("Allowances cannot be negative.")

        if ctx.local_service_tax.amount < 0:
            raise InvalidIncomeError("LST cannot be negative.")

        # LST is deducted separately from net pay in this model.
        taxable_income = ctx.income + ctx.allowances

        amount = calculate_paye(
            income=taxable_income,
            residency=ctx.residency,
            tax_date=ctx.tax_date,
        )

        return TaxResult(
            name="PAYE",
            amount=amount,
            explanation=(
                "Calculated using the assignment's configured "
                "PAYE bands."
            ),
        )


# ==================================================
# 5. Payroll and NSSF
# ==================================================

@dataclass(frozen=True)
class PayrollResult:
    """Store the results of a monthly payroll calculation."""

    gross_plus_allowances: Money
    employee_nssf: Money
    employer_nssf: Money
    lst: Money
    paye: Money
    net_pay: Money


def calculate_payroll(
    gross_pay: Money,
    allowances: Money = ZERO_MONEY,
    residency: str = "resident",
    lst: Money = ZERO_MONEY,
    tax_date: str | date = "2026-10-01",
) -> PayrollResult:
    """Calculate payroll and return a PayrollResult object."""

    if not all(
        isinstance(value, Money)
        for value in (gross_pay, allowances, lst)
    ):
        raise TypeError(
            "gross_pay, allowances and lst must be Money objects."
        )

    if min(
        gross_pay.amount,
        allowances.amount,
        lst.amount,
    ) < 0:
        raise InvalidIncomeError(
            "Gross pay, allowances and LST must be non-negative."
        )

    # Salary plus allowances
    gross_plus_allowances = gross_pay + allowances

    # Assignment's sample NSSF assumptions
    employee_nssf = gross_pay * Decimal("0.05")
    employer_nssf = gross_pay * Decimal("0.10")

    # Calculate PAYE on salary plus allowances
    paye_result = PAYE().calculate(
        TaxContext(
            income=gross_pay,
            allowances=allowances,
            residency=residency,
            tax_date=tax_date,
            local_service_tax=lst,
        )
    )

    paye = paye_result.amount

    # Employee net pay excludes the employer's NSSF contribution.
    net_pay = Money(
        gross_plus_allowances.amount
        - employee_nssf.amount
        - lst.amount
        - paye.amount
    )

    return PayrollResult(
        gross_plus_allowances=gross_plus_allowances,
        employee_nssf=employee_nssf,
        employer_nssf=employer_nssf,
        lst=lst,
        paye=paye,
        net_pay=net_pay,
    )


# ==================================================
# 6. VAT
# ==================================================

@dataclass(frozen=True)
class Invoice:
    """Invoice data for simplified VAT calculations."""

    amount: Money
    category: str
    input_vat: Money = field(
        default_factory=lambda: Money(Decimal("0"))
    )


@dataclass(frozen=True)
class VATResult:
    """Output VAT, recoverable input VAT and net payable."""

    output_vat: Money
    input_vat: Money
    net_payable: Money


def calculate_vat(invoices: Iterable[Invoice]) -> VATResult:
    """Calculate VAT using the assignment's sample categories."""

    output_vat = Decimal("0")
    input_vat = Decimal("0")

    for invoice in invoices:
        if not isinstance(invoice, Invoice):
            raise TypeError("Every item must be an Invoice object.")

        if (
            invoice.amount.amount < 0
            or invoice.input_vat.amount < 0
        ):
            raise InvalidIncomeError(
                "Invoice amounts cannot be negative."
            )

        category = invoice.category.strip().lower()

        if category == "standard":
            output_vat += (
                invoice.amount.amount * Decimal("0.18")
            )
            input_vat += invoice.input_vat.amount

        elif category in ("zero", "exempt"):
            # Assignment's simplified assumption:
            # neither output nor input VAT is included.
            continue

        else:
            raise ValueError(
                f"Unknown VAT category: {invoice.category}"
            )

    output = Money(output_vat)
    recoverable = Money(input_vat)

    return VATResult(
        output_vat=output,
        input_vat=recoverable,
        net_payable=Money(
            output.amount - recoverable.amount
        ),
    )


# ==================================================
# 7. Corporate tax
# ==================================================

def calculate_corporate_tax(
    revenue: Money,
    allowable_deductions: Money,
) -> tuple[Money, Money]:
    """Return chargeable income and tax at the sample 30% rate."""

    if not isinstance(revenue, Money):
        raise TypeError("revenue must be a Money object.")

    if not isinstance(allowable_deductions, Money):
        raise TypeError(
            "allowable_deductions must be a Money object."
        )

    if (
        revenue.amount < 0
        or allowable_deductions.amount < 0
    ):
        raise InvalidIncomeError(
            "Revenue and deductions cannot be negative."
        )

    chargeable_income = Money(
        max(
            Decimal("0"),
            revenue.amount - allowable_deductions.amount,
        )
    )

    tax = chargeable_income * Decimal("0.30")

    return chargeable_income, tax


# ==================================================
# 8. Tax scenario planner
# ==================================================

@dataclass(frozen=True)
class TaxScenario:
    """One salary scenario for comparison."""

    label: str
    income: Money
    residency: str = "resident"


class TaxPlanner:
    """Compare PAYE across salary scenarios."""

    def compare(
        self,
        first: TaxScenario,
        second: TaxScenario,
        tax_date: str | date = "2026-10-01",
    ) -> dict[str, Money]:
        """Calculate and compare PAYE for two scenarios."""

        tax_first = calculate_paye(
            first.income,
            first.residency,
            tax_date,
        )

        tax_second = calculate_paye(
            second.income,
            second.residency,
            tax_date,
        )

        return {
            "first_tax": tax_first,
            "second_tax": tax_second,
            "tax_difference": Money(
                tax_second.amount - tax_first.amount
            ),
        }
