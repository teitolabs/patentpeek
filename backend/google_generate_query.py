# google_generate_query_url.py
import urllib.parse
import re

def _process_structured_condition_to_string(condition_payload):
    condition_type = condition_payload.get('type')
    condition_data = condition_payload.get('data', {})

    if condition_type == 'TEXT':
        text = condition_data.get('text', '').strip()
        if not text: return ""
        
        raw_terms_from_text = [t for t in text.split() if t]
        if not raw_terms_from_text: return ""

        selected_scopes_input = condition_data.get('selectedScopes', ['FT'])
        # Ensure selected_scopes is a list
        selected_scopes = list(selected_scopes_input) if isinstance(selected_scopes_input, (list, set)) else ['FT']
        
        term_operator = condition_data.get('termOperator', 'ALL')
        
        content_terms = []
        if term_operator == 'EXACT': 
            content_terms = [text] 
        else:
            if term_operator in ['ANY', 'ALL', 'NONE']: 
                content_terms = [t for t in raw_terms_from_text if t.upper() not in ['OR', 'AND', 'NOT']]
                if not content_terms and raw_terms_from_text: 
                    content_terms = raw_terms_from_text
            else: 
                content_terms = raw_terms_from_text
        
        if not content_terms: return ""

        processed_terms_content = "" 

        if term_operator == 'EXACT':
            processed_terms_content = f'"{text}"' 
        elif term_operator == 'ANY':
            processed_terms_content = " OR ".join([f'"{t}"' if " " in t else t for t in content_terms])
            if len(content_terms) > 1: 
                processed_terms_content = f"({processed_terms_content})"
        elif term_operator == 'NONE':
            processed_terms_content = " ".join([f'-"{t}"' if " " in t else f'-{t}' for t in content_terms])
        else: # ALL (default)
            processed_terms_content = " ".join([f'"{t}"' if " " in t else t for t in content_terms])

        if not processed_terms_content:
            return ""

        if 'FT' in selected_scopes or not selected_scopes: 
            return processed_terms_content 
        else:
            # Use a list derived from selected_scopes to maintain order, filtering FT
            ordered_non_ft_scopes = [s for s in selected_scopes if s != 'FT']

            if not ordered_non_ft_scopes: # Should not happen if FT was not the only scope
                return processed_terms_content

            # Check for TAC: if TI, AB, CL are all present and are the *only* non-FT scopes
            is_ti_present = 'TI' in ordered_non_ft_scopes
            is_ab_present = 'AB' in ordered_non_ft_scopes
            is_cl_present = 'CL' in ordered_non_ft_scopes
            if is_ti_present and is_ab_present and is_cl_present and len(ordered_non_ft_scopes) == 3:
                # This check ensures that ordered_non_ft_scopes *only* contains TI, AB, CL.
                return f"TAC=({processed_terms_content})"
            
            scoped_parts = []
            
            # Iterate through the ordered non-FT scopes as derived from input
            for scope_val in ordered_non_ft_scopes:
                if scope_val == 'CPC' and term_operator == 'ANY' and len(content_terms) > 1:
                    # Special handling for CPC with ANY operator and multiple CPC codes
                    # Each content_term is treated as a separate CPC code
                    for cpc_code_item in content_terms:
                        scoped_parts.append(f"CPC=({cpc_code_item})")
                elif scope_val == 'TI':
                    scoped_parts.append(f"TI=({processed_terms_content})")
                elif scope_val == 'AB':
                    scoped_parts.append(f"AB=({processed_terms_content})")
                elif scope_val == 'CL':
                    scoped_parts.append(f"CL=({processed_terms_content})")
                elif scope_val == 'CPC': # CPC not matching the ANY multi-term case (e.g., ALL operator, or ANY with single term)
                    scoped_parts.append(f"CPC=({processed_terms_content})")
                # Add other specific scope handling here if necessary
            
            if not scoped_parts: 
                return processed_terms_content # Fallback
            
            final_scoped_expr = " OR ".join(scoped_parts)
            
            # Parenthesize if it's an OR expression resulting from multiple scoped_parts
            if len(scoped_parts) > 1: 
                 return f"({final_scoped_expr})"
            return final_scoped_expr # Single scoped part, no outer parentheses needed unless already in part

    elif condition_type == 'CLASSIFICATION':
        cpc_code = condition_data.get('cpc', '').strip()
        if cpc_code: return f"cpc:{cpc_code.replace('/', '')}"
        return ""
    return ""

