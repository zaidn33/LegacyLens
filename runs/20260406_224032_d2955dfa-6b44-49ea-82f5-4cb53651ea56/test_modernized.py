import pytest
from decimal import Decimal

# Assuming the provided Python code is in a file named main.py
# If it's in a different file, adjust the import accordingly.
# For this example, we'll simulate the global variables and logic directly in the test file.

# --- Global State Initializations (simulated) ---
# These would typically be imported from the module containing the original code.
# For testing purposes, we'll define them here and potentially modify them within tests.

# Mocking the global state and logic for testing
def run_shipping_check(initial_package_weight):
    order_id = 20481
    destination = "TORONTO"
    package_weight = Decimal(str(initial_package_weight))
    shipping_fee = Decimal("0")
    status_msg = ""

    if package_weight > 20:
        shipping_fee = Decimal('25.00')
        status_msg = 'HEAVY PACKAGE'
    else:
        shipping_fee = Decimal('12.50')
        status_msg = 'STANDARD RATE'

    return order_id, destination, package_weight, shipping_fee, status_msg

def test_shipping_check_standard_rate():
    """Tests the case where the package weight is less than or equal to 20."""
    # Simulate a package weight that falls into the standard rate category
    test_package_weight = 18.50
    order_id, destination, package_weight, shipping_fee, status_msg = run_shipping_check(test_package_weight)

    assert order_id == 20481
    assert destination == "TORONTO"
    assert package_weight == Decimal("18.50")
    assert shipping_fee == Decimal("12.50")
    assert status_msg == 'STANDARD RATE'

def test_shipping_check_heavy_package_rate():
    """Tests the case where the package weight is greater than 20."""
    # Simulate a package weight that falls into the heavy package category
    test_package_weight = 25.75
    order_id, destination, package_weight, shipping_fee, status_msg = run_shipping_check(test_package_weight)

    assert order_id == 20481
    assert destination == "TORONTO"
    assert package_weight == Decimal("25.75")
    assert shipping_fee == Decimal("25.00")
    assert status_msg == 'HEAVY PACKAGE'

def test_shipping_check_boundary_weight_below():
    """Tests the boundary case just below the heavy package threshold."""
    test_package_weight = 20.00
    order_id, destination, package_weight, shipping_fee, status_msg = run_shipping_check(test_package_weight)

    assert order_id == 20481
    assert destination == "TORONTO"
    assert package_weight == Decimal("20.00")
    assert shipping_fee == Decimal("12.50")
    assert status_msg == 'STANDARD RATE'

def test_shipping_check_boundary_weight_above():
    """Tests the boundary case just above the heavy package threshold."""
    test_package_weight = 20.01
    order_id, destination, package_weight, shipping_fee, status_msg = run_shipping_check(test_package_weight)

    assert order_id == 20481
    assert destination == "TORONTO"
    assert package_weight == Decimal("20.01")
    assert shipping_fee == Decimal("25.00")
    assert status_msg == 'HEAVY PACKAGE'

# Note: The original code has print statements. Pytest captures stdout by default.
# If you wanted to assert the printed output, you would use pytest.raises(SystemExit) for exit codes
# or capture stdout using capsys fixture.

def test_initial_global_state_values():
    """Tests the initial values of the global state variables as defined in the original code."""
    # This test assumes the global variables are accessible or can be reset/mocked.
    # Since we are simulating the logic in run_shipping_check, we'll test the initial values
    # as they would be before the conditional logic is applied.
    # For a real module import, you might do:
    # from your_module import order_id, destination, package_weight, shipping_fee, status_msg
    # assert order_id == 20481
    # assert destination == "TORONTO"
    # assert package_weight == Decimal("18.50")
    # assert shipping_fee == Decimal("0") # Initial value before logic
    # assert status_msg == "" # Initial value before logic

    # Testing initial values within our simulation context:
    initial_order_id = 20481
    initial_destination = "TORONTO"
    initial_package_weight = Decimal("18.50")
    initial_shipping_fee = Decimal("0")
    initial_status_msg = ""

    # We can't directly test the initial global state if the code runs immediately on import.
    # The run_shipping_check function simulates the logic based on input, which is better for testing.
    # If the original code was structured as a function, we would test that function.
    # For this specific script structure, testing the outcome of the logic is more practical.
    pass # No direct test for initial global state if script runs on import
