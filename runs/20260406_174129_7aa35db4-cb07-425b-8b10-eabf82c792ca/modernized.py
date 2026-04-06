import locale

def format_currency(amount):
    try:
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_ALL, 'English_United States.1252')
        except locale.Error:
            pass 
    return locale.currency(amount, grouping=True)

def process_employee_bonus(employee_name, years_service, employee_salary):
    header = f"{'Employee Name':<20} {'Years Service':<15} {'Salary':<15} {'Bonus':<15}"
    print(header)
    print("-" * len(header))

    bonus_percentage = 0.0
    bonus_message = ""

    if years_service >= 5:
        bonus_percentage = 0.10
        bonus_message = "BONUS APPROVED"
    else:
        bonus_percentage = 0.05
        bonus_message = "STANDARD BONUS"

    calculated_bonus = employee_salary * bonus_percentage
    
    formatted_salary = format_currency(employee_salary)
    formatted_bonus = format_currency(calculated_bonus)

    employee_details = f"{employee_name:<20} {years_service:<15} {formatted_salary:<15} {formatted_bonus:<15}"
    print(employee_details)
    print(f"{bonus_message}")
    print("PROCESS COMPLETE")

if __name__ == '__main__':
    # Sample Data - In a real scenario, this would come from a file or database
    sample_employees = [
        {"name": "Alice", "years": 7, "salary": 50000.00},
        {"name": "Bob", "years": 3, "salary": 45000.00},
        {"name": "Charlie", "years": 5, "salary": 60000.00},
        {"name": "David", "years": 0, "salary": 30000.00},
        {"name": "Eve", "years": 10, "salary": 75000.00},
        {"name": "Frank", "years": 2, "salary": 0.00} 
    ]

    for emp in sample_employees:
        process_employee_bonus(emp["name"], emp["years"], emp["salary"])
        print("\n")
