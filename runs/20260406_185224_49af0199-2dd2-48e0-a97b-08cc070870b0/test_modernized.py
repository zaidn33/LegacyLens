import pytest

# Mock global variables
item_name = "MONITOR"
item_count = 12
reorder_level = 15
status_msg = "SPACES"

def test_reorder_needed():
    global item_count, reorder_level, status_msg
    item_count = 10
    reorder_level = 15
    # Execute the code snippet
    exec("\nprint(\"=== INVENTORY STATUS CHECK ===\")\nprint(f\"ITEM: {item_name}\")\nprint(f\"COUNT: {item_count}\")\n\nif item_count < reorder_level:\n    status_msg = \"REORDER NEEDED\"\nelse:\n    status_msg = \"STOCK OK\"\n\nprint(f\"STATUS: {status_msg}\")\nprint(\"CHECK COMPLETE\")\n")
    assert status_msg == "REORDER NEEDED"

def test_stock_ok():
    global item_count, reorder_level, status_msg
    item_count = 20
    reorder_level = 15
    # Execute the code snippet
    exec("\nprint(\"=== INVENTORY STATUS CHECK ===\")\nprint(f\"ITEM: {item_name}\")\nprint(f\"COUNT: {item_count}\")\n\nif item_count < reorder_level:\n    status_msg = \"REORDER NEEDED\"\nelse:\n    status_msg = \"STOCK OK\"\n\nprint(f\"STATUS: {status_msg}\")\nprint(\"CHECK COMPLETE\")\n")
    assert status_msg == "STOCK OK"

def test_reorder_level_equal_to_count():
    global item_count, reorder_level, status_msg
    item_count = 15
    reorder_level = 15
    # Execute the code snippet
    exec("\nprint(\"=== INVENTORY STATUS CHECK ===\")\nprint(f\"ITEM: {item_name}\")\nprint(f\"COUNT: {item_count}\")\n\nif item_count < reorder_level:\n    status_msg = \"REORDER NEEDED\"\nelse:\n    status_msg = \"STOCK OK\"\n\nprint(f\"STATUS: {status_msg}\")\nprint(\"CHECK COMPLETE\")\n")
    assert status_msg == "STOCK OK"
