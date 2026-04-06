# Logic Map

## Executive Summary

This COBOL program, HELLOTEST, is a simple demonstration program. It displays user information and a counter loop, concluding with an age-based status check.

## Business Objective

To demonstrate basic COBOL syntax including variable declaration, display statements, a PERFORM VARYING loop, and an IF-ELSE conditional.

## Inputs and Outputs

### Inputs


### Outputs

- Console output of program messages, user name, user age, counter values, and status (ADULT/MINOR).

### External Touchpoints


## Logic Dictionary

| Legacy Name | Proposed Modern Name | Meaning | Confidence |
|:---|:---|:---|:---|
| USER-NAME | userName | Stores the name of the user. | High |
| USER-AGE | userAge | Stores the age of the user. | High |
| COUNTER | counter | A loop counter variable. | High |

## Step-by-Step Logic Flow

Start program execution.
Display initial header message.
Display the value of USER-NAME.
Display the value of USER-AGE.
Initialize COUNTER to 1.
Start a loop that continues as long as COUNTER is less than or equal to 3.
Inside the loop, display the current value of COUNTER.
Increment COUNTER by 1.
Check if COUNTER is greater than 3. If true, exit loop.
If USER-AGE is greater than or equal to 18, display 'STATUS: ADULT'.
Otherwise (if USER-AGE is less than 18), display 'STATUS: MINOR'.
Display a completion message.
Terminate the program.

## Business Rules

- If the user's age is 18 or greater, they are classified as an ADULT.
- If the user's age is less than 18, they are classified as a MINOR.

## Edge Cases

- What happens if USER-AGE is exactly 18? (Handled by >= operator).
- What happens if USER-AGE is a very large number? (PIC 99 limits to 99).
- What happens if USER-NAME contains non-alphabetic characters? (PIC A(20) will accept them).

## Dependencies


## Critical Constraints

- The program must run on a COBOL compiler.
- The maximum value for USER-AGE is 99 due to PIC 99.

## Assumptions and Ambiguities

### Observed

- The program uses fixed initial values for USER-NAME and USER-AGE.
- The loop iterates exactly 3 times.

### Inferred

- The purpose of this program is purely for demonstration or testing.
- The output is intended for direct human viewing on a console.

### Unknown

- What is the intended real-world context for this program?
- Are there any specific character set limitations for USER-NAME beyond standard alphanumeric?

## Test-Relevant Scenarios

- Test with USER-AGE = 21 (expected: ADULT).
- Test with USER-AGE = 17 (expected: MINOR).
- Test with USER-AGE = 18 (expected: ADULT).
- Verify the loop runs exactly 3 times and displays RUN NUMBER: 1, 2, 3.
- Verify the initial display of NAME and AGE.

## Confidence Assessment

**High**

The provided COBOL code is straightforward and self-contained. All variables and logic flows are clearly defined within the source, allowing for high confidence in the analysis and mapping.
