import pytest
from io import StringIO
from unittest.mock import patch

# Assuming the main script is saved as main.py
# from main import check_inventory_status

# For demonstration, let's include the function here
def check_inventory_status():
    item_name = "Widget A"
    item_count = 50
    reorder_level = 75
    status_message = ""

    print("=== INVENTORY STATUS CHECK ===")
    print(f"ITEM-NAME: {item_name}")
    print(f"ITEM-COUNT: {item_count}")

    if item_count < reorder_level:
        status_message = "REORDER NEEDED"
    else:
        status_message = "STOCK OK"

    print(f"STATUS-MSG: {status_message}")
    print("CHECK COMPLETE")

@patch('builtins.print')
def test_reorder_needed(mock_print):
    # Mocking the global variables for specific test case
    with patch('__main__.item_count', 50),
         patch('__main__.reorder_level', 75),
         patch('__main__.item_name', "Widget A"):
        check_inventory_status()
        
        calls = mock_print.call_args_list
        assert calls[0][0][0] == "=== INVENTORY STATUS CHECK ==="
        assert calls[1][0][0] == "ITEM-NAME: Widget A"
        assert calls[2][0][0] == "ITEM-COUNT: 50"
        assert calls[3][0][0] == "STATUS-MSG: REORDER NEEDED"
        assert calls[4][0][0] == "CHECK COMPLETE"

@patch('builtins.print')
def test_stock_ok(mock_print):
    # Mocking the global variables for specific test case
    with patch('__main__.item_count', 100),
         patch('__main__.reorder_level', 75),
         patch('__main__.item_name', "Widget B"):
        check_inventory_status()

        calls = mock_print.call_args_list
        assert calls[0][0][0] == "=== INVENTORY STATUS CHECK ==="
        assert calls[1][0][0] == "ITEM-NAME: Widget B"
        assert calls[2][0][0] == "ITEM-COUNT: 100"
        assert calls[3][0][0] == "STATUS-MSG: STOCK OK"
        assert calls[4][0][0] == "CHECK COMPLETE"

@patch('builtins.print')
def test_stock_ok_exact_match(mock_print):
    # Mocking the global variables for specific test case
    with patch('__main__.item_count', 75),
         patch('__main__.reorder_level', 75),
         patch('__main__.item_name', "Widget C"):
        check_inventory_status()

        calls = mock_print.call_args_list
        assert calls[0][0][0] == "=== INVENTORY STATUS CHECK ==="
        assert calls[1][0][0] == "ITEM-NAME: Widget C"
        assert calls[2][0][0] == "ITEM-COUNT: 75"
        assert calls[3][0][0] == "STATUS-MSG: STOCK OK"
        assert calls[4][0][0] == "CHECK COMPLETE"
