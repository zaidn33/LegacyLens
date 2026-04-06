# Logic Map

## Executive Summary

This program calculates an employee bonus based on their years of service and salary. It determines the bonus amount by applying a percentage to the salary, with a higher percentage for employees with 5 or more years of service.

## Business Objective

To calculate and award a performance-based bonus to employees, incentivizing loyalty and performance.

## Inputs and Outputs

### Inputs

- EMP-NAME (Employee Name)
- YEARS-SERVICE (Years of Service)
- SALARY (Employee Salary)

### Outputs

- BONUS (Calculated Bonus Amount)
- Display messages indicating bonus approval status and amount.

### External Touchpoints


## Logic Dictionary

| Legacy Name | Proposed Modern Name | Meaning | Confidence |
|:---|:---|:---|:---|
| EMP-NAME | EmployeeName | The name of the employee. | High |
| YEARS-SERVICE | YearsOfService | The number of years the employee has been with the company. | High |
| SALARY | EmployeeSalary | The current annual salary of the employee. | High |
| BONUS | CalculatedBonus | The calculated bonus amount for the employee. | High |

## Step-by-Step Logic Flow

Start the program.
Display header message '=== EMPLOYEE BONUS CHECK ==='.
Display employee name.
Display employee salary.
Check if YEARS-SERVICE is greater than or equal to 5.
If true, calculate BONUS as SALARY * 0.10 and display 'BONUS APPROVED'.
If false, calculate BONUS as SALARY * 0.05 and display 'STANDARD BONUS'.
Display the calculated BONUS AMOUNT.
Display 'PROCESS COMPLETE'.
End the program.

## Business Rules

- If an employee has 5 or more years of service, their bonus is 10% of their salary.
- If an employee has less than 5 years of service, their bonus is 5% of their salary.

## Edge Cases

- What happens if SALARY is zero or negative?
- What happens if YEARS-SERVICE is zero or negative?
- What if the employee name is very long or contains special characters (though PIC A(20) handles length)?
- Potential for integer overflow if SALARY is extremely high and the bonus calculation exceeds PIC 9(5)V99 limits.

## Dependencies


## Critical Constraints

- The bonus calculation must adhere to the specified percentages (10% for >= 5 years, 5% for < 5 years).
- The output format for the bonus amount must be consistent with the PIC 9(5)V99 definition.

## Assumptions and Ambiguities

### Observed

- The program assumes that SALARY and YEARS-SERVICE are valid numeric values.
- The program assumes that the bonus percentages (0.10 and 0.05) are fixed business requirements.

### Inferred

- It is inferred that '5' years is the threshold for a higher bonus rate.
- It is inferred that the bonus is a one-time calculation per run, not a recurring process.

### Unknown

- What is the source of the input data (e.g., manual entry, another system)?
- What is the business context for the bonus (e.g., annual, performance-based)?
- Are there any other factors that could influence bonus calculation not present in this snippet?
- What is the expected behavior if the input data is invalid (e.g., non-numeric)?
- What is the maximum possible salary and years of service that the system is designed to handle?

## Test-Relevant Scenarios

- Test with YEARS-SERVICE = 5, SALARY = 50000 (Expected BONUS = 5000)
- Test with YEARS-SERVICE = 10, SALARY = 60000 (Expected BONUS = 6000)
- Test with YEARS-SERVICE = 3, SALARY = 40000 (Expected BONUS = 2000)
- Test with YEARS-SERVICE = 0, SALARY = 30000 (Expected BONUS = 1500)
- Test with YEARS-SERVICE = 4, SALARY = 50000 (Expected BONUS = 2500)

## Confidence Assessment

**High**

The COBOL code is straightforward and the logic for bonus calculation is clearly defined with explicit conditions and calculations. All variables and their usage are directly observable within the provided snippet.
