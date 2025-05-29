# google_generate_query_testbench.py
import unittest
import json
import os
import re # For sanitizing method names

# Attempt to import the function to be tested
try:
    from google_generate_query import generate_google_patents_query
except ImportError:
    raise ImportError("Ensure 'google_generate_query.py' is in the same directory or accessible in PYTHONPATH.")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_VECTORS_FILE = os.path.join(BASE_DIR, 'google_generate_query_testvectors.json')

class TestGooglePatentsQueryGenerator(unittest.TestCase):
    # This class will be populated with test methods dynamically.
    # You can still have setUpClass or tearDownClass if needed.
    pass

def _create_test_method(test_case_data):
    """
    Factory function to create a bound test method for a single test case.
    The returned function will be added to TestGooglePatentsQueryGenerator.
    """
    description = test_case_data.get("description", "Unnamed_Test_Case")
    input_data = test_case_data.get("input")
    expected_error_str = test_case_data.get("expected_error")
    expected_display_query = test_case_data.get("expected_display_query")
    expected_url = test_case_data.get("expected_url")

    # This is the actual function that will be run by unittest for each TC
    def test_method(self): # 'self' will be an instance of TestGooglePatentsQueryGenerator
        if input_data is None:
            self.fail(f"Test case '{description}' is missing 'input' data.")
            return

        # Prepare structured_search_conditions by including all fields from data object
        structured_conditions_input = input_data.get("structured_search_conditions")
        processed_structured_conditions = []
        if structured_conditions_input:
            for cond_input in structured_conditions_input:
                # For NUMBERS tool, ensure all relevant fields are passed through
                # The generate_google_patents_query function expects 'doc_id' for the text
                # and other fields like 'number_type', 'country_restriction', 'preferred_countries_order'
                # directly in the data dict.
                # The frontend sends 'doc_ids_text' which is mapped to 'doc_id' in the python script.
                # So, the test vector should use 'doc_id' for the text of numbers.
                
                # No special processing needed here for NUMBERS tool data fields if the
                # test vector's "data" object for NUMBERS already contains all expected keys
                # like "doc_id", "number_type", "country_restriction", "preferred_countries_order".
                # The test bench just passes the "data" object as is.
                processed_structured_conditions.append(cond_input)


        args_for_function = {
            "structured_search_conditions": processed_structured_conditions if processed_structured_conditions else None,
            "inventors": input_data.get("inventors"),
            "assignees": input_data.get("assignees"),
            "after_date": input_data.get("after_date"),
            "after_date_type": input_data.get("after_date_type"),
            "before_date": input_data.get("before_date"),
            "before_date_type": input_data.get("before_date_type"),
            "status": input_data.get("status"),
            "patent_type": input_data.get("patent_type"),
            "litigation": input_data.get("litigation"),
            "dedicated_cpc": input_data.get("dedicated_cpc"),
            "dedicated_title": input_data.get("dedicated_title"),
            "dedicated_document_id": input_data.get("dedicated_document_id"),
        }

        patent_office_json_val = input_data.get("patent_office") # Legacy single value
        if patent_office_json_val is not None:
            args_for_function["patent_offices"] = [patent_office_json_val] if patent_office_json_val else []
        elif "patent_offices" in input_data: # New list value
            args_for_function["patent_offices"] = input_data.get("patent_offices")

        language_json_val = input_data.get("language") # Legacy single value
        if language_json_val is not None:
            args_for_function["languages"] = [language_json_val] if language_json_val else []
        elif "languages" in input_data: # New list value
            args_for_function["languages"] = input_data.get("languages")
        
        kwargs_to_pass = {k: v for k, v in args_for_function.items() if v is not None}


        if expected_error_str:
            error_map = {"ValueError": ValueError} # Add more error types if needed
            expected_exception = error_map.get(expected_error_str, Exception)
            with self.assertRaises(expected_exception, msg=f"Failed error check for: {description}"):
                generate_google_patents_query(**kwargs_to_pass)
        else:
            if expected_display_query is None or expected_url is None:
                self.fail(f"Test case '{description}' is missing 'expected_display_query' or 'expected_url'.")
                return

            actual_result = generate_google_patents_query(**kwargs_to_pass)

            self.assertEqual(actual_result.get("query_string_display"), expected_display_query,
                             f"Display query mismatch for: {description}\nActual: {actual_result.get('query_string_display')}\nExpected: {expected_display_query}")
            self.assertEqual(actual_result.get("url"), expected_url,
                             f"URL mismatch for: {description}\nActual: {actual_result.get('url')}\nExpected: {expected_url}")

    test_method.__doc__ = description
    return test_method

if os.path.exists(TEST_VECTORS_FILE):
    with open(TEST_VECTORS_FILE, 'r', encoding='utf-8') as f:
        all_test_vectors = json.load(f)

    for i, test_case_from_json in enumerate(all_test_vectors):
        description = test_case_from_json.get("description", f"TestCase_{i+1}")
        sane_description = re.sub(r'\W|^(?=\d)', '_', description) 
        method_name = f"test_{sane_description}_{i}" 

        test_func = _create_test_method(test_case_from_json)
        setattr(TestGooglePatentsQueryGenerator, method_name, test_func)
else:
    def test_json_file_missing(self):
        self.fail(f"Test vectors file not found: {TEST_VECTORS_FILE}. No tests were generated from it.")
    setattr(TestGooglePatentsQueryGenerator, "test_json_file_missing", test_json_file_missing)


if __name__ == '__main__':
    unittest.main(verbosity=2)