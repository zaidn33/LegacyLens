
import pytest

def test_calculate_bonus():
    # Test bonus calculation rules
    assert calculate_bonus(11, 1000) == 150
    assert calculate_bonus(7, 1000) == 100
    assert calculate_bonus(3, 1000) == 50

def test_calculate_total_compensation():
    # Test total compensation calculation
    assert calculate_total_compensation(1000, 150) == 1150

def test_generate_report():
    # Test report generation
    input_file = 'test_input.txt'
    output_file = 'test_output.txt'
    
    # Create test input file
    with open(input_file, 'w') as emp_file:
        emp_file.write('1,John Doe,1000,11\n')
        emp_file.write('2,Jane Doe,1000,7\n')
        emp_file.write('3,Bob Smith,1000,3\n')
    
    # Generate report
    generate_report(input_file, output_file)
    
    # Check report contents
    with open(output_file, 'r') as rpt_file:
        lines = rpt_file.readlines()
        assert len(lines) == 3
        assert lines[0].strip().split(',')[4] == '150.0'
        assert lines[1].strip().split(',')[4] == '100.0'
        assert lines[2].strip().split(',')[4] == '50.0'

def test_edge_cases():
    # Test edge cases
    assert calculate_bonus(0, 1000) == 50
    assert calculate_bonus(-1, 1000) == 50
    assert calculate_bonus(100, 1000) == 150
