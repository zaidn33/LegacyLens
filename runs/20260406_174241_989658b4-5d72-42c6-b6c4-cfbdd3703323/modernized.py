import sys

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

if __name__ == "__main__":
    check_inventory_status()
