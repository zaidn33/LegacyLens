# Logic Map

## Executive Summary

This COBOL program, HELLOTEST, is a simple demonstration program. It displays user information and a counter loop, concluding with an age-based status check.

## Business Objective

To demonstrate basic COBOL syntax including variable declaration, display statements, loops, and conditional logic.

## Inputs and Outputs

### Inputs


### Outputs

- Console output of program messages, user name, user age, counter values, and adult/minor status.

### External Touchpoints


## Logic Dictionary

| Legacy Name | Proposed Modern Name | Meaning | Confidence |
|:---|:---|:---|:---|
| USER-NAME | userName | Stores the name of the user. | High |
| USER-AGE | userAge | Stores the age of the user. | High |
| COUNTER | counter | A loop counter variable. | High |

## Step-by-Step Logic Flow

Start program execution.
Display initial program header message.
Display the value of USER-NAME.
Display the value of USER-AGE.
Initialize COUNTER to 1.
Check if COUNTER is greater than 3. If true, exit loop.
Display the current value of COUNTER.
Increment COUNTER by 1.
Go back to loop condition check.
After loop, check if USER-AGE is greater than or equal to 18.
If USER-AGE is 18 or greater, display 'STATUS: ADULT'.
If USER-AGE is less than 18, display 'STATUS: MINOR'.
Display 'PROGRAM COMPLETE.' message.
Terminate the program.

## Business Rules

- If the user's age is 18 or greater, they are classified as an 'ADULT'.
- If the user's age is less than 18, they are classified as a 'MINOR'.

## Edge Cases

- What happens if USER-AGE is exactly 18? (Handled by >=)
- What happens if USER-AGE is a very large number? (PIC 99 limits to 99)
- What happens if USER-NAME contains non-alphabetic characters? (PIC A(20) will accept them)
- The loop condition `COUNTER > 3` means the loop will run for COUNTER values 1, 2, and 3.

## Dependencies


## Critical Constraints

- The program must run in a COBOL environment.
- Output is directed to the standard console.

## Assumptions and Ambiguities

### Observed

- The program uses fixed values for USER-NAME and USER-AGE.
- The loop iterates exactly 3 times.

### Inferred

- The purpose of this program is likely for testing or demonstration of basic COBOL features.
- The 'ZAID' and '21' are placeholder values.

### Unknown

- What is the intended real-world application of this logic?
- Are there any specific performance requirements?
- What are the expected ranges for USER-NAME and USER-AGE in a production scenario?

## Test-Relevant Scenarios

- Scenario 1: USER-AGE is 21 (ADULT). Expected output: 'STATUS: ADULT'.
- Scenario 2: USER-AGE is 17 (MINOR). Expected output: 'STATUS: MINOR'.
- Scenario 3: USER-AGE is 18 (ADULT). Expected output: 'STATUS: ADULT'.
- Scenario 4: Verify the loop runs exactly 3 times, displaying RUN NUMBER 1, 2, and 3.

## Confidence Assessment

**High**

The COBOL code is straightforward and the logic is clearly defined. Variable names and operations are standard, allowing for high confidence in the interpretation of the business logic and its mapping.
