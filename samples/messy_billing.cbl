       IDENTIFICATION DIVISION.
       PROGRAM-ID. MSYBILL.
      * This program processes billing with lots of dead code and a missing copybook
       ENVIRONMENT DIVISION.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       COPY MSGMACRO.  *> MISSING COPYBOOK!
       01  WS-IN-VARS.
           05  IN-AMT          PIC 9(5)V99.
           05  IN-CUST-TYP     PIC X(3).
           05  IN-DT           PIC 9(8).
       01  WS-OUT-VARS.
           05  OUT-TOT         PIC 9(6)V99.
           05  OUT-FLG         PIC X.
       01  WS-DEAD-VARS.
           05  DUMMY-YR        PIC 9(4) VALUE 1999.
           05  UNUSED-CTR      PIC 9(2) VALUE 0.

       PROCEDURE DIVISION.
       000-MAIN.
           PERFORM 100-INIT
           PERFORM 200-CALC
           PERFORM 300-DEAD-BRANCH
           PERFORM 900-WRAP
           STOP RUN.

       100-INIT.
           MOVE 0 TO OUT-TOT.
           MOVE 'N' TO OUT-FLG.
           IF IN-AMT < 0
               MOVE 'E' TO OUT-FLG
               PERFORM 900-WRAP
               STOP RUN
           END-IF.

       200-CALC.
      * Apply weird discount rules
           IF IN-CUST-TYP = 'VIP'
               COMPUTE OUT-TOT = IN-AMT * 0.85
           ELSE
               IF IN-CUST-TYP = 'EMP'
                   COMPUTE OUT-TOT = IN-AMT * 0.50
               ELSE
                   COMPUTE OUT-TOT = IN-AMT
               END-IF
           END-IF.
           
           IF OUT-TOT > 10000
               MOVE 'Y' TO OUT-FLG
           END-IF.

       300-DEAD-BRANCH.
      * This is unreachable if IN-AMT was negative, but who cares
           IF DUMMY-YR = 2000
               COMPUTE UNUSED-CTR = UNUSED-CTR + 1
           END-IF.

       900-WRAP.
           DISPLAY "BILLING DONE: " OUT-TOT.
           DISPLAY "FLAG: " OUT-FLG.
