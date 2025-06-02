# query_converter_testbench.py
import unittest
import json
import os
import re
import traceback # Import traceback for detailed error logging

from query_converter import (
    convert_query
)
# Import ASTNode for from_dict and specific node types if directly checked
from ast_nodes import ASTNode, QueryRootNode, TermNode # Add other AST nodes if needed for direct comparison
from uspto_parser import USPTOQueryParser
from google_generator import ASTToGoogleQueryGenerator
from google_parser import GoogleQueryParser
from uspto_generator import ASTToUSPTOQueryGenerator


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_VECTORS_FILE = os.path.join(BASE_DIR, 'query_converter_testvectors.json')

class TestQueryConverter(unittest.TestCase):
    pass # Test methods will be added dynamically

def create_test_method(test_case_data):
    description = test_case_data.get("description", "Unnamed_Conversion_Test")
    conversion_type = test_case_data.get("conversion_type")
    input_data = test_case_data.get("input")
    expected_output_data = test_case_data.get("expected_output")
    expected_settings_data = test_case_data.get("expected_settings")
    expected_error_msg = test_case_data.get("expected_error")

    def test_method(self):
        actual_output = None
        actual_error = None
        actual_settings = None

        try:
            if conversion_type == "uspto_to_ast":
                parser = USPTOQueryParser()
                ast_root = parser.parse(input_data)
                actual_output = ast_root.query
                actual_settings = ast_root.settings
                if isinstance(actual_output, TermNode) and hasattr(actual_output, 'value') and \
                   ("PARSE_ERROR" in actual_output.value or "UNEXPECTED_PARSE_ERROR" in actual_output.value):
                    actual_error = actual_output.value # Capture parse error string from TermNode
                    actual_output = None # Don't compare AST if it's an error node

            elif conversion_type == "ast_to_google":
                if not isinstance(input_data, dict) or 'node_type' not in input_data:
                    self.fail(f"Input data for ast_to_google must be a dict representing an ASTNode. Test: {description}")
                ast_input_root = ASTNode.from_dict(input_data)
                if not isinstance(ast_input_root, QueryRootNode): # Ensure it's a QueryRootNode
                     self.fail(f"AST input for ast_to_google must be a QueryRootNode. Got {type(ast_input_root)}. Test: {description}")
                generator = ASTToGoogleQueryGenerator()
                actual_output = generator.generate(ast_input_root)
                # Check for embedded errors from generator
                if actual_output and ("Error:" in actual_output or "UnhandledASTNode" in actual_output):
                    actual_error = actual_output
                    actual_output = None


            elif conversion_type == "google_to_ast":
                parser = GoogleQueryParser()
                ast_root = parser.parse(input_data) # This is where the original error likely occurs
                actual_output = ast_root.query
                actual_settings = ast_root.settings
                if isinstance(actual_output, TermNode) and \
                   ("__GOOGLE_PARSE_STUB__" in actual_output.value or \
                    "PARSE_ERROR" in actual_output.value or \
                    "UNEXPECTED_GOOGLE_PARSE_ERROR" in actual_output.value): # More specific error check
                    actual_error = actual_output.value
                    actual_output = None

            elif conversion_type == "ast_to_uspto":
                if not isinstance(input_data, dict) or 'node_type' not in input_data:
                    self.fail(f"Input data for ast_to_uspto must be a dict representing an ASTNode. Test: {description}")
                ast_input_root = ASTNode.from_dict(input_data)
                if not isinstance(ast_input_root, QueryRootNode):
                     self.fail(f"AST input for ast_to_uspto must be a QueryRootNode. Got {type(ast_input_root)}. Test: {description}")
                generator = ASTToUSPTOQueryGenerator()
                actual_output = generator.generate(ast_input_root)
                if actual_output and ("__USPTO_GENERATE_STUB__" in actual_output or "ERROR_" in actual_output):
                    actual_error = actual_output
                    actual_output = None

            elif conversion_type == "uspto_to_google":
                result = convert_query(input_data, "uspto", "google")
                actual_output = result["query"]
                actual_error = result["error"]
                actual_settings = result["settings"]

            elif conversion_type == "google_to_uspto":
                result = convert_query(input_data, "google", "uspto")
                actual_output = result["query"]
                actual_error = result["error"]
                actual_settings = result["settings"]

            else:
                self.fail(f"Unknown conversion_type: {conversion_type} in test: {description}")

        except Exception as e:
            # MODIFIED EXCEPTION HANDLING FOR BETTER DEBUGGING
            print(f"\n--- START: FULL TRACEBACK FOR TEST: {description} ---")
            traceback.print_exc() # This prints the full traceback of the original error 'e'
            print(f"--- END: FULL TRACEBACK FOR TEST: {description} ---\n")
            actual_error = str(e) # Store the string representation of the error for assertion


        if expected_error_msg:
            self.assertIsNotNone(actual_error, f"Expected error '{expected_error_msg}' but got no error for: {description}")
            # Allow for more flexible error message checking
            # If expected error is a stub, just check if the actual error contains it.
            # Otherwise, do a more direct comparison or check for keywords.
            if "STUB" in expected_error_msg.upper() or "PARSE_ERROR" in expected_error_msg.upper() or "UNHANDLED" in expected_error_msg.upper() or "ERROR" in expected_error_msg.upper():
                 self.assertIn(expected_error_msg.lower(), (actual_error or "").lower(), f"Error message mismatch for: {description}\nExpected part: {expected_error_msg}\nActual error: {actual_error}")
            else:
                 self.assertEqual(actual_error.lower(), expected_error_msg.lower(), f"Exact error message mismatch for: {description}\nExpected: {expected_error_msg}\nActual: {actual_error}")
        else:
            # MODIFIED ASSERTION MESSAGE FOR UNEXPECTED ERRORS
            self.assertIsNone(actual_error, f"Unexpected error for: {description}. Original error was: '{actual_error}'")

            if conversion_type.endswith("_to_ast"):
                if expected_output_data is None and actual_output is None: # For cases where error is expected and output is None
                    pass # This case is covered by expected_error_msg check
                elif expected_output_data is None:
                     self.assertIsNone(actual_output, f"Expected no AST output but got one for: {description}\nActual: {actual_output!r}")
                elif actual_output is None:
                    self.fail(f"Expected AST output but got None for: {description}\nExpected: {expected_output_data!r}")
                else:
                    try:
                        expected_ast_node = ASTNode.from_dict(expected_output_data)
                        self.assertEqual(actual_output, expected_ast_node, f"AST mismatch for: {description}\nActual:   {actual_output!r}\nExpected: {expected_ast_node!r}")
                    except Exception as e_ast_conv:
                        self.fail(f"Failed to convert expected_output_data to ASTNode for comparison in test '{description}': {e_ast_conv}\nData: {expected_output_data}")

            else: # String output
                self.assertEqual(actual_output, expected_output_data, f"Output string mismatch for: {description}\nActual:   '{actual_output}'\nExpected: '{expected_output_data}'")

            if expected_settings_data is not None: # Check settings if provided in test case
                 self.assertEqual(actual_settings, expected_settings_data, f"Settings mismatch for: {description}\nActual: {actual_settings}\nExpected: {expected_settings_data}")
            elif actual_settings and actual_settings != {}: # If no expected settings, actual should be empty or None
                 self.assertEqual(actual_settings, {}, f"Expected empty settings but got: {actual_settings} for: {description}")


    test_method.__doc__ = description
    return test_method

