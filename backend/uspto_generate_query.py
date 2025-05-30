# uspto_generate_query.py
import urllib.parse
import re

USPTO_BOOLEAN_OPS_REGEX_PATTERN = re.compile(
    r"\b(AND|OR|ADJ|NEAR|WITH|SAME|XOR)(\d*)\b",
    re.IGNORECASE
)
USPTO_OPERATOR_KEYWORDS = ["AND", "OR", "ADJ", "NEAR", "WITH", "SAME", "XOR"]
# Define STRONG_USPTO_OPERATOR_KEYWORDS globally
STRONG_USPTO_OPERATOR_KEYWORDS = ["ADJ", "NEAR", "WITH", "SAME", "XOR"] 

def _is_structured_operator_query(text_input: str, specific_ops_list=None) -> bool:
    """
    Checks if text_input contains operators.
    If specific_ops_list is provided, checks only for those operators.
    Otherwise, uses the global regex for any USPTO operator.
    """
    if specific_ops_list:
        text_upper = text_input.upper()
        # For specific ops list, we need to be careful to match whole words
        # and op[N] patterns if they are implicitly included in specific_ops_list.
        # This simplified check looks for whole word matches from the list.
        # A more robust version would re-use regex logic for op[N] if needed here.
        words_in_text = text_upper.split()
        for op_keyword in specific_ops_list:
            if op_keyword.upper() in words_in_text: # Check if the exact keyword is a word
                return True
            # Check for opN patterns if the base keyword is in specific_ops_list
            # e.g. if "ADJ" is in specific_ops_list, this will find "ADJ2"
            for word in words_in_text:
                if word.startswith(op_keyword.upper()) and \
                   len(word) > len(op_keyword) and \
                   word[len(op_keyword):].isdigit():
                    return True
        return False
    return bool(USPTO_BOOLEAN_OPS_REGEX_PATTERN.search(text_input))


def _format_uspto_text_condition(text, field_code, multi_word_op="ADJ", is_exact=False):
    current_text = str(text).strip()
    if not current_text: return ""

    words = current_text.split()
    n_words = len(words)
    processed_text = ""

    if is_exact:
        temp_text = current_text.replace('"', '\\"') 
        processed_text = f'"{temp_text}"'
        if processed_text == '""': return "" 
    else: # Not exact
        is_already_fully_parenthesized = current_text.startswith('(') and current_text.endswith(')')
        is_already_quoted = current_text.startswith('"') and current_text.endswith('"')
        
        if is_already_fully_parenthesized or is_already_quoted:
            processed_text = current_text
        else:
            contains_any_operator = _is_structured_operator_query(current_text)

            if contains_any_operator:
                # Operators are detected. Decide whether to preserve or ADJ-join.
                
                # Heuristic for TC59: "NEAR field communication"
                # If the first word is an operator, but the rest of the string isn't structured by operators,
                # then treat the first word as part of the phrase to be ADJ-joined.
                first_word_is_op_keyword = n_words > 0 and words[0].upper() in USPTO_OPERATOR_KEYWORDS
                
                if first_word_is_op_keyword and n_words > 1 and \
                   not _is_structured_operator_query(" ".join(words[1:])):
                    processed_text = f"({(' ' + multi_word_op.upper() + ' ').join(words)})"
                
                # Heuristic for TC61: Long phrase with only incidental AND/OR
                elif not ('(' in current_text or ')' in current_text) and n_words >= 7: # No internal user parentheses
                    ops_found_details = []
                    for match in USPTO_BOOLEAN_OPS_REGEX_PATTERN.finditer(current_text):
                        ops_found_details.append((match.group(1).upper(), match.group(2)))
                    
                    all_ops_are_weak_no_num = False
                    if ops_found_details: # Ensure ops_found_details is not empty before all()
                        all_ops_are_weak_no_num = all(op_detail[0] in ["AND", "OR"] and not op_detail[1] for op_detail in ops_found_details)

                    if all_ops_are_weak_no_num and 1 <= len(ops_found_details) <= 2:
                        processed_text = f"({(' ' + multi_word_op.upper() + ' ').join(words)})"
                    else: # Contains strong ops, or complex weak op structure, or short phrase with ops
                        processed_text = current_text
                else: # Default for structured queries (e.g., "cat OR dog", "(A OR B) AND C")
                      # or shorter phrases with operators that are not the TC59 leading-op case.
                    processed_text = current_text
            
            elif n_words > 1: # Not structured by ops, multi-word -> ADJ-join
                processed_text = f"({(' ' + multi_word_op.upper() + ' ').join(words)})"
            else: # Single word
                processed_text = current_text
        
        if not processed_text: return "" 

    # Field application
    if field_code and str(field_code).upper() != "ALL":
        if not processed_text: return ""
        
        is_self_contained_unit = (processed_text.startswith('(') and processed_text.endswith(')')) or \
                                 (processed_text.startswith('"') and processed_text.endswith('"'))
        
        is_single_alphanum_word_for_text_field = len(processed_text.split()) == 1 and \
                                                 processed_text.isalnum() and \
                                                 str(field_code).upper() != "PN"

        if is_self_contained_unit or is_single_alphanum_word_for_text_field:
            return f"{processed_text}.{str(field_code).lower()}."
        else:
            return f"({processed_text}).{str(field_code).lower()}."
    else: # field is "ALL"
        return processed_text


