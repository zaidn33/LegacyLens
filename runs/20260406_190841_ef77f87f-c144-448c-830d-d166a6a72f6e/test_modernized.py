import pytest
from decimal import Decimal

# Assuming the provided code is in a file named main.py
# from main import main_section, customer_name, order_amount, discount_rate, final_amount

# Mocking the global variables for testing purposes
customer_name = "SARA"
order_amount = Decimal("125.50")
discount_rate = Decimal("0.00")
final_amount = Decimal("0.00")

def main_section():
    global customer_name, order_amount, discount_rate, final_amount

    print("=== ORDER CHECK ===")
    print(f"CUSTOMER: {customer_name}")
    print(f"ORDER AMOUNT: {order_amount}")

    if order_amount > 100:
        discount_rate = Decimal("0.10")
        print("DISCOUNT APPLIED")
    else:
        discount_rate = Decimal("0.00")
        print("NO DISCOUNT")

    final_amount = order_amount - (order_amount * discount_rate)

    print(f"FINAL AMOUNT: {final_amount}")
    print("ORDER COMPLETE")


@pytest.fixture(autouse=True)
def reset_globals():
    global customer_name, order_amount, discount_rate, final_amount
    customer_name = "SARA"
    order_amount = Decimal("125.50")
    discount_rate = Decimal("0.00")
    final_amount = Decimal("0.00")


def test_main_section_discount_applied(capsys):
    global order_amount, discount_rate, final_amount
    order_amount = Decimal("150.00") # Set an order amount that triggers discount
    main_section()
    captured = capsys.readouterr()
    assert "DISCOUNT APPLIED" in captured.out
    assert final_amount == Decimal("135.00") # 150 - (150 * 0.10)

def test_main_section_no_discount(capsys):
    global order_amount, discount_rate, final_amount
    order_amount = Decimal("75.00") # Set an order amount that does not trigger discount
    main_section()
    captured = capsys.readouterr()
    assert "NO DISCOUNT" in captured.out
    assert final_amount == Decimal("75.00") # 75 - (75 * 0.00)

def test_main_section_edge_case_100(capsys):
    global order_amount, discount_rate, final_amount
    order_amount = Decimal("100.00") # Edge case: exactly 100
    main_section()
    captured = capsys.readouterr()
    assert "NO DISCOUNT" in captured.out # Based on the condition `order_amount > 100`
    assert final_amount == Decimal("100.00")

def test_main_section_customer_name(capsys):
    global customer_name
    customer_name = "TEST CUSTOMER"
    main_section()
    captured = capsys.readouterr()
    assert "CUSTOMER: TEST CUSTOMER" in captured.out

def test_main_section_initial_values(capsys):
    # This test relies on the autouse fixture to reset globals
    main_section()
    captured = capsys.readouterr()
    assert "CUSTOMER: SARA" in captured.out
    assert "ORDER AMOUNT: 125.50" in captured.out
    # The discount rate and final amount will be calculated within main_section
    # so we check the final output based on the initial order_amount
    assert "FINAL AMOUNT: 112.95" in captured.out # 125.50 - (125.50 * 0.10)
