# query_converter_testbench.py
import unittest
import json
import os
import re
from query_converter import (
    convert_query
)
# Import ASTNode for from_dict and specific node types if directly checked
from ast_nodes import ASTNode, QueryRootNode, TermNode
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
                if isinstance(actual_output, ASTNode) and hasattr(actual_output, 'value') and \
                   ("PARSE_ERROR" in actual_output.value or "UNEXPECTED_PARSE_ERROR" in actual_output.value):
                    actual_error = actual_output.value
                    actual_output = None

            elif conversion_type == "ast_to_google":
                ast_input_root = ASTNode.from_dict(input_data)
                generator = ASTToGoogleQueryGenerator()
                actual_output = generator.generate(ast_input_root)
            
            elif conversion_type == "google_to_ast": # New type
                parser = GoogleQueryParser()
                ast_root = parser.parse(input_data)
                actual_output = ast_root.query 
                actual_settings = ast_root.settings
                if isinstance(actual_output, TermNode) and \
                   ("__GOOGLE_PARSE_STUB__" in actual_output.value or \
                    "PARSE_ERROR" in actual_output.value):
                    actual_error = actual_output.value
                    actual_output = None
            
            elif conversion_type == "ast_to_uspto": # New type
                ast_input_root = ASTNode.from_dict(input_data)
                generator = ASTToUSPTOQueryGenerator()
                actual_output = generator.generate(ast_input_root)
                if actual_output and "__USPTO_GENERATE_STUB__" in actual_output:
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
            actual_error = str(e)
            # import traceback
            # print(f"Exception during test '{description}': {e}\n{traceback.format_exc()}")


        if expected_error_msg:
            self.assertIsNotNone(actual_error, f"Expected error '{expected_error_msg}' but got no error for: {description}")
            # Allow for more flexible error message checking (e.g., stub messages)
            if "STUB" in expected_error_msg or "STUB" in (actual_error or ""):
                 self.assertIn(expected_error_msg.lower(), (actual_error or "").lower(), f"Error message mismatch for: {description}")
            else:
                 self.assertIn(expected_error_msg.lower(), actual_error.lower(), f"Error message mismatch for: {description}")

        else:
            self.assertIsNone(actual_error, f"Unexpected error '{actual_error}' for: {description}")

            if conversion_type.endswith("_to_ast"):
                if expected_output_data is None and actual_output is None: # For cases where error is expected and output is None
                    pass
                else:
                    expected_ast_node = ASTNode.from_dict(expected_output_data)
                    self.assertEqual(actual_output, expected_ast_node, f"AST mismatch for: {description}\nActual: {actual_output!r}\nExpected: {expected_ast_node!r}")
            else: # String output
                self.assertEqual(actual_output, expected_output_data, f"Output string mismatch for: {description}")

            if expected_settings_data is not None: # Check settings if provided in test case
                 self.assertEqual(actual_settings, expected_settings_data, f"Settings mismatch for: {description}\nActual: {actual_settings}\nExpected: {expected_settings_data}")


    test_method.__doc__ = description
    return test_method

if os.path.exists(TEST_VECTORS_FILE):
    try:
        with open(TEST_VECTORS_FILE, 'r', encoding='utf-8') as f:
            all_test_vectors = json.load(f)

        for i, tc_data in enumerate(all_test_vectors):
            sane_desc = re.sub(r'\W|^(?=\d)', '_', tc_data.get("description", f"TestCase_{i}"))
            method_name = f"test_{sane_desc}"
            
            original_method_name = method_name
            count = 0
            while hasattr(TestQueryConverter, method_name):
                count += 1
                method_name = f"{original_method_name}_{count}"

            test_func = create_test_method(tc_data)
            setattr(TestQueryConverter, method_name, test_func)

    except json.JSONDecodeError as e:
        def test_json_error(self): self.fail(f"Failed to decode {TEST_VECTORS_FILE}: {e}")
        setattr(TestQueryConverter, "test_json_decode_error", test_json_error)
    except Exception as e:
        def test_generation_error(self): self.fail(f"Error generating tests: {e}")
        setattr(TestQueryConverter, "test_generation_error_critical", test_generation_error)
else:
    def test_file_missing(self): self.fail(f"{TEST_VECTORS_FILE} not found.")
    setattr(TestQueryConverter, "test_json_file_missing", test_file_missing)

if __name__ == '__main__':
    unittest.main(verbosity=2)