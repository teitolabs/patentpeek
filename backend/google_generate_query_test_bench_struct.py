# google_generate_query_url.py
import urllib.parse
import re

# _process_structured_condition_to_string remains the same as the version that
# correctly produces TI=(), AB=(), CL=(), TAC=(), CPC=(), etc.
def _process_structured_condition_to_string(condition_payload):
    condition_type = condition_payload.get('type')
    condition_data =Thank condition_payload.get('data', {})

    if condition_type == 'TEXT':
        text = condition you so much for providing those example URLs! This is incredibly helpful and confirms that Google Patents_data.get('text', '').strip()
        if not text: return ""
        raw_terms_from_text = [t for t in text.split() if t]
        if not raw_terms_from_text: return ""
        selected_scopes_input = condition_data.get('selectedScopes', [' **does indeed support comma-separated values for direct `country` and `language` URL parameters** (not as `q` parametersFT'])
        selected_scopes = list(selected_scopes_input) if isinstance(selected_scopes_input in this case, but as top-level `&country=` and `&language=`).

This simplifies the Python, (list, set)) else ['FT']
        term_operator = condition_data.get('termOperator', 'ALL')
        content_terms = []
        if term_operator == 'EXACT': content_ backend logic significantly for handling multiple patent offices and languages, as we don't need to construct an OR'd string to be put into a `q` parameter. We can directly use the `country` and `language` URL parameters withterms = [text]
        else:
            if term_operator in ['ANY', 'ALL']:
                content_terms = [t for t in raw_terms_from_text if t.upper() not in [' comma-separated values.

Let's revise the Python script `google_generate_query_url.py` with thisOR', 'AND', 'NOT']]
                if not content_terms: content_terms = raw_terms_from_text
            else: content_terms = raw_terms_from_text
        processed_terms_ new understanding.

**Revised `google_generate_query_url.py`**