def _format_uspto_name_condition(name_string, field_code, default_op="ADJ"):
    name_string = str(name_string).strip()
    if not name_string: return ""
        
    words = name_string.split()
    processed_name = ""
    
    has_internal_ops = _is_structured_operator_query(name_string)

    if has_internal_ops: 
        processed_name = name_string 
    elif len(words) > 1:
        processed_name = f"({(' ' + default_op.upper() + ' ').join(words)})" 
    else: 
        processed_name = name_string

    if not processed_name: return ""

    is_self_contained_unit = (processed_name.startswith('(') and processed_name.endswith(')'))
    is_single_alphanum_name = len(processed_name.split()) == 1 and processed_name.isalnum()

    if is_self_contained_unit or is_single_alphanum_name:
        return f"{processed_name}.{str(field_code).lower()}."
    else:
        return f"({processed_name}).{str(field_code).lower()}."


def _format_uspto_classification_condition(value, class_type):
    value = str(value).strip().replace(" ", "") 
    if not value: return ""
    return f"{value}.{str(class_type).lower()}."


def _format_uspto_date_condition(expression, field_code):
    expression = str(expression).strip()
    field_code = str(field_code).strip().upper()
    if not expression or not field_code: return ""
    return f"@{field_code}{expression}"

def _format_uspto_patent_numbers_condition(numbers: list):
    if not numbers: return ""
    processed_numbers = [str(n).strip() for n in numbers if str(n).strip()]
    if not processed_numbers: return ""

    if len(processed_numbers) == 1:
        single_num_str = processed_numbers[0]
        is_already_field_coded = False
        for suffix in [".pn.", ".app.", ".did."]:
            if single_num_str.lower().endswith(suffix):
                is_already_field_coded = True
                break
        if is_already_field_coded: return single_num_str 
        else: return f"({single_num_str}).pn."
    
    needs_or_join = any(
        ("." in pn_str and any(fc_suffix in pn_str.lower() for fc_suffix in [".pn.", ".did.", ".app."])) or \
        _is_structured_operator_query(pn_str) 
        for pn_str in processed_numbers
    )

    if needs_or_join:
        final_parts = []
        for pn_str in processed_numbers:
            is_simple_number_without_field_code_or_ops = not (
                ("." in pn_str and any(fc_suffix in pn_str.lower() for fc_suffix in [".pn.", ".did.", ".app."])) or
                _is_structured_operator_query(pn_str) or
                (pn_str.startswith('(') and pn_str.endswith(')')) 
            )
            if is_simple_number_without_field_code_or_ops:
                final_parts.append(f"({pn_str}).pn.")
            else:
                final_parts.append(pn_str) 
        
        or_joined_parts = []
        for part in final_parts:
            if (part.startswith('(') and part.endswith(')')) or \
               _is_structured_operator_query(part): 
                or_joined_parts.append(part)
            else:
                or_joined_parts.append(f"({part})")
        return " OR ".join(or_joined_parts)
    else: 
        return f"({ '|'.join(processed_numbers) }).pn."


