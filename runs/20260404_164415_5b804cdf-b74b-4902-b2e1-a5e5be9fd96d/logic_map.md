# Logic Map

## Executive Summary

The provided COBOL program, HELLO-WORLD, is designed to print a greeting message to the console a specified number of times. The program utilizes a counter to track the number of iterations and stops once the counter reaches a predefined maximum value.

## Business Objective

Print 'HELLO, WORLD!' to the console 5 times

## Inputs and Outputs

### Inputs


### Outputs

- console output

### External Touchpoints


## Logic Dictionary

| Legacy Name | Proposed Modern Name | Meaning | Confidence |
|:---|:---|:---|:---|
| WS-MESSAGE | greetingMessage | The message to be printed to the console | High |
| WS-COUNTER | iterationCounter | The current iteration number | High |
| WS-MAX | maxIterations | The maximum number of iterations | High |

## Step-by-Step Logic Flow

1. Initialize the iteration counter (WS-COUNTER) to 0 and the maximum iterations (WS-MAX) to 5
2. Perform the PRINT-PARA procedure until the iteration counter equals the maximum iterations
3. Within PRINT-PARA, increment the iteration counter by 1
4. Display the current iteration counter and the greeting message to the console
5. Stop the program once the maximum iterations are reached

## Business Rules

- The program must print the greeting message to the console
- The program must stop after a maximum of 5 iterations

## Edge Cases

- The program does not handle any external inputs or errors
- The program does not account for negative or zero values for the maximum iterations

## Dependencies


## Critical Constraints

- The program must print the greeting message exactly 5 times
- The program must stop after 5 iterations

## Assumptions and Ambiguities

### Observed

- The program uses a fixed greeting message
- The program uses a fixed maximum number of iterations

### Inferred

- The program is designed to run in a console or terminal environment

### Unknown


## Test-Relevant Scenarios

- Test the program with the default maximum iterations (5)
- Test the program with a modified maximum iterations value

## Confidence Assessment

**High**

The program logic is straightforward and easy to understand, with no complex dependencies or ambiguous rules.
