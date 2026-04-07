# Logic Map

## Executive Summary

This program calculates shipping fees based on package weight. It determines the fee and a status message, then displays the results.

## Business Objective

To calculate the appropriate shipping fee for an order based on its package weight and provide a status message.

## Inputs and Outputs

### Inputs

- ORDER-ID (PIC 9(5))
- DESTINATION (PIC A(20))
- PACKAGE-WEIGHT (PIC 999V99)

### Outputs

- SHIPPING-FEE (PIC 9(4)V99)
- STATUS-MSG (PIC A(20))

### External Touchpoints

- DISPLAY (Console Output)

## Logic Dictionary

| Legacy Name | Proposed Modern Name | Meaning | Confidence |
|:---|:---|:---|:---|
| ORDER-ID | OrderIdentifier | Unique identifier for the order. | High |
| DESTINATION | ShippingDestination | The destination city or region for the shipment. | High |
| PACKAGE-WEIGHT | PackageWeight | The weight of the package to be shipped. | High |
| SHIPPING-FEE | CalculatedShippingFee | The calculated cost of shipping. | High |
| STATUS-MSG | ShippingStatusMessage | A message indicating the shipping status or rate type. | High |

## Step-by-Step Logic Flow

Start program execution.
Initialize variables: ORDER-ID, DESTINATION, PACKAGE-WEIGHT, SHIPPING-FEE, STATUS-MSG.
Display header '=== SHIPPING CHECK ==='.
Display order details: ORDER-ID, DESTINATION, PACKAGE-WEIGHT.
Check if PACKAGE-WEIGHT is greater than 20.
If true: Set SHIPPING-FEE to 25.00 and STATUS-MSG to 'HEAVY PACKAGE'.
If false: Set SHIPPING-FEE to 12.50 and STATUS-MSG to 'STANDARD RATE'.
Display calculated SHIPPING-FEE and STATUS-MSG.
Display completion message 'CHECK COMPLETE'.
Terminate program execution.

## Business Rules

- If PACKAGE-WEIGHT > 20, then SHIPPING-FEE is 25.00 and STATUS-MSG is 'HEAVY PACKAGE'.
- If PACKAGE-WEIGHT <= 20, then SHIPPING-FEE is 12.50 and STATUS-MSG is 'STANDARD RATE'.

## Edge Cases

- Package weight exactly 20.00 will fall into the 'STANDARD RATE' category.
- Non-numeric or invalid data for PACKAGE-WEIGHT is not handled and would cause a runtime error in a real system, but is not explicitly coded for here.

## Dependencies


## Critical Constraints

- The program relies on the COBOL runtime environment for execution.
- Input data for PACKAGE-WEIGHT must be a valid numeric value within the PIC 999V99 format.

## Assumptions and Ambiguities

### Observed

- The program assumes the input PACKAGE-WEIGHT is always a positive numeric value.
- The program assumes the threshold for heavy packages is exactly 20.

### Inferred

- The program is intended to be a standalone utility for calculating shipping fees.
- The values for heavy and standard shipping fees (25.00 and 12.50) are hardcoded.

### Unknown

- What happens if the input data is not valid (e.g., non-numeric)?
- Are there other factors besides weight that influence shipping fees?
- What is the expected range of PACKAGE-WEIGHT values?

## Test-Relevant Scenarios

- Test with PACKAGE-WEIGHT = 18.50 (standard rate).
- Test with PACKAGE-WEIGHT = 20.00 (boundary case, standard rate).
- Test with PACKAGE-WEIGHT = 20.01 (boundary case, heavy rate).
- Test with PACKAGE-WEIGHT = 30.00 (heavy rate).

## Confidence Assessment

**High**

The logic is straightforward and directly maps to the provided COBOL code. All variables and control flow are clearly defined and understood.
