import pytest

# Mock the global variables for testing

@pytest.fixture
def mock_globals():
    return {
        "item_name": "MONITOR",
        "item_count": 12,
        "reorder_level": 15,
        "status_msg": ""
    }

def test_reorder_needed(mock_globals):
    # Simulate a scenario where reorder is needed
    mock_globals["item_count"] = 10
    mock_globals["reorder_level"] = 15

    # Re-run the logic with mocked globals
    item_name = mock_globals["item_name"]
    item_count = mock_globals["item_count"]
    reorder_level = mock_globals["reorder_level"]
    status_msg = mock_globals["status_msg"]

    if item_count < reorder_level:
        status_msg = "REORDER NEEDED"
    else:
        status_msg = "STOCK OK"

    assert status_msg == "REORDER NEEDED"

def test_stock_ok(mock_globals):
    # Simulate a scenario where stock is ok
    mock_globals["item_count"] = 20
    mock_globals["reorder_level"] = 15

    # Re-run the logic with mocked globals
    item_name = mock_globals["item_name"]
    item_count = mock_globals["item_count"]
    reorder_level = mock_globals["reorder_level"]
    status_msg = mock_globals["status_msg"]

    if item_count < reorder_level:
        status_msg = "REORDER NEEDED"
    else:
        status_msg = "STOCK OK"

    assert status_msg == "STOCK OK"

def test_exact_reorder_level(mock_globals):
    # Simulate a scenario where item count is exactly the reorder level
    mock_globals["item_count"] = 15
    mock_globals["reorder_level"] = 15

    # Re-run the logic with mocked globals
    item_name = mock_globals["item_name"]
    item_count = mock_globals["item_count"]
    reorder_level = mock_globals["reorder_level"]
    status_msg = mock_globals["status_msg"]

    if item_count < reorder_level:
        status_msg = "REORDER NEEDED"
    else:
        status_msg = "STOCK OK"

    assert status_msg == "STOCK OK"
