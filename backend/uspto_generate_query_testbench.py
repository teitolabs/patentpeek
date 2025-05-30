# uspto_generate_query_testbench.py
import unittest
import json
import os
import re # For sanitizing method names

# Attempt to import the function to be tested
try:
    from uspto_generate_query import generate_uspto_patents_query
except ImportError:
    raise ImportError("Ensure 'uspto_generate_query.py' is in the same directory or accessible in PYTHONPATH.")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_VECTORS_FILE = os.path.join(BASE_DIR, 'uspto_generate_query_testvectors.json')

class TestUsptoPatentsQueryGenerator(unittest.TestCase):
    # This class will be populated with test methods dynamically.
    pass

def _create_uspto_test_method(test_case_data):
    """
    Factory function to create a bound test method for a single USPTO test case.
    The returned function will be added to TestUsptoPatentsQueryGenerator.
    """
    description = test_case_data.get("description", "Unnamed_Uspto_Test_Case")
    input_data = test_case_data.get("input")
    expected_display_query = test_case_data.get("expected_display_query")
    expected_url = test_case_data.get("expected_url")
    # USPTO test vectors currently don't have 'expected_error', but could be added.

    # This is the actual function that will be run by unittest for each TC
    def test_method(self): # 'self' will be an instance of TestUsptoPatentsQueryGenerator
        if input_data is None:
            self.fail(f"Test case '{description}' is missing 'input' data.")
            return

        # Prepare arguments for the generate_uspto_patents_query function
        args_for_function = {
            "conditions": input_data.get("conditions"),
            "databases": input_data.get("databases"),
            "combine_conditions_with": input_data.get("combine_conditions_with", "AND") # Default if not in JSON
        }
        
        # Filter out None values if the function signature has defaults and we want to use them
        # For generate_uspto_patents_query, 'conditions' and 'databases' can be None,
        # 'combine_conditions_with' has a default "AND".
        kwargs_to_pass = {}
        if args_for_function["conditions"] is not None:
            kwargs_to_pass["conditions"] = args_for_function["conditions"]
        if args_for_function["databases"] is not None:
            kwargs_to_pass["databases"] = args_for_function["databases"]
        
        # Only pass combine_conditions_with if it's explicitly in the input_data,
        # otherwise the function's default will be used.
        # Or, if we always want to pass it (even if it's the default "AND" from JSON):
        if "combine_conditions_with" in input_data:
             kwargs_to_pass["combine_conditions_with"] = args_for_function["combine_conditions_with"]
        elif args_for_function["conditions"] and len(args_for_function["conditions"]) > 1 : # only relevant if there are multiple conditions
            kwargs_to_pass["combine_conditions_with"] = args_for_function["combine_conditions_with"]


        # Currently, no error cases are defined in the USPTO JSON, so we directly call and check results.
        # If error cases were added, similar logic to the Google testbench for expected_error would go here.
        
        if expected_display_query is None or expected_url is None:
            self.fail(f"Test case '{description}' is missing 'expected_display_query' or 'expected_url'.")
            return

        actual_result = generate_uspto_patents_query(**kwargs_to_pass)

        self.assertEqual(actual_result.get("query_string_display"), expected_display_query,
                         f"Display query mismatch for: {description}\nActual:   {actual_result.get('query_string_display')}\nExpected: {expected_display_query}")
        self.assertEqual(actual_result.get("url"), expected_url,
                         f"URL mismatch for: {description}\nActual:   {actual_result.get('url')}\nExpected: {expected_url}")

    test_method.__doc__ = description
    return test_method

if os.path.exists(TEST_VECTORS_FILE):
    try:
        with open(TEST_VECTORS_FILE, 'r', encoding='utf-8') as f:
            all_test_vectors = json.load(f)

        for i, test_case_from_json in enumerate(all_test_vectors):
            description = test_case_from_json.get("description", f"UsptoTestCase_{i+1}")
            # Sanitize the description to create a valid method name
            sane_description = re.sub(r'\W|^(?=\d)', '_', description) 
            method_name = f"test_{sane_description}_{i}" 

            test_func = _create_uspto_test_method(test_case_from_json)
            setattr(TestUsptoPatentsQueryGenerator, method_name, test_func)
    except json.JSONDecodeError as e:
        def test_json_decode_error(self):
            self.fail(f"Failed to decode JSON from {TEST_VECTORS_FILE}: {e}")
        setattr(TestUsptoPatentsQueryGenerator, "test_json_decode_error", test_json_decode_error)
    except Exception as e: # Catch other potential errors during test generation
        def test_generation_error(self):
            self.fail(f"An error occurred during test generation from {TEST_VECTORS_FILE}: {e}")
        setattr(TestUsptoPatentsQueryGenerator, "test_generation_error", test_generation_error)

else:
    def test_json_file_missing(self):
        self.fail(f"Test vectors file not found: {TEST_VECTORS_FILE}. No tests were generated from it.")
    setattr(TestUsptoPatentsQueryGenerator, "test_json_file_missing", test_json_file_missing)


if __name__ == '__main__':
    unittest.main(verbosity=2)