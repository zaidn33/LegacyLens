import pytest

# Mocking the global state for testing
@pytest.fixture(autouse=True)
def mock_global_state(monkeypatch):
    monkeypatch.setattr(__name__, 'item_name', "MONITOR")
    monkeypatch.setattr(__name__, 'item_count', 12)
    monkeypatch.setattr(__name__, 'reorder_level', 15)
    monkeypatch.setattr(__name__, 'status_msg', "")

def test_stock_ok_case(capsys, monkeypatch):
    # Set item_count to be >= reorder_level
    monkeypatch.setattr(__name__, 'item_count', 20)
    
    # Re-execute the script logic (simulated)
    # In a real scenario, you'd import and run the function containing this logic.
    # For this example, we'll re-evaluate the conditions.
    
    # Simulate the print statements and conditional logic
    print("=== INVENTORY STATUS CHECK ===")
    print(f"ITEM: {item_name}")
    print(f"COUNT: {item_count}")

    if item_count < reorder_level:
        status_msg = "REORDER NEEDED"
    else:
        status_msg = "STOCK OK"

    print(f"STATUS: {status_msg}")
    print("CHECK COMPLETE")

    captured = capsys.readouterr()
    assert "STATUS: STOCK OK" in captured.out
    assert "ITEM: MONITOR" in captured.out
    assert "COUNT: 20" in captured.out

def test_reorder_needed_case(capsys, monkeypatch):
    # Set item_count to be < reorder_level
    monkeypatch.setattr(__name__, 'item_count', 10)
    
    # Simulate the print statements and conditional logic
    print("=== INVENTORY STATUS CHECK ===")
    print(f"ITEM: {item_name}")
    print(f"COUNT: {item_count}")

    if item_count < reorder_level:
        status_msg = "REORDER NEEDED"
    else:
        status_msg = "STOCK OK"

    print(f"STATUS: {status_msg}")
    print("CHECK COMPLETE")

    captured = capsys.readouterr()
    assert "STATUS: REORDER NEEDED" in captured.out
    assert "ITEM: MONITOR" in captured.out
    assert "COUNT: 10" in captured.out

def test_initial_state(capsys, mock_global_state):
    # This test verifies the output with the initial global state values
    # Re-execute the script logic (simulated)
    print("=== INVENTORY STATUS CHECK ===")
    print(f"ITEM: {item_name}")
    print(f"COUNT: {item_count}")

    if item_count < reorder_level:
        status_msg = "REORDER NEEDED"
    else:
        status_msg = "STOCK OK"

    print(f"STATUS: {status_msg}")
    print("CHECK COMPLETE")

    captured = capsys.readouterr()
    assert "STATUS: REORDER NEEDED" in captured.out # Because initial item_count (12) < reorder_level (15)
    assert "ITEM: MONITOR" in captured.out
    assert "COUNT: 12" in captured.out
