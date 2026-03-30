       IDENTIFICATION DIVISION.
       PROGRAM-ID. MAIN-ROUTINE.
       
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT CUSTOMER-FILE ASSIGN TO "CUSTDAT.TXT"
               ORGANIZATION IS SEQUENTIAL.
               
       DATA DIVISION.
       FILE SECTION.
       FD  CUSTOMER-FILE.
       COPY "definitions.cpy".
       
       WORKING-STORAGE SECTION.
       01  WS-EOF-FLAG         PIC X VALUE 'N'.
       01  WS-TOTAL-BILLED     PIC 9(7)V99 VALUE ZERO.
       
       PROCEDURE DIVISION.
       100-MAIN-PROCESSING.
           OPEN INPUT CUSTOMER-FILE
           
           PERFORM UNTIL WS-EOF-FLAG = 'Y'
               READ CUSTOMER-FILE
                   AT END
                       MOVE 'Y' TO WS-EOF-FLAG
                   NOT AT END
                       PERFORM 200-PROCESS-RECORD
               END-READ
           END-PERFORM
           
           CLOSE CUSTOMER-FILE
           DISPLAY "TOTAL BILLED: " WS-TOTAL-BILLED
           STOP RUN.
           
       200-PROCESS-RECORD.
           IF CUST-STATUS = "ACTIVE"
               COMPUTE WS-TOTAL-BILLED = WS-TOTAL-BILLED + CUST-BALANCE
           END-IF.
