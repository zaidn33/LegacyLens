import pytest
from backend.provider import MockProvider

def test_json_repair_salvage():
    """
    Verifies that the LLMProvider can salvage a truncated JSON response 
    containing a code block using json-repair.
    """
    truncated_json = (
        '{ "generated_code": "def hello():\\n    print(\'world\')", '
        '"generated_tests": "def test_hello(): pass", '
        '"implementation_choices": "simple", '
        '"logic_step_mapping": [], '
        '"deferred_items": ['
    )
    
    provider = MockProvider()
    parsed = provider._parse_json(truncated_json)
    
    assert "generated_code" in parsed, f"Missing generated_code: {parsed}"
    # Using a simple check to see exactly what's inside
    code = parsed["generated_code"]
    expected = "def hello():"
    assert expected in code, f"Expected '{expected}' in '{code}'"
    
def test_json_repair_malformed():
    """Verifies that even seriously malformed JSON is salvaged if possible."""
    malformed_json = '{ "generated_code": "print(1)" some other text { "foo": 1 }'
    provider = MockProvider()
    parsed = provider._parse_json(malformed_json)
    assert "generated_code" in parsed
    assert parsed["generated_code"] == "print(1)"

def test_json_repair_list_wrapper():
    """
    Verifies that the LLMProvider can 'flatten' a response that is 
    accidentally wrapped in a JSON list.
    """
    wrapped_json = '[{ "generated_code": "print(\'flattened\')" }]'
    provider = MockProvider()
    
    parsed = provider._parse_json(wrapped_json)
    assert isinstance(parsed, dict)
    assert parsed["generated_code"] == "print('flattened')"
