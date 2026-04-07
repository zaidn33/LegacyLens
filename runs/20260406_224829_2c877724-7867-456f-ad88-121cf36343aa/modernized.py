from decimal import Decimal

# --- Global State Initializations ---
order_id = 20481
destination = "TORONTO"
package_weight = Decimal("18.50")
shipping_fee = Decimal("0")
status_msg = ""

print("=== SHIPPING CHECK ===")
print(f"ORDER ID: {order_id}")
print(f"DESTINATION: {destination}")
print(f"WEIGHT: {package_weight}")

if package_weight > 20:
    shipping_fee = Decimal('25.00')
    status_msg = 'HEAVY PACKAGE'
else:
    shipping_fee = Decimal('12.50')
    status_msg = 'STANDARD RATE'

print(f"FEE: {shipping_fee}")
print(f"STATUS: {status_msg}")
print("CHECK COMPLETE")
# STOP RUN is handled by the end of the script execution in Python