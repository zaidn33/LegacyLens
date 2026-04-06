
# Employee Bonus Calculator
# This module calculates employee bonuses and generates a report.

def calculate_bonus(years_of_service, base_salary):
    # Calculate bonus based on years of service
    if years_of_service > 10:
        return base_salary * 0.15
    elif 5 <= years_of_service <= 10:
        return base_salary * 0.10
    else:
        return base_salary * 0.05

def calculate_total_compensation(base_salary, bonus):
    # Calculate total compensation including bonus
    return base_salary + bonus

def generate_report(input_file, output_file):
    # Open input and output files
    with open(input_file, 'r') as emp_file, open(output_file, 'w') as rpt_file:
        # Read the first employee record
        for line in emp_file:
            # Extract employee data
            emp_id, emp_name, emp_base_salary, emp_years_service = line.strip().split(',')
            emp_base_salary = float(emp_base_salary)
            emp_years_service = int(emp_years_service)
            
            # Calculate bonus and total compensation
            bonus = calculate_bonus(emp_years_service, emp_base_salary)
            total_compensation = calculate_total_compensation(emp_base_salary, bonus)
            
            # Write the calculated bonus and total compensation to the report file
            rpt_file.write(f'{emp_id},{emp_name},{emp_base_salary},{emp_years_service},{bonus},{total_compensation}\n')
