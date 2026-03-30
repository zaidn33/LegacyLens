      *===============================================================*
      * PROGRAM-ID: SIMPBATCH
      * AUTHOR:     LEGACY-SYSTEM
      * DATE:       1998-11-20
      *---------------------------------------------------------------*
      * Simple Employee Bonus Calculation Batch Program.
      * Processes a sequential file of employee records, calculates
      * a simple bonus, and writes an output report.
      * No nested performs or complex loops.
      *===============================================================*

       IDENTIFICATION DIVISION.
       PROGRAM-ID. SIMPBATCH.

       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT EMP-FILE ASSIGN TO 'EMPFILE'
               ORGANIZATION IS SEQUENTIAL.
           SELECT RPT-FILE ASSIGN TO 'RPTFILE'
               ORGANIZATION IS SEQUENTIAL.

       DATA DIVISION.
       FILE SECTION.

       FD EMP-FILE.
       01  EMP-REC.
           05  EMP-ID              PIC X(5).
           05  EMP-NAME            PIC X(20).
           05  EMP-BASE-SALARY     PIC 9(6)V99.
           05  EMP-YEARS-SERVICE   PIC 9(2).

       FD RPT-FILE.
       01  RPT-REC.
           05  RPT-EMP-ID          PIC X(5).
           05  FILLER              PIC X(2) VALUE SPACES.
           05  RPT-BONUS-AMT       PIC 9(6)V99.
           05  FILLER              PIC X(2) VALUE SPACES.
           05  RPT-TOTAL-COMP      PIC 9(7)V99.

       WORKING-STORAGE SECTION.
       01  WS-EOF-FLAG             PIC X VALUE 'N'.
           88  END-OF-FILE         VALUE 'Y'.

       01  WS-CALC-FIELDS.
           05  WS-BONUS            PIC 9(6)V99 VALUE 0.
           05  WS-TOTAL            PIC 9(7)V99 VALUE 0.

       PROCEDURE DIVISION.
       0000-MAIN.
           OPEN INPUT EMP-FILE
               OUTPUT RPT-FILE

           READ EMP-FILE
               AT END SET END-OF-FILE TO TRUE
           END-READ

           PERFORM UNTIL END-OF-FILE
               MOVE 0 TO WS-BONUS
               MOVE 0 TO WS-TOTAL

               IF EMP-YEARS-SERVICE > 10
                   COMPUTE WS-BONUS = EMP-BASE-SALARY * 0.15
               ELSE
                   IF EMP-YEARS-SERVICE > 5
                       COMPUTE WS-BONUS = EMP-BASE-SALARY * 0.10
                   ELSE
                       COMPUTE WS-BONUS = EMP-BASE-SALARY * 0.05
                   END-IF
               END-IF

               COMPUTE WS-TOTAL = EMP-BASE-SALARY + WS-BONUS

               MOVE EMP-ID TO RPT-EMP-ID
               MOVE WS-BONUS TO RPT-BONUS-AMT
               MOVE WS-TOTAL TO RPT-TOTAL-COMP
               WRITE RPT-REC

               READ EMP-FILE
                   AT END SET END-OF-FILE TO TRUE
               END-READ
           END-PERFORM

           CLOSE EMP-FILE RPT-FILE
           STOP RUN.
