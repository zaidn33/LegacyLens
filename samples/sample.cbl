      *===============================================================*
      * PROGRAM-ID: BILL-CALC
      * AUTHOR:     LEGACY-SYSTEM
      * DATE:       2004-03-15
      *---------------------------------------------------------------*
      * Monthly Billing Calculation Program.
      * Calculates tiered usage charges and late-payment penalties
      * for active customer accounts.
      *===============================================================*

       IDENTIFICATION DIVISION.
       PROGRAM-ID. BILL-CALC.

       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT CUSTOMER-FILE ASSIGN TO 'CUSTFILE'
               ORGANIZATION IS SEQUENTIAL
               FILE STATUS IS WS-CUST-FS.
           SELECT RATE-FILE ASSIGN TO 'RATEFILE'
               ORGANIZATION IS INDEXED
               ACCESS MODE IS RANDOM
               RECORD KEY IS RT-RATE-KEY
               FILE STATUS IS WS-RATE-FS.
           SELECT BILLING-OUTPUT ASSIGN TO 'BILLOUT'
               ORGANIZATION IS SEQUENTIAL
               FILE STATUS IS WS-BILL-FS.
           SELECT ERROR-LOG ASSIGN TO 'ERRLOG'
               ORGANIZATION IS SEQUENTIAL
               FILE STATUS IS WS-ERR-FS.

       DATA DIVISION.
       FILE SECTION.

       FD CUSTOMER-FILE.
       COPY CUSTOMER-RECORD.

       FD RATE-FILE.
       COPY RATE-RECORD.

       FD BILLING-OUTPUT.
       01  BILL-OUT-REC              PIC X(200).

       FD ERROR-LOG.
       01  ERR-LOG-REC               PIC X(200).

       WORKING-STORAGE SECTION.

       01  WS-FILE-STATUS.
           05  WS-CUST-FS            PIC XX.
           05  WS-RATE-FS            PIC XX.
           05  WS-BILL-FS            PIC XX.
           05  WS-ERR-FS             PIC XX.

       01  WS-FLAGS.
           05  WS-EOF-FLAG           PIC X VALUE 'N'.
               88  END-OF-FILE       VALUE 'Y'.

       01  WS-CUSTOMER-DATA.
           05  WS-CUST-ID            PIC X(10).
           05  WS-CUST-NAME          PIC X(30).
           05  WS-CUST-STATUS        PIC X.
               88  CUST-ACTIVE       VALUE 'A'.
               88  CUST-SUSPENDED    VALUE 'S'.
               88  CUST-CLOSED       VALUE 'C'.

       01  WS-USAGE-DATA.
           05  WS-USAGE-AMT          PIC 9(7)V99.

       01  WS-RATE-DATA.
           05  WS-BASE-RATE          PIC 9(3)V9(4).
           05  WS-TIER2-THRESHOLD    PIC 9(7)V99.
           05  WS-TIER2-RATE         PIC 9(3)V9(4).
           05  WS-TIER3-THRESHOLD    PIC 9(7)V99.
           05  WS-TIER3-RATE         PIC 9(3)V9(4).

       01  WS-PAYMENT-DATA.
           05  WS-DAYS-OVERDUE       PIC 9(4).
           05  WS-LATE-FEE-PCT       PIC 9V9(4).

       01  WS-CALC-FIELDS.
           05  WS-BASE-CHARGES       PIC 9(9)V99.
           05  WS-TIER2-CHARGES      PIC 9(9)V99.
           05  WS-TIER3-CHARGES      PIC 9(9)V99.
           05  WS-SUBTOTAL           PIC 9(9)V99.
           05  WS-PENALTY            PIC 9(9)V99.
           05  WS-TOTAL-DUE          PIC 9(9)V99.

       01  WS-BILLING-DT             PIC X(10).

       01  WS-COUNTERS.
           05  WS-RECORDS-READ       PIC 9(6) VALUE 0.
           05  WS-RECORDS-BILLED     PIC 9(6) VALUE 0.
           05  WS-RECORDS-ERROR      PIC 9(6) VALUE 0.

       01  WS-ERR-CODE               PIC 9(4).
       01  WS-ERR-MSG                PIC X(50).

      *===============================================================*
       PROCEDURE DIVISION.
      *===============================================================*

       0000-MAIN.
           PERFORM 1000-INITIALIZE
           PERFORM 2000-PROCESS-CUSTOMERS
               UNTIL END-OF-FILE
           PERFORM 9000-FINALIZE
           STOP RUN.

       1000-INITIALIZE.
           OPEN INPUT  CUSTOMER-FILE
                       RATE-FILE
                OUTPUT BILLING-OUTPUT
                       ERROR-LOG
           ACCEPT WS-BILLING-DT FROM DATE YYYYMMDD
           PERFORM 1100-LOAD-RATES.

       1100-LOAD-RATES.
           READ RATE-FILE INTO WS-RATE-DATA
               KEY IS RT-RATE-KEY
               INVALID KEY
                   DISPLAY 'RATE TABLE LOAD FAILED'
                   STOP RUN.

       2000-PROCESS-CUSTOMERS.
           READ CUSTOMER-FILE INTO WS-CUSTOMER-DATA
               AT END
                   SET END-OF-FILE TO TRUE
               NOT AT END
                   ADD 1 TO WS-RECORDS-READ
                   PERFORM 3000-VALIDATE-CUSTOMER
           END-READ.

       3000-VALIDATE-CUSTOMER.
           IF WS-CUST-ID = SPACES
               MOVE 1001 TO WS-ERR-CODE
               MOVE 'EMPTY CUSTOMER ID' TO WS-ERR-MSG
               PERFORM 8000-LOG-ERROR
           ELSE IF NOT CUST-ACTIVE
               MOVE 1002 TO WS-ERR-CODE
               MOVE 'ACCOUNT NOT ACTIVE' TO WS-ERR-MSG
               PERFORM 8000-LOG-ERROR
           ELSE
               PERFORM 4000-CALCULATE-BILLING
           END-IF.

       4000-CALCULATE-BILLING.
           INITIALIZE WS-CALC-FIELDS
           PERFORM 4100-CALC-BASE
           PERFORM 4200-CALC-TIER2
           PERFORM 4300-CALC-TIER3
           ADD WS-BASE-CHARGES WS-TIER2-CHARGES
               WS-TIER3-CHARGES GIVING WS-SUBTOTAL
           PERFORM 5000-APPLY-PENALTY
           ADD WS-SUBTOTAL WS-PENALTY GIVING WS-TOTAL-DUE
           PERFORM 6000-WRITE-BILLING.

       4100-CALC-BASE.
           IF WS-USAGE-AMT <= WS-TIER2-THRESHOLD
               COMPUTE WS-BASE-CHARGES =
                   WS-USAGE-AMT * WS-BASE-RATE
           ELSE
               COMPUTE WS-BASE-CHARGES =
                   WS-TIER2-THRESHOLD * WS-BASE-RATE
           END-IF.

       4200-CALC-TIER2.
           IF WS-USAGE-AMT > WS-TIER2-THRESHOLD
               IF WS-USAGE-AMT <= WS-TIER3-THRESHOLD
                   COMPUTE WS-TIER2-CHARGES =
                       (WS-USAGE-AMT - WS-TIER2-THRESHOLD)
                       * WS-TIER2-RATE
               ELSE
                   COMPUTE WS-TIER2-CHARGES =
                       (WS-TIER3-THRESHOLD - WS-TIER2-THRESHOLD)
                       * WS-TIER2-RATE
               END-IF
           END-IF.

       4300-CALC-TIER3.
           IF WS-USAGE-AMT > WS-TIER3-THRESHOLD
               COMPUTE WS-TIER3-CHARGES =
                   (WS-USAGE-AMT - WS-TIER3-THRESHOLD)
                   * WS-TIER3-RATE
           END-IF.

       5000-APPLY-PENALTY.
           MOVE 0 TO WS-PENALTY
           IF WS-DAYS-OVERDUE > 30
               COMPUTE WS-PENALTY =
                   WS-SUBTOTAL * WS-LATE-FEE-PCT
               IF WS-DAYS-OVERDUE > 90
                   IF WS-PENALTY > (WS-SUBTOTAL * 0.25)
                       COMPUTE WS-PENALTY =
                           WS-SUBTOTAL * 0.25
                   END-IF
               END-IF
           END-IF.

       6000-WRITE-BILLING.
           STRING WS-CUST-ID DELIMITED SIZE
                  ',' DELIMITED SIZE
                  WS-CUST-NAME DELIMITED SIZE
                  ',' DELIMITED SIZE
                  WS-SUBTOTAL DELIMITED SIZE
                  ',' DELIMITED SIZE
                  WS-PENALTY DELIMITED SIZE
                  ',' DELIMITED SIZE
                  WS-TOTAL-DUE DELIMITED SIZE
                  ',' DELIMITED SIZE
                  WS-BILLING-DT DELIMITED SIZE
               INTO BILL-OUT-REC
           WRITE BILL-OUT-REC
           ADD 1 TO WS-RECORDS-BILLED.

       8000-LOG-ERROR.
           STRING WS-CUST-ID DELIMITED SIZE
                  ',' DELIMITED SIZE
                  WS-ERR-CODE DELIMITED SIZE
                  ',' DELIMITED SIZE
                  WS-ERR-MSG DELIMITED SIZE
               INTO ERR-LOG-REC
           WRITE ERR-LOG-REC
           ADD 1 TO WS-RECORDS-ERROR.

       9000-FINALIZE.
           CLOSE CUSTOMER-FILE
                 RATE-FILE
                 BILLING-OUTPUT
                 ERROR-LOG
           DISPLAY 'RECORDS READ:   ' WS-RECORDS-READ
           DISPLAY 'RECORDS BILLED: ' WS-RECORDS-BILLED
           DISPLAY 'RECORDS ERROR:  ' WS-RECORDS-ERROR.