if os.path.exists(TEST_VECTORS_FILE):
    try:
        with open(TEST_VECTORS_FILE, 'r', encoding='utf-8') as f:
            all_test_vectors = json.load(f)

        for i, tc_data in enumerate(all_test_vectors):
            # Sanitize description for method name
            base_sane_desc = re.sub(r'\W|^(?=\d)', '_', tc_data.get("description", f"TestCase_{i}"))
            # Add conversion type to make method names more unique if descriptions are similar
            conv_type_suffix = re.sub(r'\W', '_', tc_data.get("conversion_type", "unknown_conv"))
            method_name_base = f"test_{base_sane_desc}_{conv_type_suffix}"

            method_name = method_name_base
            count = 0
            # Ensure unique method names if base name is somehow repeated
            while hasattr(TestQueryConverter, method_name):
                count += 1
                method_name = f"{method_name_base}_{count}"

            test_func = create_test_method(tc_data)
            setattr(TestQueryConverter, method_name, test_func)

    except json.JSONDecodeError as e:
        # If JSON is invalid, create a single test that fails with the decode error
        def test_json_error(self):
            self.fail(f"Failed to decode JSON from {TEST_VECTORS_FILE}: {e}")
        setattr(TestQueryConverter, "test_json_decode_error", test_json_error)
    except Exception as e: # Catch other potential errors during test generation
        def test_generation_error(self):
            self.fail(f"An error occurred during test case generation from {TEST_VECTORS_FILE}: {e}")
        setattr(TestQueryConverter, "test_critical_test_generation_error", test_generation_error)
else:
    # If the test vectors file is missing, create a single test that fails
    def test_file_missing(self):
        self.fail(f"Test vectors file not found: {TEST_VECTORS_FILE}. No tests were generated from it.")
    setattr(TestQueryConverter, "test_json_file_missing", test_file_missing)

if __name__ == '__main__':
    unittest.main(verbosity=2)