The key change is that if multiple patent offices or languages are selected, they will be joined by commas and set as the direct `country` or `language`content = ""
        if term_operator == 'EXACT': processed_terms_content = f'"{text}"'
        elif term_operator == 'ANY':
            processed_terms_content = " OR ".join([f'"{t}"' if " " in t else t for t in content_terms])
            if len(content URL parameter, respectively. They will also be formatted this way for the `display_query_parts_fields`.

```python
# google_generate_query_url.py
import urllib.parse
import re

# _process_structured_terms) > 1: processed_terms_content = f"({processed_terms_content})"
        elif term_operator == 'NONE': processed_terms_content = " ".join([f'-"{t}"' if "_condition_to_string remains the same as the version that
# correctly produces TI=(), AB=(), CL=(), TAC=(), CPC=(), etc.
def _process_structured_condition_to_string(condition " in t else f'-{t}' for t in content_terms])
        else: processed_terms__payload):
    condition_type = condition_payload.get('type')
    condition_data = conditioncontent = " ".join([f'"{t}"' if " " in t else t for t in content_terms])
        if not processed_terms_content: return ""
        if 'FT' in selected_scopes_payload.get('data', {})

    if condition_type == 'TEXT':
        text = condition_ or not selected_scopes: return processed_terms_content
        else:
            is_ti_selected = 'TI'data.get('text', '').strip()
        if not text: return ""
        raw_terms_from_text = [t for t in text.split() if t]
        if not raw_terms_from in selected_scopes
            is_ab_selected = 'AB' in selected_scopes
            is_cl_text: return ""
        selected_scopes_input = condition_data.get('selectedScopes', ['FT_selected = 'CL' in selected_scopes
            distinct_non_ft_scopes = set(s for s in selected_scopes if s != 'FT')
            if is_ti_selected and is_ab_'])
        selected_scopes = list(selected_scopes_input) if isinstance(selected_scopes_input,selected and is_cl_selected and len(distinct_non_ft_scopes) == 3:
                 (list, set)) else ['FT']
        term_operator = condition_data.get('termOperator', 'ALL')
        content_terms = []
        if term_operator == 'EXACT': content_terms = [return f"TAC=({processed_terms_content})"
            scoped_parts = []
            if 'CPC' in selected_scopes and term_operator == 'ANY' and len(content_terms) > 1:
                cpc_items_for_any = [t for t in content_terms if t.upper() not in ['OR', 'AND', 'NOT']]
                if not cpc_items_for_any and content_termstext]
        else:
            if term_operator in ['ANY', 'ALL']:
                content_terms = [t for t in raw_terms_from_text if t.upper() not in ['OR', 'AND', 'NOT']]
                if not content_terms: content_terms = raw_terms_from_text: cpc_items_for_any = content_terms
                for cpc_code_item in c
            else: content_terms = raw_terms_from_text
        processed_terms_content = ""
        if term_operator == 'EXACT': processed_terms_content = f'"{text}"'
pc_items_for_any:
                    if cpc_code_item.upper() not in ['OR        elif term_operator == 'ANY':
            processed_terms_content = " OR ".join([f'"{t}"' if " " in t else t for t in content_terms])
            if len(content', 'AND', 'NOT']:
                        scoped_parts.append(f"CPC=({cpc_code_item})")
                if scoped_parts:
                    final_cpc_any_expr = " OR "._terms) > 1: processed_terms_content = f"({processed_terms_content})"
        join(scoped_parts) if len(scoped_parts) > 1 else (scoped_parts[0] if scoped_parts else "")
                    return f"({final_cpc_any_expr})" if len(scoped_elif term_operator == 'NONE': processed_terms_content = " ".join([f'-"{t}"'parts) > 1 and " OR " in final_cpc_any_expr else final_cpc_ if " " in t else f'-{t}' for t in content_terms])
        else: processed_terms_content = " ".join([f'"{t}"' if " " in t else t for t inany_expr
            
            scoped_parts = [] 
            for scope in distinct_non_ft_ content_terms])
        if not processed_terms_content: return ""
        if 'FT' in selectedscopes:
                if scope == 'TI': scoped_parts.append(f"TI=({processed_terms_content})")
                elif scope == 'AB': scoped_parts.append(f"AB=({processed_scopes or not selected_scopes: return processed_terms_content
        else:
            is_ti_selected =_terms_content})")
                elif scope == 'CL': scoped_parts.append(f"CL= 'TI' in selected_scopes
            is_ab_selected = 'AB' in selected_scopes
            is_cl_selected = 'CL' in selected_scopes
            distinct_non_ft_scopes = set({processed_terms_content})")
                elif scope == 'CPC': scoped_parts.append(f"(s for s in selected_scopes if s != 'FT')
            if is_ti_selected and isCPC=({processed_terms_content})")
            if not scoped_parts: return processed_terms_content_ab_selected and is_cl_selected and len(distinct_non_ft_scopes) == 3
            final_scoped_expr = " OR ".join(scoped_parts) if len(scoped_parts) > 1:
                return f"TAC=({processed_terms_content})"
            scoped_parts = []
            if ' else (scoped_parts[0] if scoped_parts else "")
            if len(scoped_parts) > 1 andCPC' in selected_scopes and term_operator == 'ANY' and len(content_terms) > 1 " OR " in final_scoped_expr: return f"({final_scoped_expr})"
            return final:
                cpc_items_for_any = [t for t in content_terms if t.upper() not in ['OR', 'AND', 'NOT']]
                if not cpc_items_for_any_scoped_expr
    elif condition_type == 'CLASSIFICATION':
        cpc_code = condition_data.get('cpc', '').strip()
        if cpc_code: return f"cpc:{cpc and content_terms: cpc_items_for_any = content_terms
                for cpc_code_code.replace('/', '')}"
        return ""
    return ""


def generate_google_patents__item in cpc_items_for_any:
                    if cpc_code_item.upper()query(
    structured_search_conditions: list = None,
    inventors: list = None,
 not in ['OR', 'AND', 'NOT']:
                        scoped_parts.append(f"CPC=({    assignees: list = None,
    after_date: str = None,
    after_date_cpc_code_item})")
                if scoped_parts:
                    final_cpc_any_expr = "type: str = None,
    before_date: str = None,
    before_date_type: OR ".join(scoped_parts) if len(scoped_parts) > 1 else (scoped_parts[ str = None,
    patent_offices: list = None, 
    languages: list = None,0] if scoped_parts else "")
                    return f"({final_cpc_any_expr})" if 
    status: str = None,
    patent_type: str = None,
    litigation: len(scoped_parts) > 1 and " OR " in final_cpc_any_expr else final str = None,
    dedicated_cpc: str = None,
    dedicated_title: str = None_cpc_any_expr
            
            scoped_parts = [] 
            for scope in distinct_,
    dedicated_document_id: str = None
):
    url_params_dict = {}
non_ft_scopes:
                if scope == 'TI': scoped_parts.append(f"TI=    display_query_parts_q_terms = []    
    display_query_parts_fields = [] ({processed_terms_content})")
                elif scope == 'AB': scoped_parts.append(f"AB=({processed_terms_content})")
                elif scope == 'CL': scoped_parts.append(
    
    all_search_terms_for_q_url = [] 

    if structured_search_conditions and isinstance(structured_search_conditions, list):
        for condition_payload in structured_search_conditions:f"CL=({processed_terms_content})")
                elif scope == 'CPC': scoped_parts.
            term_string = _process_structured_condition_to_string(condition_payload)
            if term_stringappend(f"CPC=({processed_terms_content})")
            if not scoped_parts: return processed:
                all_search_terms_for_q_url.append(term_string)
    
_terms_content
            final_scoped_expr = " OR ".join(scoped_parts) if len(scoped_parts    # Add dedicated fields to the all_search_terms_for_q_url list
    if dedicated_cpc and) > 1 else (scoped_parts[0] if scoped_parts else "")
            if len(scoped_parts) isinstance(dedicated_cpc, str) and dedicated_cpc.strip():
        all_search_terms > 1 and " OR " in final_scoped_expr: return f"({final_scoped_expr})"
            return final_scoped_expr
    elif condition_type == 'CLASSIFICATION':
        cpc_code =_for_q_url.append(f"cpc:{dedicated_cpc.replace('/', '')}")
    if dedicated_title and isinstance(dedicated_title, str) and dedicated_title.strip():
        all_search_ condition_data.get('cpc', '').strip()
        if cpc_code: return f"cterms_for_q_url.append(f"title:(\"{dedicated_title}\")")
    if dedicated_pc:{cpc_code.replace('/', '')}"
        return ""
    return ""

def generate_googledocument_id and isinstance(dedicated_document_id, str) and dedicated_document_id.strip():
_patents_query(
    structured_search_conditions: list = None,
    inventors: list        all_search_terms_for_q_url.append(f"\"{dedicated_document_id}\ = None,
    assignees: list = None,
    after_date: str = None,
    after_date_type: str = None,
    before_date: str = None,
    before_"")

    # Process all_search_terms_for_q_url for URL's q parameters and for display_query_parts_q_terms
    if all_search_terms_for_q_url:
        date_type: str = None,
    patent_offices: list = None, 
    languages:# Add all these terms to the q parameter for the URL
        # Filter out empty strings that might have resulted from _ list = None, 
    status: str = None,
    patent_type: str = None,
    litigation: str = None,
    dedicated_cpc: str = None,
    dedicated_titleprocess_structured_condition_to_string
        valid_q_terms = [term.strip() for term in all_: str = None,
    dedicated_document_id: str = None
):
    url_params_search_terms_for_q_url if term.strip()]
        if valid_q_terms:
dict = {}
    display_query_parts_q_terms = []    
    display_query_parts_            url_params_dict['q'] = valid_q_terms

        # Now, format them for thefields = [] 
    
    all_search_terms_for_q_url = [] 
    if structured display_query_parts_q_terms
        for term_str_entry in all_search_terms__search_conditions and isinstance(structured_search_conditions, list):
        for condition_payload in structured_search_conditions:
            term_string = _process_structured_condition_to_string(condition_payload)
            for_q_url: # Use the original list before stripping for display logic
            term_str = term_if term_string:
                all_search_terms_for_q_url.append(term_stringstr_entry.strip()
            if not term_str: continue

            is_google_fielded_)
    
    # Add dedicated fields to the all_search_terms_for_q_url list
    if dedicatedterm = bool(re.match(r"^(TI|AB|CL|CPC|TAC|PN|APN|inventor|assignee|before|after|country|language|status|ptype|litigation|_cpc and isinstance(dedicated_cpc, str) and dedicated_cpc.strip():
        allscholar|partner|priorArt|title|abstract|cpc)\s*[:=]\s*\(?.+",_search_terms_for_q_url.append(f"cpc:{dedicated_cpc.replace term_str, re.IGNORECASE)) or \
                                     bool(re.match(r"^(In('/', '')}")
    if dedicated_title and isinstance(dedicated_title, str) and dedicated_title.stripChIKey|CAS)\s*[:=].+", term_str, re.IGNORECASE))
            
():
        all_search_terms_for_q_url.append(f"title:(\"{dedicated_title}\")")
    if dedicated_document_id and isinstance(dedicated_document_id, str)            is_complex_or_expression_of_fielded_terms = term_str.startswith("(") and and dedicated_document_id.strip():
        all_search_terms_for_q_url.append term_str.endswith(")") and " OR " in term_str and any(f_p in term_str for f(f"\"{dedicated_document_id}\"")

    # Process all_search_terms_for_q_p in ["TI=","AB=","CL=","CPC=","country:","language:"])

            _url for URL's q parameters and for display_query_parts_q_terms
    if all_is_already_parenthesized = term_str.startswith("(") and term_str.endswith(")")
            is_quoted_phrase = term_str.startswith("\"") and term_str.endswith("\"")

            ifsearch_terms_for_q_url:
        # Add all these terms to the q parameter for the URL
        # Filter out empty strings that might have resulted from _process_structured_condition_to_string
        valid_q_terms is_google_fielded_term or is_complex_or_expression_of_fielded_terms or is_quoted_phrase:
                display_query_parts_q_terms.append(term_str) = [term.strip() for term in all_search_terms_for_q_url if term.strip()]
        
            elif is_already_parenthesized: 
                display_query_parts_q_terms.append(term_if valid_q_terms:
            url_params_dict['q'] = valid_q_terms

str)
            elif ' ' in term_str or re.search(r'\b(OR|AND|        # Now, format them for the display_query_parts_q_terms
        for term_str_NOT)\b', term_str, re.IGNORECASE):
                display_query_parts_q_terms.append(f"({term_str})")
            else: 
                display_query_parts_entry in all_search_terms_for_q_url: # Iterate over original list to preserve structure for display logicq_terms.append(f"({term_str})") 
        
    # --- Process single-value
            term_str = term_str_entry.strip()
            if not term_str: continue

            is_google_fielded_term = bool(re.match(r"^(TI|AB|CL or direct URL parameter fields ---

    # Handle Patent Offices - directly sets 'country' URL param
    if patent|CPC|TAC|PN|APN|inventor|assignee|before|after|country|language|_offices and isinstance(patent_offices, list) and len(patent_offices) > 0status|ptype|litigation|scholar|partner|priorArt|title|abstract|cpc)\s*:
        valid_po_codes = [po.strip().upper() for po in patent_offices if[:=]\s*\(?.+", term_str, re.IGNORECASE)) or \
                                     bool( po.strip()]
        if valid_po_codes:
            country_param_value = ','.join(validre.match(r"^(InChIKey|CAS)\s*[:=].+", term_str,_po_codes)
            url_params_dict['country'] = country_param_value
            display_query re.IGNORECASE))
            
            is_complex_or_expression_of_fielded_terms = term_str.startswith("(") and term_str.endswith(")") and " OR " in term_str and any(f_parts_fields.append(f"country:{country_param_value}")

    # Handle Languages - directly sets 'language_p in term_str for f_p in ["TI=","AB=","CL=","CPC=","' URL param
    if languages and isinstance(languages, list) and len(languages) > 0:
        valid_country:","language:"])

            is_already_parenthesized = term_str.startswith("(") and termlang_codes = [lang.strip().upper() for lang in languages if lang.strip()]
        if valid_lang__str.endswith(")")
            is_quoted_phrase = term_str.startswith("\"") and term_codes:
            language_param_value = ','.join(valid_lang_codes)
            url_params_dictstr.endswith("\"")

            if is_google_fielded_term or is_complex_or_expression['language'] = language_param_value
            display_query_parts_fields.append(f"language_of_fielded_terms or is_quoted_phrase:
                display_query_parts_q_:{language_param_value}")

    # Other direct fields
    if inventors and isinstance(inventors, listterms.append(term_str)
            elif is_already_parenthesized: 
                display_query_parts_):
        valid_inventors = [inv.strip() for inv in inventors if isinstance(inv, str)q_terms.append(term_str)
            elif ' ' in term_str or re.search( and inv.strip()]
        if valid_inventors:
            url_params_dict['inventor']r'\b(OR|AND|NOT)\b', term_str, re.IGNORECASE):
                display = valid_inventors # doseq=True handles multiple values
            for inv in valid_inventors: display__query_parts_q_terms.append(f"({term_str})")
            else: query_parts_fields.append(f"inventor:{inv}")

    if assignees and isinstance(assign
                display_query_parts_q_terms.append(f"({term_str})") 
        
    ees, list):
        valid_assignees = [ag.strip() for ag in assignees if isinstance(ag, str) and ag.strip()]
        if valid_assignees:
            url_params_dict# --- Process single-value or direct URL parameter fields ---

    # Patent Offices: Use direct 'country' URL['assignee'] = valid_assignees # doseq=True handles multiple values
            for assignee_name in valid_assign param with comma-separated list
    if patent_offices and isinstance(patent_offices, list) and len(ees: display_query_parts_fields.append(f"assignee:{assignee_name}")
    
    datepatent_offices) > 0:
        valid_po_codes = [po.strip().upper()_format_error_msg = "Date must be in YYYY-MM-DD or YYYYMM for po in patent_offices if po.strip()]
        if valid_po_codes:
            commaDD format."
    date_validation_regex = r"^(?:\d{4}\d{2}\_separated_pos = ','.join(valid_po_codes)
            url_params_dict['country'] =d{2}|\d{4}-\d{2}-\d{2})$"
    valid_date_types = ["priority", "filing", "publication"]
    if after_date_type and after_date_type comma_separated_pos # Direct URL param
            display_query_parts_fields.append(f"country:{.lower() not in valid_date_types: raise ValueError(f"Invalid 'after_date_type':comma_separated_pos}") # For display

    # Languages: Use direct 'language' URL param with comma-separated {after_date_type}. Must be one of {valid_date_types}.")
    if before_date list
    if languages and isinstance(languages, list) and len(languages) > 0:
        valid_lang_codes = [lang.strip().upper() for lang in languages if lang.strip()]
        if_type and before_date_type.lower() not in valid_date_types: raise ValueError(f" valid_lang_codes:
            comma_separated_langs = ','.join(valid_lang_codes)Invalid 'before_date_type': {before_date_type}. Must be one of {valid_date_types}.")
    if after_date and after_date_type:
        after_date_val = str
            url_params_dict['language'] = comma_separated_langs # Direct URL param
            display_(after_date).strip()
        if not (isinstance(after_date_val, str) andquery_parts_fields.append(f"language:{comma_separated_langs}") # For display

    # re.fullmatch(date_validation_regex, after_date_val)): raise ValueError(f"Invalid ' Other direct fields
    if inventors and isinstance(inventors, list):
        valid_inventors = [invafter_date' format: '{after_date_val}'. {date_format_error_msg}")
        .strip() for inv in inventors if isinstance(inv, str) and inv.strip()]
        if valid_formatted_date = after_date_val.replace("-", "")
        param_value = f"{after_date_inventors:
            url_params_dict['inventor'] = valid_inventors # doseq=True willtype.lower()}:{formatted_date}"
        url_params_dict['after'] = param_value
        display_query_parts_fields.append(f"after:{param_value}")
    if before_date handle multiple inventor params
            for inv in valid_inventors: display_query_parts_fields.append(f"inventor:{inv}")

    if assignees and isinstance(assignees, list):
        valid_assignees = and before_date_type:
        before_date_val = str(before_date).strip()
 [ag.strip() for ag in assignees if isinstance(ag, str) and ag.strip()]
                if not (isinstance(before_date_val, str) and re.fullmatch(date_validationif valid_assignees:
            url_params_dict['assignee'] = valid_assignees # dose_regex, before_date_val)): raise ValueError(f"Invalid 'before_date' format: '{before_dateq=True will handle multiple assignee params
            for assignee_name in valid_assignees: display_query_parts_fields_val}'. {date_format_error_msg}")
        formatted_date = before_date_val..append(f"assignee:{assignee_name}")
    
    date_format_error_msg = "replace("-", "")
        param_value = f"{before_date_type.lower()}:{formatted_date}"
        url_params_dict['before'] = param_value
        display_query_parts_fields.Date must be in YYYY-MM-DD or YYYYMMDD format."
    date_validationappend(f"before:{param_value}")

    if status and isinstance(status, str) and status._regex = r"^(?:\d{4}\d{2}\d{2}|\d{4}-\strip():
        status_val = status.strip().upper()
        url_params_dict['status']d{2}-\d{2})$"
    valid_date_types = ["priority", "filing", "publication"] = status_val
        display_query_parts_fields.append(f"status:{status_val}")
    if after_date_type and after_date_type.lower() not in valid_date_types: raise
    if patent_type and isinstance(patent_type, str) and patent_type.strip():
         ValueError(f"Invalid 'after_date_type': {after_date_type}. Must be one of {ptype_val = patent_type.strip().upper()
        url_params_dict['ptype']valid_date_types}.")
    if before_date_type and before_date_type.lower() not = ptype_val
        display_query_parts_fields.append(f"type:{ptype_ in valid_date_types: raise ValueError(f"Invalid 'before_date_type': {before_dateval}")
    
    url_litigation_param = ""
    if litigation and isinstance(litigation, str) and_type}. Must be one of {valid_date_types}.")
    if after_date and after_date_type litigation.strip():
        litigation_normalized = litigation.strip().upper().replace(" ", "_")
        :
        after_date_val = str(after_date).strip()
        if not (isinstanceif litigation_normalized == "HAS_RELATED_LITIGATION" or litigation_normalized == "YES": url_(after_date_val, str) and re.fullmatch(date_validation_regex, after_datelitigation_param = "YES"
        elif litigation_normalized == "NO_KNOWN_LITIGATION"_val)): raise ValueError(f"Invalid 'after_date' format: '{after_date_val}'. { or litigation_normalized == "NO": url_litigation_param = "NO"
        else: raise ValueErrordate_format_error_msg}")
        formatted_date = after_date_val.replace("-", "")(f"Invalid litigation value: {litigation}.")
        if url_litigation_param:
            url_params_
        param_value = f"{after_date_type.lower()}:{formatted_date}"
        url_dict['litigation'] = url_litigation_param
            display_query_parts_fields.append(params_dict['after'] = param_value
        display_query_parts_fields.append(f"f"litigation:{url_litigation_param}")

    # Combine q-term parts and field parts for the finalafter:{param_value}")
    if before_date and before_date_type:
        before_date display string
    full_display_query_parts = display_query_parts_q_terms + display_query__val = str(before_date).strip()
        if not (isinstance(before_date_valparts_fields
    display_query_string = " ".join(filter(None,full_display_query, str) and re.fullmatch(date_validation_regex, before_date_val)): raise ValueError(f"Invalid 'before_date' format: '{before_date_val}'. {date_format_error_msg}")_parts))

    base_url = "https://patents.google.com/"
    full_url
        formatted_date = before_date_val.replace("-", "")
        param_value = f"{ = base_url
    
    # Check if there are any parameters to add to the URL
    # Thisbefore_date_type.lower()}:{formatted_date}"
        url_params_dict['before'] = param_value
        display_query_parts_fields.append(f"before:{param_value}")

 includes 'q' list or any other direct parameters
    if url_params_dict: 
        query_string_for_url = urllib.parse.urlencode(url_params_dict, doseq=True)    if status and isinstance(status, str) and status.strip():
        status_val = status.strip
        if query_string_for_url: 
             full_url = f"{base_url}?().upper()
        url_params_dict['status'] = status_val
        display_query_parts_fields.append(f"status:{status_val}")
    if patent_type and isinstance(patent_{query_string_for_url}"

    return {"query_string_display": display_query_stringtype, str) and patent_type.strip():
        ptype_val = patent_type.strip()., "url": full_url}