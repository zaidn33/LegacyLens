"""
Tests for the billing calculator.

Covers all critical constraints and major business rules from the Logic Map.
"""

import pytest
from datetime import date
from billing_calculator import (
    RateTable,
    CustomerRecord,
    UsageRecord,
    PaymentHistory,
    InMemoryErrorLogger,
    validate_customer,
    calculate_tiered_charges,
    apply_late_penalty,
    process_billing,
)


# --- Fixtures ---

@pytest.fixture
def rate_table():
    return RateTable(
        base_rate=0.10,
        tier2_threshold=1000.0,
        tier2_rate=0.08,
        tier3_threshold=5000.0,
        tier3_rate=0.05,
    )


@pytest.fixture
def billing_date():
    return date(2024, 3, 15)


# --- Critical Constraint Tests ---

class TestCriticalConstraints:
    """Tests that MUST pass — they gate the pipeline."""

    def test_tier_order_no_double_counting(self, rate_table):
        """Tier calculation: base -> tier2 -> tier3, no double-counting."""
        base, tier2, tier3 = calculate_tiered_charges(6000.0, rate_table)
        expected_base = 1000.0 * 0.10   # 100.0
        expected_tier2 = 4000.0 * 0.08  # 320.0
        expected_tier3 = 1000.0 * 0.05  # 50.0
        assert base == pytest.approx(expected_base)
        assert tier2 == pytest.approx(expected_tier2)
        assert tier3 == pytest.approx(expected_tier3)
        total = base + tier2 + tier3
        assert total == pytest.approx(470.0)

    def test_late_fee_cap_at_25_percent(self):
        """Late fee capped at 25% when >90 days overdue."""
        subtotal = 1000.0
        penalty = apply_late_penalty(subtotal, days_overdue=91, late_fee_percentage=0.50)
        assert penalty == pytest.approx(250.0)  # 25% cap

    def test_only_active_accounts_billed(self, rate_table, billing_date):
        """Suspended/closed accounts must not be billed."""
        customers = [
            CustomerRecord("C001", "Active User", "A"),
            CustomerRecord("C002", "Suspended User", "S"),
            CustomerRecord("C003", "Closed User", "C"),
        ]
        usage = {
            "C001": UsageRecord("C001", 500.0),
            "C002": UsageRecord("C002", 500.0),
            "C003": UsageRecord("C003", 500.0),
        }
        logger = InMemoryErrorLogger()
        results = process_billing(
            customers, usage, {}, rate_table,
            error_logger=logger, billing_date=billing_date,
        )
        billed_ids = [r.customer_id for r in results]
        assert "C001" in billed_ids
        assert "C002" not in billed_ids
        assert "C003" not in billed_ids

    def test_error_logging_does_not_halt_batch(self, rate_table, billing_date):
        """Errors must not stop processing of remaining records."""
        customers = [
            CustomerRecord("", "Bad User", "A"),     # invalid
            CustomerRecord("C002", "Good User", "A"),  # valid
        ]
        usage = {"C002": UsageRecord("C002", 100.0)}
        logger = InMemoryErrorLogger()
        results = process_billing(
            customers, usage, {}, rate_table,
            error_logger=logger, billing_date=billing_date,
        )
        assert len(results) == 1
        assert results[0].customer_id == "C002"
        assert len(logger.errors) == 1

    def test_billing_date_is_actual_processing_date(self, rate_table):
        """Billing date must be the actual processing date."""
        customers = [CustomerRecord("C001", "User", "A")]
        usage = {"C001": UsageRecord("C001", 100.0)}
        results = process_billing(customers, usage, {}, rate_table)
        assert results[0].billing_date == date.today()


# --- Business Rule Tests ---

class TestBusinessRules:
    """Tests for major business rules."""

    def test_tier1_only(self, rate_table):
        """Usage within tier 1 only."""
        base, tier2, tier3 = calculate_tiered_charges(500.0, rate_table)
        assert base == pytest.approx(50.0)
        assert tier2 == pytest.approx(0.0)
        assert tier3 == pytest.approx(0.0)

    def test_tier1_and_tier2(self, rate_table):
        """Usage spanning tiers 1 and 2."""
        base, tier2, tier3 = calculate_tiered_charges(3000.0, rate_table)
        assert base == pytest.approx(100.0)   # 1000 * 0.10
        assert tier2 == pytest.approx(160.0)  # 2000 * 0.08
        assert tier3 == pytest.approx(0.0)

    def test_penalty_at_31_days(self):
        """Penalty applies at >30 days overdue."""
        penalty = apply_late_penalty(1000.0, days_overdue=31, late_fee_percentage=0.10)
        assert penalty == pytest.approx(100.0)

    def test_no_penalty_at_30_days(self):
        """No penalty at exactly 30 days."""
        penalty = apply_late_penalty(1000.0, days_overdue=30, late_fee_percentage=0.10)
        assert penalty == pytest.approx(0.0)

    def test_zero_usage_produces_record(self, rate_table, billing_date):
        """Zero-usage customer still gets a $0 billing record."""
        customers = [CustomerRecord("C001", "User", "A")]
        usage = {"C001": UsageRecord("C001", 0.0)}
        results = process_billing(
            customers, usage, {}, rate_table, billing_date=billing_date,
        )
        assert len(results) == 1
        assert results[0].total_amount_due == pytest.approx(0.0)


# --- Edge Case Tests ---

class TestEdgeCases:
    """Tests for boundary conditions."""

    def test_usage_exactly_at_tier2_boundary(self, rate_table):
        """Threshold value falls in the lower tier."""
        base, tier2, tier3 = calculate_tiered_charges(1000.0, rate_table)
        assert base == pytest.approx(100.0)  # 1000 * 0.10
        assert tier2 == pytest.approx(0.0)

    def test_penalty_at_exactly_90_days(self):
        """At exactly 90 days, standard penalty (not capped)."""
        penalty = apply_late_penalty(1000.0, days_overdue=90, late_fee_percentage=0.50)
        assert penalty == pytest.approx(500.0)  # not capped

    def test_empty_customer_id_validation(self):
        """Empty customer ID is a validation failure."""
        is_valid, code, msg = validate_customer(
            CustomerRecord("", "Bad User", "A")
        )
        assert not is_valid
        assert code == 1001
