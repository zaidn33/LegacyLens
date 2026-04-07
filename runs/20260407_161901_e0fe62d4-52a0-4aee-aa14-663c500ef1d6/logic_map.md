# Logic Map

## Executive Summary

This COBOL program, HELLOTEST, serves as a basic demonstration of procedural logic. It displays user information and iterates through a simple counter loop, concluding with an age-based status check.

## Business Objective

To demonstrate fundamental COBOL programming constructs including variable declaration, display statements, loops, and conditional logic.

## Inputs and Outputs

### Inputs


### Outputs

- Console output of program title, user name, user age, loop counter, and adult/minor status.

### External Touchpoints


## Logic Dictionary

| Legacy Name | Proposed Modern Name | Meaning | Confidence |
|:---|:---|:---|:---|
| USER-NAME | UserName | A 20-character alphanumeric field storing the user's name. | High |
| USER-AGE | UserAge | A 2-digit numeric field storing the user's age. | High |
| COUNTER | LoopCounter | A single-digit numeric field used to control the loop iteration. | High |
| MAIN-PARA | MainParagraph | The main entry point and procedural block of the program. | High |

## Step-by-Step Logic Flow

Start program execution at MAIN-PARA.
Display the program title '=== LEGACY LENS TEST FILE ==='.
Display the current value of USER-NAME.
Display the current value of USER-AGE.
Initialize COUNTER to 1.
Start a loop that continues as long as COUNTER is less than or equal to 3.
Inside the loop, display 'RUN NUMBER: ' followed by the current value of COUNTER.
Increment COUNTER by 1.
Check if COUNTER is greater than 3. If true, exit the loop.
If USER-AGE is greater than or equal to 18, display 'STATUS: ADULT'.
Otherwise (if USER-AGE is less than 18), display 'STATUS: MINOR'.
Display 'PROGRAM COMPLETE.'.
Terminate the program execution.

## Business Rules

- The program will display a fixed header message.
- The program will display the initialized USER-NAME and USER-AGE.
- The program will loop exactly 3 times, displaying the current run number in each iteration.
- If the USER-AGE is 18 or greater, the program will output 'STATUS: ADULT'.
- If the USER-AGE is less than 18, the program will output 'STATUS: MINOR'.

## Edge Cases

- What happens if USER-AGE is exactly 18? (Covered by >= rule).
- What happens if USER-AGE is a non-numeric value? (COBOL PIC 9 would typically error or zero-fill depending on compiler settings, but not explicitly handled here).
- What happens if USER-NAME is longer than 20 characters? (Truncation or error depending on compiler).
- What happens if COUNTER exceeds its PIC 9 limit? (Unlikely with the current loop condition).

## Dependencies


## Critical Constraints

- The program must run on a COBOL compiler.
- Console output is the only form of interaction/reporting.
- Fixed initial values for USER-NAME, USER-AGE, and COUNTER.

## Assumptions and Ambiguities

### Observed

- The program uses fixed initial values for USER-NAME, USER-AGE, and COUNTER.
- The loop condition is `COUNTER > 3` and the increment is `BY 1`.

### Inferred

- The `DISPLAY` statements are intended for console output.
- The `STOP RUN` statement signifies program termination.

### Unknown

- The specific COBOL compiler and its behavior for data type violations (e.g., non-numeric USER-AGE).
- The intended purpose or context of this demonstration program.

## Test-Relevant Scenarios

- Execute the program with default values (USER-AGE = 21) to verify all outputs and the loop.
- Manually alter USER-AGE to a value less than 18 (e.g., 17) and verify 'STATUS: MINOR' is displayed.
- Manually alter USER-AGE to a value greater than or equal to 18 (e.g., 18, 50) and verify 'STATUS: ADULT' is displayed.
- Verify the loop runs exactly 3 times for 'RUN NUMBER: 1', 'RUN NUMBER: 2', 'RUN NUMBER: 3'.

## Confidence Assessment

**High**

The COBOL code is straightforward and uses standard syntax. The logic is simple and directly maps to the provided code snippets, with high confidence in variable meanings and control flow interpretation.
