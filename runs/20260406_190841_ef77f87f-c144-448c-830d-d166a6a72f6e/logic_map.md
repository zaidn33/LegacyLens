# Logic Map

## Executive Summary

The ORDERCHK program validates and processes customer orders based on their amount. It calculates a discount for orders exceeding a certain threshold and determines the final payable amount.

## Business Objective

To process customer orders by applying discounts based on order value and calculating the final amount due.

## Inputs and Outputs

### Inputs

- ORDER-AMOUNT (PIC 9(4)V99)
- CUSTOMER-NAME (PIC A(20))

### Outputs

- DISCOUNT-RATE (PIC 9V99)
- FINAL-AMOUNT (PIC 9(4)V99)
- DISPLAY messages

### External Touchpoints


## Logic Dictionary

| Legacy Name | Proposed Modern Name | Meaning | Confidence |
|:---|:---|:---|:---|
| ORDER-AMOUNT | OrderAmount | The total monetary value of the customer's order before any discounts. | High |
| DISCOUNT-RATE | DiscountRate | The percentage discount applied to the order amount. | High |
| FINAL-AMOUNT | FinalAmount | The final amount payable after applying any applicable discounts. | High |
| CUSTOMER-NAME | CustomerName | The name of the customer placing the order. | High |

## Step-by-Step Logic Flow

Start the program execution.
Display program header '=== ORDER CHECK =='.
Display customer name.
Display original order amount.
Check if ORDER-AMOUNT is greater than 100.
If true, set DISCOUNT-RATE to 0.10 and display 'DISCOUNT APPLIED'.
If false, set DISCOUNT-RATE to 0.00 and display 'NO DISCOUNT'.
Calculate FINAL-AMOUNT by subtracting the discount amount (ORDER-AMOUNT * DISCOUNT-RATE) from ORDER-AMOUNT.
Display the calculated FINAL-AMOUNT.
Display 'ORDER COMPLETE'.
Terminate the program.

## Business Rules

- If ORDER-AMOUNT is greater than 100, apply a 10% discount (DISCOUNT-RATE = 0.10).
- If ORDER-AMOUNT is 100 or less, no discount is applied (DISCOUNT-RATE = 0.00).
- FINAL-AMOUNT is calculated as ORDER-AMOUNT - (ORDER-AMOUNT * DISCOUNT-RATE).

## Edge Cases

- Order amount exactly 100: No discount should be applied.
- Order amount slightly above 100 (e.g., 100.01): Discount should be applied.
- Order amount of 0: No discount should be applied, final amount is 0.

## Dependencies


## Critical Constraints

- The ORDER-AMOUNT must be a numeric value.
- The program relies on hardcoded values for discount thresholds and rates.

## Assumptions and Ambiguities

### Observed

- The discount threshold is hardcoded at 100.
- The discount rate for orders > 100 is hardcoded at 0.10 (10%).

### Inferred

- The program assumes that the input ORDER-AMOUNT is always a valid positive number.
- The program assumes that the DISPLAY statements are for informational purposes and do not require specific handling or logging.

### Unknown

- What happens if ORDER-AMOUNT is negative?
- Are there any other conditions that might affect the discount or final amount?
- What is the source of the ORDER-AMOUNT and CUSTOMER-NAME data?

## Test-Relevant Scenarios

- Test with ORDER-AMOUNT = 150.00 (should apply discount).
- Test with ORDER-AMOUNT = 100.00 (should not apply discount).
- Test with ORDER-AMOUNT = 50.00 (should not apply discount).
- Test with ORDER-AMOUNT = 100.01 (should apply discount).
- Test with ORDER-AMOUNT = 0.00 (should not apply discount).

## Confidence Assessment

**High**

The logic is straightforward and directly implemented in the provided COBOL snippet. Variable meanings and flow are clear. The primary ambiguity lies in unstated business rules or input validation not present in this snippet.
