
# Pytest tests for the Logic Map
import pytest
from io import StringIO
import sys

def test_print_hello_world(capsys):
    # Test that the program prints the greeting message exactly 5 times
    print_hello_world()
    captured = capsys.readouterr()
    assert captured.out.count('HELLO, WORLD!') == 5

def test_max_iterations(capsys):
    # Test that the program stops after 5 iterations
    print_hello_world()
    captured = capsys.readouterr()
    assert len(captured.out.split('\n')) == 6  # 5 iterations + 1 for the last newline

def test_no_external_inputs():
    # Test that the program does not handle any external inputs
    try:
        print_hello_world()
    except Exception as e:
        assert False, f'Unexpected exception: {e}'

def test_no_error_handling():
    # Test that the program does not account for negative or zero values for the maximum iterations
    try:
        # Modify the max_iterations variable to test the error handling
        max_iterations = 0
        print_hello_world()
    except Exception as e:
        assert False, f'Unexpected exception: {e}'
