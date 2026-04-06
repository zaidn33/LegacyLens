# Logic Map

## Executive Summary

This program calculates an employee bonus based on years of service and salary. It determines the bonus amount by applying a percentage to the employee's salary, with a higher percentage for employees with five or more years of service.

## Business Objective

To calculate and award employee bonuses based on tenure and salary, incentivizing long-term employment.

## Inputs and Outputs

### Inputs

- EMP-NAME (PIC A(20))
- YEARS-SERVICE (PIC 99)
- SALARY (PIC 9(5))

### Outputs

- BONUS (PIC 9(5)V99)
- DISPLAY messages (BONUS APPROVED, STANDARD BONUS, BONUS AMOUNT)

### External Touchpoints


## Logic Dictionary

| Legacy Name | Proposed Modern Name | Meaning | Confidence |
|:---|:---|:---|:---|
| EMP-NAME | EmployeeName | The name of the employee. | High |
| YEARS-SERVICE | YearsOfService | The number of years the employee has been with the company. | High |
| SALARY | EmployeeSalary | The current salary of the employee. | High |
| BONUS | CalculatedBonus | The calculated bonus amount for the employee. | High |

## Step-by-Step Logic Flow

Start program execution.
Initialize employee data (name, years of service, salary).
Display header and employee details.
Check if YEARS-SERVICE is greater than or equal to 5.
If true, calculate BONUS as SALARY * 0.10 and display 'BONUS APPROVED'.
If false, calculate BONUS as SALARY * 0.05 and display 'STANDARD BONUS'.
Display the calculated BONUS AMOUNT.
Display 'PROCESS COMPLETE'.
End program execution.

## Business Rules

- If an employee has 5 or more years of service, their bonus is 10% of their salary.
- If an employee has less than 5 years of service, their bonus is 5% of their salary.

## Edge Cases

- What happens if SALARY is zero?
- What happens if YEARS-SERVICE is zero or negative (though PIC 99 implies non-negative)?
- Handling of very large salaries that might exceed PIC 9(5)V99 capacity after multiplication (unlikely with current percentages).

## Dependencies


## Critical Constraints

- The bonus calculation must adhere to the specified percentages (10% for >= 5 years, 5% for < 5 years).
- The output format for the bonus amount must be maintained (PIC 9(5)V99).

## Assumptions and Ambiguities

### Observed

- The program assumes that YEARS-SERVICE will always be a non-negative integer due to PIC 99.
- The program assumes SALARY is a non-negative integer.
- The bonus calculation uses fixed percentages (0.10 and 0.05).

### Inferred

- The program is intended to run for a single employee at a time.
- The bonus is a monetary value.
- The program is a standalone batch process.

### Unknown

- What is the source of the employee data (EMP-NAME, YEARS-SERVICE, SALARY)?
- Are there any other conditions that might affect bonus eligibility?
- What is the maximum value for YEARS-SERVICE that the system is designed to handle?
- What is the expected behavior if the input data is invalid (e.g., non-numeric characters in numeric fields, though COBOL might handle this with specific settings)?

## Test-Relevant Scenarios

- Test with YEARS-SERVICE = 5, SALARY = 50000 (Expected BONUS = 5000.00).
- Test with YEARS-SERVICE = 4, SALARY = 50000 (Expected BONUS = 2500.00).
- Test with YEARS-SERVICE = 10, SALARY = 60000 (Expected BONUS = 6000.00).
- Test with YEARS-SERVICE = 0, SALARY = 30000 (Expected BONUS = 1500.00).
- Test with SALARY = 0, YEARS-SERVICE = 7 (Expected BONUS = 0.00).
- Test with SALARY = 0, YEARS-SERVICE = 2 (Expected BONUS = 0.00).

## Confidence Assessment

**High**

The logic is straightforward and directly maps to the provided COBOL code. Variable names and their usage are clear, and the business rules are explicitly defined within the conditional statements.
