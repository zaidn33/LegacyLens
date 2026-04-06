import pytest
from your_module import process_employee_bonus # Assuming your code is in 'your_module.py'

@pytest.mark.parametrize("name, years, salary, expected_bonus_percentage, expected_message", [
    ("Alice", 7, 50000.00, 0.10, "BONUS APPROVED"),
    ("Bob", 3, 45000.00, 0.05, "STANDARD BONUS"),
    ("Charlie", 5, 60000.00, 0.10, "BONUS APPROVED"),
    ("David", 0, 30000.00, 0.05, "STANDARD BONUS"),
    ("Eve", 10, 75000.00, 0.10, "BONUS APPROVED"),
    ("Frank", 2, 0.00, 0.05, "STANDARD BONUS") 
])
def test_process_employee_bonus_calculation(capsys, name, years, salary, expected_bonus_percentage, expected_message):
    process_employee_bonus(name, years, salary)
    captured = capsys.readouterr()
    
    # Check for the bonus message
    assert expected_message in captured.out

    # Check for the calculated bonus amount (approximate due to formatting)
    expected_bonus_amount = salary * expected_bonus_percentage
    
    # Extract the bonus amount from the output line containing the bonus
    bonus_line = None
    for line in captured.out.splitlines():
        if name in line and "Bonus" in line:
            bonus_line = line
            break
    
    assert bonus_line is not None, f"Bonus line not found for {name}"
    
    # Simple check for presence of formatted bonus amount, more robust parsing might be needed
    # This assumes the bonus is the last item on the line and is formatted
    try:
        parts = bonus_line.split()
        actual_bonus_str = parts[-1]
        # Remove currency symbols and commas for comparison
        actual_bonus_str = actual_bonus_str.replace('$', '').replace(',', '')
        actual_bonus = float(actual_bonus_str)
        
        # Allow for small floating point inaccuracies
        assert abs(actual_bonus - expected_bonus_amount) < 0.01, f"Bonus amount mismatch for {name}. Expected: {expected_bonus_amount}, Got: {actual_bonus}"
    except (IndexError, ValueError) as e:
        pytest.fail(f"Could not parse bonus amount from line: {bonus_line} for {name}. Error: {e}")

def test_process_employee_bonus_header(capsys):
    process_employee_bonus("Test", 1, 1000.00)
    captured = capsys.readouterr()
    assert "Employee Name" in captured.out
    assert "Years Service" in captured.out
    assert "Salary" in captured.out
    assert "Bonus" in captured.out

def test_process_employee_bonus_completion_message(capsys):
    process_employee_bonus("Test", 1, 1000.00)
    captured = capsys.readouterr()
    assert "PROCESS COMPLETE" in captured.out
