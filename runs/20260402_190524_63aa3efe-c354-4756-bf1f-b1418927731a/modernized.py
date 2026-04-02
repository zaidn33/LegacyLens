# Modifying logic for run version 2

"""
Billing Calculator — modernized from COBOL BILL-CALC.

Implements tiered usage billing with late-payment penalties.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Protocol


class ErrorLogger(Protocol):
    """Protocol for error logging — batch must not halt on errors."""

    def log_error(self, customer_id: str, error_code: int, message: str) -> None:
        ...


@dataclass
class RateTable:
    """Tiered pricing configuration."""
    base_rate: float
    tier2_threshold: float
    tier2_rate: float
    tier3_threshold: float
    tier3_rate: float


@dataclass
class CustomerRecord:
    """Customer account details."""
    customer_id: str
    customer_name: str
    account_status: str  # 'A' = Active, 'S' = Suspended, 'C' = Closed


@dataclass
class UsageRecord:
    """Monthly usage for a customer."""
    customer_id: str
    monthly_usage_units: float


@dataclass
class PaymentHistory:
    """Payment history for penalty calculation."""
    customer_id: str
    days_overdue: int
    late_fee_percentage: float


@dataclass
class BillingSummary:
    """Output billing record."""
    customer_id: str
    customer_name: str
    subtotal: float
    penalty: float
    total_amount_due: float
    billing_date: date


class InMemoryErrorLogger:
    """Simple error logger that collects errors in memory."""

    def __init__(self) -> None:
        self.errors: list[dict] = []

    def log_error(self, customer_id: str, error_code: int, message: str) -> None:
        self.errors.append({
            "customer_id": customer_id,
            "error_code": error_code,
            "message": message,
        })


def validate_customer(customer: CustomerRecord) -> tuple[bool, int, str]:
    """
    Validate a customer record.

    Returns (is_valid, error_code, error_message).
    Only active accounts pass validation.
    """
    if not customer.customer_id or customer.customer_id.strip() == "":
        return False, 1001, "EMPTY CUSTOMER ID"
    if customer.account_status != "A":
        return False, 1002, "ACCOUNT NOT ACTIVE"
    return True, 0, ""


def calculate_tiered_charges(
    usage_units: float,
    rate_table: RateTable,
) -> tuple[float, float, float]:
    """
    Calculate charges across three pricing tiers.

    Tier order: base -> tier 2 -> tier 3.
    Units are never double-counted across tiers.
    Threshold value itself falls in the lower tier.
    """
    # Base tier: usage up to tier 2 threshold
    if usage_units <= rate_table.tier2_threshold:
        base_charges = usage_units * rate_table.base_rate
    else:
        base_charges = rate_table.tier2_threshold * rate_table.base_rate

    # Tier 2: usage between tier 2 and tier 3 thresholds
    tier2_charges = 0.0
    if usage_units > rate_table.tier2_threshold:
        tier2_units = min(
            usage_units - rate_table.tier2_threshold,
            rate_table.tier3_threshold - rate_table.tier2_threshold,
        )
        tier2_charges = tier2_units * rate_table.tier2_rate

    # Tier 3: usage above tier 3 threshold
    tier3_charges = 0.0
    if usage_units > rate_table.tier3_threshold:
        tier3_units = usage_units - rate_table.tier3_threshold
        tier3_charges = tier3_units * rate_table.tier3_rate

    return base_charges, tier2_charges, tier3_charges


def apply_late_penalty(
    subtotal: float,
    days_overdue: int,
    late_fee_percentage: float,
) -> float:
    """
    Apply late-payment penalty.

    - No penalty if days_overdue <= 30
    - Standard penalty if 30 < days_overdue <= 90
    - Capped at 25% of subtotal if days_overdue > 90
    """
    if days_overdue <= 30:
        return 0.0

    penalty = subtotal * late_fee_percentage

    if days_overdue > 90:
        cap = subtotal * 0.25
        if penalty > cap:
            penalty = cap

    return penalty


def process_billing(
    customers: list[CustomerRecord],
    usage_records: dict[str, UsageRecord],
    payment_history: dict[str, PaymentHistory],
    rate_table: RateTable,
    error_logger: ErrorLogger | None = None,
    billing_date: date | None = None,
) -> list[BillingSummary]:
    """
    Process billing for a batch of customers.

    Error logging does not halt the batch — processing continues
    with the next record.
    """
    if billing_date is None:
        billing_date = date.today()

    if error_logger is None:
        error_logger = InMemoryErrorLogger()

    results: list[BillingSummary] = []

    for customer in customers:
        is_valid, err_code, err_msg = validate_customer(customer)
        if not is_valid:
            error_logger.log_error(customer.customer_id, err_code, err_msg)
            continue

        usage = usage_records.get(customer.customer_id)
        usage_units = usage.monthly_usage_units if usage else 0.0

        base, tier2, tier3 = calculate_tiered_charges(usage_units, rate_table)
        subtotal = base + tier2 + tier3

        payment = payment_history.get(customer.customer_id)
        if payment:
            penalty = apply_late_penalty(
                subtotal, payment.days_overdue, payment.late_fee_percentage
            )
        else:
            penalty = 0.0

        total_due = subtotal + penalty

        results.append(BillingSummary(
            customer_id=customer.customer_id,
            customer_name=customer.customer_name,
            subtotal=subtotal,
            penalty=penalty,
            total_amount_due=total_due,
            billing_date=billing_date,
        ))

    return results
