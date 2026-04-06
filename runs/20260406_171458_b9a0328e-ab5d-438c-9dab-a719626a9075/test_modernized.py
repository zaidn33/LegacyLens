import pytest
from io import StringIO
import sys

# Assuming the main logic is in a file named 'program_logic.py'
# If not, adjust the import statement accordingly
from program_logic import display_header, display_user_info, process_counter_loop, display_completion_message, main

def test_display_header(capsys):
    display_header()
    captured = capsys.readouterr()
    assert captured.out == "--- Program Header ---\n"

def test_display_user_info(capsys):
    display_user_info("Bob", 30)
    captured = capsys.readouterr()
    assert captured.out == "User Name: Bob\nUser Age: 30\n"

def test_process_counter_loop_adult(capsys):
    process_counter_loop(25)
    captured = capsys.readouterr()
    assert captured.out == "Counter: 1\nCounter: 2\nCounter: 3\nSTATUS: ADULT\n"

def test_process_counter_loop_minor(capsys):
    process_counter_loop(17)
    captured = capsys.readouterr()
    assert captured.out == "Counter: 1\nCounter: 2\nCounter: 3\nSTATUS: MINOR\n"

def test_process_counter_loop_exact_adult(capsys):
    process_counter_loop(18)
    captured = capsys.readouterr()
    assert captured.out == "Counter: 1\nCounter: 2\nCounter: 3\nSTATUS: ADULT\n"

def test_display_completion_message(capsys):
    display_completion_message()
    captured = capsys.readouterr()
    assert captured.out == "PROGRAM COMPLETE.\n"

# Test for the main function to capture overall output
def test_main_flow(capsys):
    # Temporarily redirect stdout to capture print statements from main
    old_stdout = sys.stdout
    sys.stdout = captured_output = StringIO()

    main()

    sys.stdout = old_stdout # Restore stdout
    output = captured_output.getvalue()

    # Expected output based on placeholder values in main (Alice, 25)
    expected_output = "--- Program Header ---\nUser Name: Alice\nUser Age: 25\nCounter: 1\nCounter: 2\nCounter: 3\nSTATUS: ADULT\nPROGRAM COMPLETE.\n"
    assert output == expected_output
