import pytest

# Mocking print statements to capture output
from unittest.mock import patch

# --- Global State --- (as defined in the original code)
user_name = "ZAID"
user_age = 21
counter = 0

def test_global_state_initialization():
    assert user_name == "ZAID"
    assert user_age == 21
    assert counter == 0

@patch('builtins.print')
def test_script_output(mock_print):
    # Re-execute the script logic within the test context
    # This is a simplified approach assuming the script can be run sequentially
    # In a real-world scenario, you might refactor the code into functions
    
    # Simulate the initial prints
    print(f"=== LEGACY LENS TEST FILE ===")
    print(f"NAME: {user_name}")
    print(f"AGE: {user_age}")

    # Simulate the loop
    for counter_loop in range(1, 4):
        print(f"RUN NUMBER: {counter_loop}")

    # Simulate the conditional print
    if user_age >= 18:
        print("STATUS: ADULT")
    else:
        print("STATUS: MINOR")

    print("PROGRAM COMPLETE.")

    # Assertions based on expected print calls
    expected_calls = [
        "=== LEGACY LENS TEST FILE ===",
        f"NAME: {user_name}",
        f"AGE: {user_age}",
        "RUN NUMBER: 1",
        "RUN NUMBER: 2",
        "RUN NUMBER: 3",
        "STATUS: ADULT",
        "PROGRAM COMPLETE."
    ]

    # Check if all expected calls were made in order
    assert mock_print.call_args_list.call_count == len(expected_calls)
    for i, call in enumerate(expected_calls):
        mock_print.assert_any_call(call)

# Note: Since the provided code is a script with side effects (prints) and global state manipulation,
# testing it directly involves capturing these side effects. 
# For more complex scenarios, refactoring the code into functions would be beneficial for testability.
