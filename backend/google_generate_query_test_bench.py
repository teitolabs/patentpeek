# test_query_generator.py
from google_generate_query_url import generate_google_patents_query
import urllib.parse
import json
import os
import argparse
import sys
import re # For splitting display query

def load_test_vectors(file_path):
    try:
        if not os.path.isabs(file_path):
            pass 
        with open(file_path, 'r') as f:
            test_vectors = json.load(f)
        print(f"Successfully loaded test vectors from: {os.path.abspath(file_path)}")
        return test_vectors
    except FileNotFoundError:
        print(f"Error: Test vector file '{os.path.abspath(file_path)}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from '{os.path.abspath(file_path)}': {e}")
        sys.exit(1)

def split_display_query(display_query_str):
    # ... (split_display_query function remains the same) ...
    potential_q_parts = []
    potential_field_specifiers = []
    tokens = display_query_str.split(' ')

    field_prefixes = ["inventor:", "assignee:", "after:", "before:", "country:", 
                      "language:", "status:", "type:", "litigation:"]
    for token in tokens:
        if not token: continue
        is_field_specifier = False
        for prefix in field_prefixes:
            if token.startswith(prefix):
                is_field_specifier = True
                break
        
        if is_field_specifier:
            potential_field_specifiers.append(token)
        else:
            potential_q_parts.append(token)
            
    q_parts_final_string = " ".join(potential_q_parts)
    field_specifiers_final_sorted = sorted(potential_field_specifiers)

    return q_parts_final_string, field_specifiers_final_sorted


def run_tests(test_vectors):
    passed_count = 0
    failed_count = 0
    error_count = 0 # For unexpected errors

    if not test_vectors:
        print("No test vectors provided or loaded. Exiting tests.")
        return

    for i, test_case in enumerate(test_vectors):
        print(f"--- {test_case.get('description', f'Test Case {i+1}')} ---")
        input_params = test_case.get("input", {})
        expected_error_type_str = test_case.get("expected_error") # Get expected error type

        try:
            actual_output = generate_google_patents_query(**input_params)
            
            if expected_error_type_str: # If an error was expected, but none was raised
                print(f"Status: FAILED - Expected error '{expected_error_type_str}' but got normal output.")
                print(f"  Actual Output: {actual_output}")
                failed_count += 1
                continue

            # Normal comparison if no error was expected
            expected_display_str = test_case.get("expected_display_query", "")
            actual_display_str = actual_output["query_string_display"]

            expected_q_display, expected_fields_display_sorted = split_display_query(expected_display_str)
            actual_q_display, actual_fields_display_sorted = split_display_query(actual_display_str)
            
            display_match = (expected_q_display == actual_q_display) and \
                            (expected_fields_display_sorted == actual_fields_display_sorted)
            
            expected_url_str = test_case.get("expected_url", "https://patents.google.com/")
            # ... (rest of the comparison logic is the same)
            actual_url_str = actual_output["url"]
            
            expected_url_parsed = urllib.parse.urlparse(expected_url_str)
            actual_url_parsed = urllib.parse.urlparse(actual_url_str)
            
            url_scheme_match = expected_url_parsed.scheme == actual_url_parsed.scheme
            url_netloc_match = expected_url_parsed.netloc == actual_url_parsed.netloc
            url_path_match = expected_url_parsed.path == actual_url_parsed.path
            
            expected_q_params = urllib.parse.parse_qs(expected_url_parsed.query, keep_blank_values=True)
            actual_q_params = urllib.parse.parse_qs(actual_url_parsed.query, keep_blank_values=True)
            url_query_params_match = expected_q_params == actual_q_params

            url_match = url_scheme_match and url_netloc_match and url_path_match and url_query_params_match


            if display_match and url_match:
                print("Status: PASSED")
                passed_count += 1
            else:
                print("Status: FAILED")
                failed_count += 1
                if not display_match:
                    # ... (mismatch reporting) ...
                    print(f"  Display Query Mismatch:")
                    print(f"    Expected Q Display: '{expected_q_display}'")
                    print(f"    Actual Q Display:   '{actual_q_display}'")
                    print(f"    Expected Fields Display (sorted): {expected_fields_display_sorted}")
                    print(f"    Actual Fields Display (sorted):   {actual_fields_display_sorted}")
                    print(f"    (Full Expected Display: '{expected_display_str}')")
                    print(f"    (Full Actual Display:   '{actual_display_str}')")
                if not url_match:
                    # ... (mismatch reporting) ...
                    print(f"  URL Mismatch:")
                    if not (url_scheme_match and url_netloc_match and url_path_match):
                         print(f"    Base URL part Expected: '{expected_url_parsed.scheme}://{expected_url_parsed.netloc}{expected_url_parsed.path}'")
                         print(f"    Base URL part Actual:   '{actual_url_parsed.scheme}://{actual_url_parsed.netloc}{actual_url_parsed.path}'")
                    if not url_query_params_match:
                        print(f"    URL Query Params Expected: {expected_q_params}")
                        print(f"    URL Query Params Actual:   {actual_q_params}")
                        print(f"    (Full Expected URL: {expected_url_str})")
                        print(f"    (Full Actual URL:   {actual_url_str})")
                        
        except ValueError as ve:
            if expected_error_type_str == "ValueError":
                print(f"Status: PASSED (Correctly raised ValueError: {ve})")
                passed_count += 1
            else:
                print(f"Status: UNEXPECTED ValueError")
                print(f"  Input: {input_params}")
                print(f"  Error: {ve}")
                import traceback
                traceback.print_exc()
                error_count += 1
        except Exception as e:
            if expected_error_type_str and type(e).__name__ == expected_error_type_str:
                 print(f"Status: PASSED (Correctly raised {expected_error_type_str}: {e})")
                 passed_count += 1
            else:
                print(f"Status: UNEXPECTED ERROR")
                print(f"  Input: {input_params}")
                print(f"  Expected error: {expected_error_type_str}, Got: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                error_count += 1
        print("-" * 30)

    # ... (summary and exit logic remain the same) ...
    print("\n--- Test Summary ---")
    print(f"Total Tests Attempted: {len(test_vectors)}")
    print(f"Passed: {passed_count}")
    print(f"Failed (Mismatch/Unexpected Output): {failed_count}")
    print(f"Errors (Execution/Unexpected Exception): {error_count}")
    
    if failed_count > 0 or error_count > 0:
        sys.exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run tests for the Google Patents query generator.")
    parser.add_argument(
        "--test_file",
        default="query_generator_test_vectors.json",
        help="Path to the JSON file containing test vectors. (Default: query_generator_test_vectors.json)"
    )
    args = parser.parse_args()
    test_vectors_list = load_test_vectors(args.test_file)
    if test_vectors_list:
        run_tests(test_vectors_list)