def generate_google_patents_query(
    structured_search_conditions: list = None,
    inventors: list = None,
    assignees: list = None,
    after_date: str = None,
    after_date_type: str = None,
    before_date: str = None,
    before_date_type: str = None,
    patent_offices: list = None, 
    languages: list = None, 
    status: str = None,
    patent_type: str = None,
    litigation: str = None,
    dedicated_cpc: str = None,
    dedicated_title: str = None,
    dedicated_document_id: str = None
):
    url_params_dict = {}
    display_query_parts_q_terms = []    
    display_query_parts_fields = [] 
    
    all_search_terms_for_q_url = [] 

    if structured_search_conditions and isinstance(structured_search_conditions, list):
        for condition_payload in structured_search_conditions:
            term_string = _process_structured_condition_to_string(condition_payload)
            if term_string:
                all_search_terms_for_q_url.append(term_string)
    
    # Add dedicated fields to the all_search_terms_for_q_url list
    if dedicated_cpc and isinstance(dedicated_cpc, str) and dedicated_cpc.strip():
        all_search_terms_for_q_url.append(f"cpc:{dedicated_cpc.replace('/', '')}")
    if dedicated_title and isinstance(dedicated_title, str) and dedicated_title.strip():
        all_search_terms_for_q_url.append(f"title:(\"{dedicated_title}\")")
    if dedicated_document_id and isinstance(dedicated_document_id, str) and dedicated_document_id.strip():
        all_search_terms_for_q_url.append(f"\"{dedicated_document_id}\"")

    # Process all_search_terms_for_q_url for URL's q parameters and for display_query_parts_q_terms
    if all_search_terms_for_q_url:
        valid_q_terms = [term.strip() for term in all_search_terms_for_q_url if term.strip()]
        if valid_q_terms:
            url_params_dict['q'] = valid_q_terms

        for term_str_entry in all_search_terms_for_q_url: 
            term_str = term_str_entry.strip()
            if not term_str: continue

            is_google_fielded_term = bool(re.match(r"^(TI|AB|CL|CPC|TAC|PN|APN|inventor|assignee|before|after|country|language|status|ptype|litigation|scholar|partner|priorArt|title|abstract|cpc)\s*[:=]\s*\(?.+", term_str, re.IGNORECASE)) or \
                                     bool(re.match(r"^(InChIKey|CAS)\s*[:=].+", term_str, re.IGNORECASE))
            
            is_complex_or_expression_of_fielded_terms = term_str.startswith("(") and term_str.endswith(")") and " OR " in term_str and any(f_p in term_str for f_p in ["TI=","AB=","CL=","CPC=","country:","language:"])

            is_already_parenthesized = term_str.startswith("(") and term_str.endswith(")")
            is_quoted_phrase = term_str.startswith("\"") and term_str.endswith("\"")

            if is_google_fielded_term or is_complex_or_expression_of_fielded_terms or is_quoted_phrase:
                display_query_parts_q_terms.append(term_str)
            elif is_already_parenthesized: 
                display_query_parts_q_terms.append(term_str)
            elif ' ' in term_str or re.search(r'\b(OR|AND|NOT)\b', term_str, re.IGNORECASE):
                display_query_parts_q_terms.append(f"({term_str})")
            else: 
                display_query_parts_q_terms.append(f"({term_str})") 
        
    # --- Process single-value or direct URL parameter fields ---

    # Patent Offices: Use direct 'country' URL param with comma-separated list
    if patent_offices and isinstance(patent_offices, list) and len(patent_offices) > 0:
        valid_po_codes = [po.strip().upper() for po in patent_offices if po.strip()]
        if valid_po_codes:
            comma_separated_pos = ','.join(valid_po_codes)
            url_params_dict['country'] = comma_separated_pos 
            display_query_parts_fields.append(f"country:{comma_separated_pos}")

    # Languages: Use direct 'language' URL param with comma-separated list
    if languages and isinstance(languages, list) and len(languages) > 0:
        valid_lang_codes = [lang.strip().upper() for lang in languages if lang.strip()]
        if valid_lang_codes:
            comma_separated_langs = ','.join(valid_lang_codes)
            url_params_dict['language'] = comma_separated_langs
            display_query_parts_fields.append(f"language:{comma_separated_langs}")

    if inventors and isinstance(inventors, list):
        valid_inventors = [inv.strip() for inv in inventors if isinstance(inv, str) and inv.strip()]
        if valid_inventors:
            url_params_dict['inventor'] = valid_inventors
            for inv in valid_inventors: display_query_parts_fields.append(f"inventor:{inv}")

    if assignees and isinstance(assignees, list):
        valid_assignees = [ag.strip() for ag in assignees if isinstance(ag, str) and ag.strip()]
        if valid_assignees:
            url_params_dict['assignee'] = valid_assignees
            for assignee_name in valid_assignees: display_query_parts_fields.append(f"assignee:{assignee_name}")
    
    date_format_error_msg = "Date must be in YYYY-MM-DD or YYYYMMDD format."
    date_validation_regex = r"^(?:\d{4}\d{2}\d{2}|\d{4}-\d{2}-\d{2})$"
    valid_date_types = ["priority", "filing", "publication"]
    if after_date_type and after_date_type.lower() not in valid_date_types: raise ValueError(f"Invalid 'after_date_type': {after_date_type}. Must be one of {valid_date_types}.")
    if before_date_type and before_date_type.lower() not in valid_date_types: raise ValueError(f"Invalid 'before_date_type': {before_date_type}. Must be one of {valid_date_types}.")
    if after_date and after_date_type:
        after_date_val = str(after_date).strip()
        if not (isinstance(after_date_val, str) and re.fullmatch(date_validation_regex, after_date_val)): raise ValueError(f"Invalid 'after_date' format: '{after_date_val}'. {date_format_error_msg}")
        formatted_date = after_date_val.replace("-", "")
        param_value = f"{after_date_type.lower()}:{formatted_date}"
        url_params_dict['after'] = param_value
        display_query_parts_fields.append(f"after:{param_value}")
    if before_date and before_date_type:
        before_date_val = str(before_date).strip()
        if not (isinstance(before_date_val, str) and re.fullmatch(date_validation_regex, before_date_val)): raise ValueError(f"Invalid 'before_date' format: '{before_date_val}'. {date_format_error_msg}")
        formatted_date = before_date_val.replace("-", "")
        param_value = f"{before_date_type.lower()}:{formatted_date}"
        url_params_dict['before'] = param_value
        display_query_parts_fields.append(f"before:{param_value}")

    if status and isinstance(status, str) and status.strip():
        status_val = status.strip().upper()
        url_params_dict['status'] = status_val
        display_query_parts_fields.append(f"status:{status_val}")
    if patent_type and isinstance(patent_type, str) and patent_type.strip():
        ptype_val = patent_type.strip().upper()
        url_params_dict['ptype'] = ptype_val
        display_query_parts_fields.append(f"type:{ptype_val}")
    
    url_litigation_param = ""
    if litigation and isinstance(litigation, str) and litigation.strip():
        litigation_normalized = litigation.strip().upper().replace(" ", "_")
        if litigation_normalized == "HAS_RELATED_LITIGATION" or litigation_normalized == "YES": url_litigation_param = "YES"
        elif litigation_normalized == "NO_KNOWN_LITIGATION" or litigation_normalized == "NO": url_litigation_param = "NO"
        else: raise ValueError(f"Invalid litigation value: {litigation}.")
        if url_litigation_param:
            url_params_dict['litigation'] = url_litigation_param
            display_query_parts_fields.append(f"litigation:{url_litigation_param}")

    full_display_query_parts = display_query_parts_q_terms + display_query_parts_fields
    display_query_string = " ".join(filter(None,full_display_query_parts))

    base_url = "https://patents.google.com/"
    full_url = base_url
    
    if url_params_dict: 
        query_string_for_url = urllib.parse.urlencode(url_params_dict, doseq=True)
        if query_string_for_url: 
             full_url = f"{base_url}?{query_string_for_url}"

    return {"query_string_display": display_query_string, "url": full_url}