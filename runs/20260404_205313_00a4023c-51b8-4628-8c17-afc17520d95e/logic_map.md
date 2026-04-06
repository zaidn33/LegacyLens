# Logic Map

## Executive Summary

The HELLOTEST.cbl program is a simple COBOL application that displays user information and performs a basic age check. It iterates over a counter and displays the run number. The program's primary function is to demonstrate basic COBOL syntax and logic.

## Business Objective

Display user information and determine age status

## Inputs and Outputs

### Inputs


### Outputs

- User name
- User age
- Run number
- Age status

### External Touchpoints


## Logic Dictionary

| Legacy Name | Proposed Modern Name | Meaning | Confidence |
|:---|:---|:---|:---|
| USER-NAME | userName | The name of the user | High |
| USER-AGE | userAge | The age of the user | High |
| COUNTER | runCounter | A counter variable used to track the number of iterations | High |

## Step-by-Step Logic Flow

1. Display the program header and user information
2. Initialize the counter variable to 1 and iterate until it exceeds 3
3. Display the run number during each iteration
4. Check if the user's age is 18 or older
5. Display the age status as 'ADULT' if the user is 18 or older, otherwise display 'MINOR'
6. Display the program completion message and stop the program

## Business Rules

- The user's age must be 18 or older to be considered an adult

## Edge Cases

- User age is less than 0
- User age is exactly 18
- User age is greater than 100

## Dependencies


## Critical Constraints

- The age threshold for determining adult status must remain at 18

## Assumptions and Ambiguities

### Observed

- The program uses a fixed user name and age
- The program iterates over a counter three times

### Inferred

- The program is intended for demonstration purposes only
- The user's age is assumed to be a non-negative integer

### Unknown

- The purpose of the program beyond demonstration
- The expected input or output formats

## Test-Relevant Scenarios

- Test with user age less than 18
- Test with user age equal to 18
- Test with user age greater than 18

## Confidence Assessment

**High**

The program's logic is straightforward and easy to follow, with clear variable names and a simple control flow. The business rules are also well-defined and easy to understand.
