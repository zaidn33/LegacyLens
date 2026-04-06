# --- Global State Initializations ---
customer_name = "SARA"
order_amount = 125.50
discount_rate = 0
final_amount = 0

from decimal import Decimal

customer_name = "SARA"
order_amount = Decimal("125.50")
discount_rate = Decimal("0.00")
final_amount = Decimal("0.00")

def main_section():
    global customer_name, order_amount, discount_rate, final_amount

    print("=== ORDER CHECK ===")
    print(f"CUSTOMER: {customer_name}")
    print(f"ORDER AMOUNT: {order_amount}")

    if order_amount > 100:
        discount_rate = Decimal("0.10")
        print("DISCOUNT APPLIED")
    else:
        discount_rate = Decimal("0.00")
        print("NO DISCOUNT")

    final_amount = order_amount - (order_amount * discount_rate)

    print(f"FINAL AMOUNT: {final_amount}")
    print("ORDER COMPLETE")

main_section()
# STOP RUN is implicitly handled by the script ending.