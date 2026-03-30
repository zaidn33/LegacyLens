# Logic Map

## Executive Summary

This module calculates monthly billing amounts for customer accounts based on usage tiers, applies late-payment penalties, and produces a billing summary record. It is a core component of the accounts receivable pipeline within a financial services billing system.

## Business Objective

Calculate tiered monthly billing charges with late-payment penalties and output a formatted billing summary for downstream invoice generation.

## Inputs and Outputs

### Inputs

- CUSTOMER-RECORD: customer account details (ID, name, status, balance)
- USAGE-RECORD: monthly usage amount in units
- RATE-TABLE: tiered pricing structure (base rate, tier thresholds, tier rates)
- PAYMENT-HISTORY: last payment date and amount

### Outputs

- BILLING-SUMMARY: calculated charges, penalties, total due, billing date
- ERROR-REPORT: validation failures written to error log file

### External Touchpoints

- CUSTOMER-FILE: sequential file read for customer records
- RATE-FILE: indexed file read for rate table lookup
- BILLING-OUTPUT: sequential file write for billing summaries
- ERROR-LOG: sequential file write for error reporting

## Logic Dictionary

| Legacy Name | Proposed Modern Name | Meaning | Confidence |
|:---|:---|:---|:---|
| WS-CUST-ID | customer_id | Unique customer account identifier | High |
| WS-CUST-NAME | customer_name | Customer display name | High |
| WS-CUST-STATUS | account_status | Account status flag: A=Active, S=Suspended, C=Closed | High |
| WS-USAGE-AMT | monthly_usage_units | Usage quantity for the billing period | High |
| WS-BASE-RATE | base_rate | Base charge per unit for tier 1 | High |
| WS-TIER2-THRESHOLD | tier2_threshold | Usage threshold above which tier 2 rate applies | High |
| WS-TIER2-RATE | tier2_rate | Rate per unit for usage above tier 2 threshold | High |
| WS-TIER3-THRESHOLD | tier3_threshold | Usage threshold above which tier 3 rate applies | Medium |
| WS-TIER3-RATE | tier3_rate | Rate per unit for usage above tier 3 threshold | Medium |
| WS-LATE-FEE-PCT | late_fee_percentage | Percentage penalty applied for overdue payments | High |
| WS-DAYS-OVERDUE | days_overdue | Number of days since last payment was due | High |
| WS-TOTAL-DUE | total_amount_due | Final calculated billing amount including penalties | High |
| WS-BILLING-DT | billing_date | Date the billing calculation was performed | High |
| WS-ERR-CODE | error_code | Numeric error identifier for validation failures | Medium |
| WS-ERR-MSG | error_message | Human-readable error description | Medium |

## Step-by-Step Logic Flow

1. Open input files (CUSTOMER-FILE, RATE-FILE) and output files (BILLING-OUTPUT, ERROR-LOG).
2. Read the RATE-TABLE to load tier thresholds and rates into working storage.
3. Read the next CUSTOMER-RECORD. If end-of-file, go to step 12.
4. Validate the customer record: check that CUST-ID is not empty, CUST-STATUS is 'A' (active). If validation fails, write to ERROR-LOG and go to step 3.
5. Read the corresponding USAGE-RECORD for this customer.
6. Calculate base charges: multiply usage units by base rate for units up to tier 2 threshold.
7. If usage exceeds tier 2 threshold, calculate tier 2 charges: multiply excess units (up to tier 3 threshold) by tier 2 rate.
8. If usage exceeds tier 3 threshold, calculate tier 3 charges: multiply excess units beyond tier 3 threshold by tier 3 rate.
9. Sum base + tier 2 + tier 3 charges into subtotal.
10. Check payment history: if days overdue > 30, apply late fee percentage to subtotal and add to total. If days overdue > 90, cap penalty at 25% of subtotal.
11. Write BILLING-SUMMARY record (customer ID, name, subtotal, penalty, total due, billing date) to BILLING-OUTPUT. Go to step 3.
12. Close all files. Write processing summary count to console. Stop.

## Business Rules

- Only active accounts (status = 'A') are billed; suspended and closed accounts are skipped with a log entry.
- Billing uses three pricing tiers: base rate up to tier 2 threshold, tier 2 rate for usage between tier 2 and tier 3 thresholds, tier 3 rate for usage above tier 3 threshold.
- Late payment penalty applies only when payment is overdue by more than 30 days.
- Late penalty is calculated as: subtotal * late_fee_percentage.
- Late penalty is capped at 25% of subtotal when payment is overdue by more than 90 days.
- Customers with zero usage still receive a billing record with $0.00 charges.
- Error records are logged but do not halt batch processing.

## Edge Cases

- Customer with exactly 0 usage units: should produce a $0.00 billing record, not be skipped.
- Usage exactly at a tier boundary: the threshold value itself falls in the lower tier.
- Days overdue exactly at 30: no penalty applied (penalty Negative usage is treated as zero.
- Missing account creation dates trigger an automatic default to standard rates.
- Delinquent records missing past-due flags silently skip penalties.

## Dependencies

- reference_name='definitions.cpy' resolved_filename='definitions.cpy' status='resolved'

## Critical Constraints

- Tier calculation order must be preserved: base -> tier 2 -> tier 3. Charges must never double-count units across tiers.
- Late fee cap at 25% for >90 days overdue must not be removed during modernization.
- Only active accounts may be billed. This is a compliance requirement, not just a filter.
- Error logging must not halt the batch — processing continues with next record.
- Billing date must be set to the actual processing date, not a hardcoded value.

## Assumptions and Ambiguities

### Observed

- Tier thresholds are loaded from RATE-FILE at program start and do not change during execution.
- The program processes all customers in a single sequential pass.
- Error records include the customer ID and a numeric error code.

### Inferred

- The 25% penalty cap appears to be a regulatory or compliance safeguard, though no comment explains the rationale.
- COPY CUSTOMER-RECORD and COPY RATE-RECORD are standard copybooks — field layouts inferred from variable naming conventions.

### Unknown

- Whether negative usage values are possible in production data and how they should be handled.
- Whether rate table can contain more than 3 tiers (the code only references 3).
- The exact file path or JCL configuration for input/output files.

## Test-Relevant Scenarios

- Active customer with usage in tier 1 only: verify base-rate calculation.
- Active customer with usage spanning tiers 1 and 2: verify tier boundary math.
- Active customer with usage spanning all 3 tiers: verify cumulative calculation.
- Active customer with 0 usage: verify $0.00 record is produced.
- Customer with status 'S' (suspended): verify record is skipped and logged.
- Customer with status 'C' (closed): verify record is skipped and logged.
- Customer with empty CUST-ID: verify error logging.
- Payment 31 days overdue: verify penalty is applied.
- Payment exactly 30 days overdue: verify no penalty.
- Payment 91 days overdue: verify penalty is capped at 25%.
- Payment exactly 90 days overdue: verify standard penalty (not capped).
- Usage exactly at tier 2 threshold: verify boundary falls in lower tier.
- Multiple customers processed: verify batch continues past errors.

## Confidence Assessment

**Medium**

Core billing logic, tier calculations, and late-fee rules are well-supported by the source code structure and variable naming. However, two copybooks (CUSTOMER-RECORD, RATE-RECORD) are referenced but not provided, so field layouts are inferred. Negative usage handling and extensibility beyond 3 tiers remain unresolved.
