# Logic Map

## Executive Summary

The SIMPBATCH program calculates employee bonuses based on years of service and writes the results to a report file. The program reads employee records from a sequential file, applies bonus rules, and generates an output report.

## Business Objective

Calculate employee bonuses and generate a report

## Inputs and Outputs

### Inputs

- EMP-FILE

### Outputs

- RPT-FILE

### External Touchpoints

- EMPFILE
- RPTFILE

## Logic Dictionary

| Legacy Name | Proposed Modern Name | Meaning | Confidence |
|:---|:---|:---|:---|
| EMP-ID | Employee ID | Unique identifier for the employee | High |
| EMP-NAME | Employee Name | Name of the employee | High |
| EMP-BASE-SALARY | Base Salary | Employee's base salary | High |
| EMP-YEARS-SERVICE | Years of Service | Number of years the employee has been with the company | High |
| WS-BONUS | Calculated Bonus | Bonus amount calculated based on years of service | High |
| WS-TOTAL | Total Compensation | Total compensation including bonus | High |

## Step-by-Step Logic Flow

Open input file EMP-FILE and output file RPT-FILE
Read the first employee record from EMP-FILE
Loop until end of file: calculate bonus and total compensation for each employee
Write the calculated bonus and total compensation to RPT-FILE
Read the next employee record from EMP-FILE
Close EMP-FILE and RPT-FILE

## Business Rules

- If years of service is greater than 10, bonus is 15% of base salary
- If years of service is between 5 and 10, bonus is 10% of base salary
- If years of service is less than or equal to 5, bonus is 5% of base salary

## Edge Cases

- Employee with no years of service
- Employee with negative years of service
- Employee with extremely high years of service

## Dependencies

- reference_name='EMPFILE' resolved_filename='EMPFILE' status='resolved'
- reference_name='RPTFILE' resolved_filename='RPTFILE' status='resolved'

## Critical Constraints

- Bonus calculation rules must not change
- Total compensation calculation must include bonus

## Assumptions and Ambiguities

### Observed

- The program assumes that the input file EMP-FILE exists and is in the correct format

### Inferred

- The program likely assumes that the output file RPT-FILE will be used for reporting purposes

### Unknown

- The purpose of the FILLER fields in the RPT-REC record is unclear

## Test-Relevant Scenarios

- Test with an employee who has more than 10 years of service
- Test with an employee who has between 5 and 10 years of service
- Test with an employee who has less than or equal to 5 years of service

## Confidence Assessment

**High**

The program logic is straightforward and easy to follow, with clear business rules and calculations. The input and output files are well-defined, and the program assumes a simple and consistent format for the data.
