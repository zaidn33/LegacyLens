# --- Global State Initializations ---
user_name = "ZAID"
user_age = 21
counter = 0

print("=== LEGACY LENS TEST FILE ===")
print(f"NAME: {user_name}")
print(f"AGE: {user_age}")

for counter in range(1, 4):
    print(f"RUN NUMBER: {counter}")

if user_age >= 18:
    print("STATUS: ADULT")
else:
    print("STATUS: MINOR")

print("PROGRAM COMPLETE.")
# STOP RUN is implicitly handled by the end of the script execution.