def _process_uspto_condition(condition: dict):
    condition_type = condition.get("type", "").upper()
    data = condition.get("data", {})
    
    if not data:
        if condition_type == "PATENT_NUMBERS" and "numbers" not in data: 
             return _format_uspto_patent_numbers_condition([])
        return "" 

    if condition_type == "TEXT":
        text = data.get("text", "")
        field = data.get("field", "ALL") 
        op = data.get("multi_word_op", "ADJ")
        is_exact = data.get("is_exact", False)
        return _format_uspto_text_condition(text, field, op, is_exact)
    
    elif condition_type == "PATENT_NUMBERS": 
        numbers = data.get("numbers", [])
        return _format_uspto_patent_numbers_condition(numbers)

    elif condition_type == "CLASSIFICATION":
        value = data.get("value", "")
        class_type = data.get("class_type", "") 
        return _format_uspto_classification_condition(value, class_type)

    elif condition_type == "INVENTOR":
        name = data.get("name", "")
        op = data.get("multi_word_op", "ADJ")
        return _format_uspto_name_condition(name, "in", op)

    elif condition_type == "ASSIGNEE":
        name = data.get("name", "")
        op = data.get("multi_word_op", "ADJ")
        return _format_uspto_name_condition(name, "as", op)

    elif condition_type == "DATE":
        expression = data.get("expression", "") 
        field = data.get("field", "") 
        return _format_uspto_date_condition(expression, field)
        
    elif condition_type == "DOCUMENT_ID": 
        doc_id = data.get("doc_id", "") 
        if not doc_id: return ""
        return f"{str(doc_id).strip()}.did."

    return ""


# --- Main Function ---
def generate_uspto_patents_query(
    conditions: list = None,
    databases: list = None,
    combine_conditions_with: str = "AND"
):
    base_url = "https://ppubs.uspto.gov/pubwebapp/external.html"
    query_parts = []
    
    is_solely_patent_numbers_query = False
    if conditions and len(conditions) == 1 and conditions[0].get("type", "").upper() == "PATENT_NUMBERS":
        pn_data = conditions[0].get("data", {})
        if pn_data and pn_data.get("numbers"): 
            temp_part = _format_uspto_patent_numbers_condition(pn_data.get("numbers", []))
            if temp_part: 
                is_solely_patent_numbers_query = True

    if conditions:
        for cond in conditions:
            part = _process_uspto_condition(cond)
            if part: 
                query_parts.append(part)
    
    q_string = ""
    if query_parts:
        if len(query_parts) == 1:
            q_string = query_parts[0]
        else:
            formatted_parts = [f"({p})" for p in query_parts]
            q_string = f" {combine_conditions_with.upper()} ".join(formatted_parts)

    url_params = {}
    if q_string:
        url_params['q'] = q_string
    
    if databases:
        db_str = ",".join(str(db).strip().upper() for db in databases if str(db).strip())
        if db_str:
            url_params['db'] = db_str
            
    if is_solely_patent_numbers_query and q_string: 
        url_params['type'] = "ids"
    elif q_string: 
        url_params['type'] = "queryString"

    final_url = base_url
    if url_params:
        query_string_for_url = urllib.parse.urlencode(url_params, quote_via=urllib.parse.quote)
        if query_string_for_url:
            final_url = f"{base_url}?{query_string_for_url}"
            
    return {
        "query_string_display": q_string,
        "url": final_url
    }