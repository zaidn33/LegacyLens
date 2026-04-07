# --- Global State Initializations ---
item_name = "MONITOR"
item_count = 12
reorder_level = 15
status_msg = ""

print("=== INVENTORY STATUS CHECK ===")
print(f"ITEM: {item_name}")
print(f"COUNT: {item_count}")

if item_count < reorder_level:
    status_msg = "REORDER NEEDED"
else:
    status_msg = "STOCK OK"

print(f"STATUS: {status_msg}")
print("CHECK COMPLETE")
# STOP RUN is handled by the program exiting naturally after the script finishes.