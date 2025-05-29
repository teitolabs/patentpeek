# google_generate_query.py
import urllib.parse
import re

      
def _format_scoped_content(scope_prefix, content):
    # Goal: SCOPE=(value), SCOPE="exact phrase", SCOPE=(A OR B)
    if (content.startswith('"') and content.endswith('"')) or \
       (content.startswith('(') and content.endswith(')')):
        # If content is already fully quoted or fully parenthesized (like an OR group)
        return f"{scope_prefix}={content}" 
    else: # Simple term
        return f"{scope_prefix}=({content})"

def _process_structured_condition_to_string(condition_payload):
    condition_type = condition_payload.get('type')
    condition_data = condition_payload.get('data', {})

    if not condition_data:
        return ""

    if condition_type == 'TEXT':
        text_value = condition_data.get('text')
        text = text_value.strip() if isinstance(text_value, str) else ""
        
        if not text: return ""
        
        raw_terms_from_text = [t for t in text.split() if t]
        if not raw_terms_from_text: return ""

        selected_scopes_input = condition_data.get('selectedScopes', ['FT'])
        raw_scopes = list(selected_scopes_input) if isinstance(selected_scopes_input, (list, set)) else ['FT']
        selected_scopes = [s.upper() for s in raw_scopes if isinstance(s, str) and s.strip()]
        if not selected_scopes:
            selected_scopes = ['FT']
        
        term_operator = condition_data.get('termOperator', 'ALL')
        
        content_terms = []
        if term_operator == 'EXACT':
            content_terms = [text] if text else []
        elif term_operator == 'NONE':
            content_terms = raw_terms_from_text
        else: 
            filtered_terms = [t for t in raw_terms_from_text if t.upper() not in ['OR', 'AND', 'NOT']]
            if not filtered_terms and raw_terms_from_text and term_operator == 'ALL':
                content_terms = [text] 
            else:
                content_terms = filtered_terms
        
        if not content_terms: return ""

        processed_terms_content = ""
        if term_operator == 'EXACT':
            processed_terms_content = f'"{text}"'
        elif term_operator == 'ANY':
            temp_join = " OR ".join(content_terms)
            if len(content_terms) > 1: 
                processed_terms_content = f"({temp_join})"
            else:
                processed_terms_content = temp_join
        elif term_operator == 'NONE':
            processed_terms_content = " ".join([f'-"{t}"' if " " in t else f'-{t}' for t in content_terms])
        else: # ALL (default)
            if len(content_terms) == 1 and (" " in content_terms[0] or (content_terms[0].upper() in ['OR', 'AND', 'NOT'])) :
                 processed_terms_content = f'"{content_terms[0]}"'
            else:
                 processed_terms_content = " ".join(content_terms)


        if not processed_terms_content:
            return ""

        ordered_non_ft_scopes = [s for s in selected_scopes if s != 'FT']

        if 'FT' in selected_scopes or not ordered_non_ft_scopes:
            return processed_terms_content
        else:
            is_ti_present = 'TI' in ordered_non_ft_scopes
            is_ab_present = 'AB' in ordered_non_ft_scopes
            is_cl_present = 'CL' in ordered_non_ft_scopes

            if is_ti_present and is_ab_present and is_cl_present and len(ordered_non_ft_scopes) == 3:
                return _format_scoped_content("TAC", processed_terms_content)
            
            tac_like_parts = []
            cpc_any_multi_code_parts = []
            general_cpc_part = [] 

            is_cpc_present = 'CPC' in ordered_non_ft_scopes
            special_cpc_any_handling = is_cpc_present and \
                                       term_operator == 'ANY' and \
                                       len(content_terms) > 1 and \
                                       all(not (" " in term) for term in content_terms) 

            for scope in ordered_non_ft_scopes:
                if scope == 'CPC' and special_cpc_any_handling:
                    for cpc_code_item in content_terms:
                        cpc_any_multi_code_parts.append(f"CPC=({cpc_code_item})")
                elif scope in ['TI', 'AB', 'CL']:
                    tac_like_parts.append(_format_scoped_content(scope, processed_terms_content))
                elif scope == 'CPC': 
                    general_cpc_part.append(_format_scoped_content(scope, processed_terms_content))
            
            all_query_segments = []
            if tac_like_parts:
                all_query_segments.append(f"({ ' OR '.join(tac_like_parts) })" if len(tac_like_parts) > 1 else tac_like_parts[0])
            
            if general_cpc_part:
                 all_query_segments.extend(general_cpc_part)

            if cpc_any_multi_code_parts:
                cpc_group_str = f"({ ' OR '.join(cpc_any_multi_code_parts) })" if len(cpc_any_multi_code_parts) > 1 else cpc_any_multi_code_parts[0]
                all_query_segments.append(cpc_group_str)

            if not all_query_segments: return processed_terms_content 

            final_scoped_expr = " OR ".join(all_query_segments)
            
            if len(all_query_segments) > 1 :
                return f"({final_scoped_expr})"
            return final_scoped_expr


    elif condition_type == 'CLASSIFICATION':
        cpc_code_value = condition_data.get('cpc')
        cpc_code = cpc_code_value.strip() if isinstance(cpc_code_value, str) else ""
        if cpc_code: return f"cpc:{cpc_code.replace('/', '')}"
        return ""

    elif condition_type == 'CHEMISTRY':
        term_value = condition_data.get('term')
        term = term_value.strip() if isinstance(term_value, str) else ""
        operator = condition_data.get('operator', 'EXACT') 
        doc_scope = condition_data.get('docScope', 'FULL') 

        if not term: return ""

        query_part = ""
        if operator == 'SIMILAR':
            query_part = f"~({term})"
        elif operator == 'SUBSTRUCTURE':
            query_part = f"SSS=({term})"
        elif operator == 'SMARTS':
            query_part = f"SMARTS=({term})"
        else: # EXACT (covers 'Exact' and 'Exact Batch' from UI)
            query_part = f'"{term}"' if " " in term else term
        
        if operator in ['SUBSTRUCTURE', 'SMARTS']:
            return query_part

        if doc_scope == 'CLAIMS_ONLY':
            return _format_scoped_content("CL", query_part)
        
        return query_part

    elif condition_type == 'MEASURE':
        measure_text_value = condition_data.get('measure_text') 
        measure_text = measure_text_value.strip() if isinstance(measure_text_value, str) else ""
        if not measure_text: return ""
        return _format_scoped_content("MEASURE", measure_text)


    elif condition_type == 'NUMBERS': 
        doc_id_text_value = condition_data.get('doc_id') 
        doc_ids_text = doc_id_text_value.strip() if isinstance(doc_id_text_value, str) else ""
        
        # number_type = condition_data.get('number_type')
        # country_restriction = condition_data.get('country_restriction')
        # preferred_countries_order = condition_data.get('preferred_countries_order')
        # These are placeholders for now and do not affect query generation.

        if not doc_ids_text: return ""
        
        doc_ids_list = [doc_id.strip() for doc_id in doc_ids_text.split('\n') if doc_id.strip()]
        if not doc_ids_list: return ""

        processed_doc_ids = []
        for doc_id_item in doc_ids_list:
            if doc_id_item.lower().startswith("patent/"):
                 processed_doc_ids.append(f"({doc_id_item})") 
            else:
                 processed_doc_ids.append(f"(patent/{doc_id_item})")
        
        if not processed_doc_ids: return ""
        
        if len(processed_doc_ids) == 1:
            return processed_doc_ids[0]
        else:
            return f"({' OR '.join(processed_doc_ids)})"

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
    
    if dedicated_cpc and isinstance(dedicated_cpc, str) and dedicated_cpc.strip():
        all_search_terms_for_q_url.append(f"cpc:{dedicated_cpc.replace('/', '')}")
    if dedicated_title and isinstance(dedicated_title, str) and dedicated_title.strip():
        all_search_terms_for_q_url.append(f"title:(\"{dedicated_title}\")")
    
    # --- MODIFICATION FOR dedicated_document_id ---
    if dedicated_document_id and isinstance(dedicated_document_id, str) and dedicated_document_id.strip():
        # For dedicated_document_id, it's usually treated as a direct search term, often quoted.
        # It should NOT be prefixed with (patent/...) unless it already has it.
        # Google usually auto-detects document numbers when they are simple strings.
        doc_id_val = dedicated_document_id.strip()
        if doc_id_val.lower().startswith("patent/"): # If user explicitly typed patent/
            all_search_terms_for_q_url.append(f"({doc_id_val})")
        elif '"' in doc_id_val or ' ' in doc_id_val or '(' in doc_id_val or ')' in doc_id_val : # If it has special chars or spaces, assume it's already formatted or needs to be as is
             all_search_terms_for_q_url.append(doc_id_val)
        else: # Simple document number, just quote it
            all_search_terms_for_q_url.append(f"\"{doc_id_val}\"")
    # --- END MODIFICATION ---


    if all_search_terms_for_q_url:
        valid_q_terms = [term.strip() for term in all_search_terms_for_q_url if term.strip()]
        if valid_q_terms:
            url_params_dict['q'] = valid_q_terms

        for term_str_entry in all_search_terms_for_q_url: 
            term_str = term_str_entry.strip()
            if not term_str: continue
            
            is_complete_display_unit = \
                bool(re.match(r"^[A-Za-z]+\s*=\s*.*$", term_str)) or \
                (term_str.startswith('"') and term_str.endswith('"')) or \
                (term_str.startswith('(') and term_str.endswith(')') and \
                 (" OR " in term_str or term_str.lower().startswith("(patent/") or term_str.lower().startswith("(application-exact/"))) or \
                bool(re.match(r"^(cpc|title):", term_str, re.IGNORECASE)) or \
                term_str.startswith("~(")

            if is_complete_display_unit:
                display_query_parts_q_terms.append(term_str)
            else: # Simple terms that need display parentheses
                 display_query_parts_q_terms.append(f"({term_str})")
        
    if patent_offices and isinstance(patent_offices, list) and len(patent_offices) > 0:
        valid_po_codes = [po.strip().upper() for po in patent_offices if isinstance(po, str) and po.strip()]
        if valid_po_codes:
            comma_separated_pos = ','.join(valid_po_codes)
            url_params_dict['country'] = comma_separated_pos 
            display_query_parts_fields.append(f"country:{comma_separated_pos}")

    if languages and isinstance(languages, list) and len(languages) > 0:
        valid_lang_codes = [lang.strip().upper() for lang in languages if isinstance(lang, str) and lang.strip()]
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
        if not re.fullmatch(date_validation_regex, after_date_val): raise ValueError(f"Invalid 'after_date' format: '{after_date_val}'. {date_format_error_msg}")
        formatted_date = after_date_val.replace("-", "")
        param_value = f"{after_date_type.lower()}:{formatted_date}"
        url_params_dict['after'] = param_value
        display_query_parts_fields.append(f"after:{param_value}")

    if before_date and before_date_type:
        before_date_val = str(before_date).strip()
        if not re.fullmatch(date_validation_regex, before_date_val): raise ValueError(f"Invalid 'before_date' format: '{before_date_val}'. {date_format_error_msg}")
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
    
    if litigation and isinstance(litigation, str) and litigation.strip():
        litigation_normalized = litigation.strip().upper().replace(" ", "_")
        url_litigation_param = ""
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