# google_generate_query.py
import urllib.parse
import re

GOOGLE_OPERATOR_KEYWORDS_REGEX = re.compile(
    r'\b(AND|OR|NOT|NEAR\d*|NEAR/\d+|ADJ\d*|ADJ/\d*|\+/\d*w|/\d*w|WITH|SAME)\b', 
    re.IGNORECASE
)
STANDALONE_BOOL_FILTER_REGEX = re.compile(r'^(AND|OR|NOT)$', re.IGNORECASE)
ONLY_OPERATOR_WORDS_REGEX = re.compile(
    r'^(?:\s*(?:AND|OR|NOT|NEAR\d*|NEAR/\d+|ADJ\d*|ADJ/\d*|\+/\d*w|/\d*w|WITH|SAME)\s*)+$', 
    re.IGNORECASE
)

def _format_scoped_content(scope_prefix, content):
    if not content: return ""
    is_quoted = content.startswith('"') and content.endswith('"')
    is_parenthesized = content.startswith('(') and content.endswith(')')
    
    if is_quoted or is_parenthesized:
        return f"{scope_prefix}={content}"
    else:
        return f"{scope_prefix}=({content})"

def _process_structured_condition_to_string(condition_payload):
    condition_type = condition_payload.get('type')
    condition_data = condition_payload.get('data', {})
    if not condition_data: return ""

    if condition_type == 'TEXT':
        text_value = condition_data.get('text')
        text = text_value.strip() if isinstance(text_value, str) else ""
        if not text: return ""
        
        term_operator = condition_data.get('termOperator', 'ALL')
        user_has_structured_query = bool(GOOGLE_OPERATOR_KEYWORDS_REGEX.search(text))
        
        processed_terms_content = ""

        if term_operator == 'EXACT':
            processed_terms_content = f'"{text}"'
        
        elif term_operator == 'NONE':
            terms_to_negate = re.findall(r'"[^"]*"|\S+', text)
            if not terms_to_negate: return ""
            negated_parts = [f"-{term}" for term in terms_to_negate]
            processed_terms_content = " ".join(negated_parts)
            # Parentheses for display of FT NONE terms are handled by the main function.
            # For scoped NONE, e.g. AB=(-foo -bar), _format_scoped_content will add them.

        elif term_operator == 'ANY':
            if user_has_structured_query and not STANDALONE_BOOL_FILTER_REGEX.fullmatch(text):
                processed_terms_content = text # User typed "A OR B", "A NEAR B", etc.
            else:
                terms = [t for t in text.split() if t]
                if not terms: return ""
                if len(terms) == 1 and STANDALONE_BOOL_FILTER_REGEX.fullmatch(terms[0]): # TC25: "OR" with ANY -> ""
                    return ""
                # For "deep learning" with ANY (TC31), expected is "(deep OR learning)"
                processed_terms_content = f"({ ' OR '.join(terms) })" if len(terms) > 1 else terms[0]
        
        else: # term_operator == 'ALL' (default)
            if ONLY_OPERATOR_WORDS_REGEX.fullmatch(text): # TC44: "NOT AND OR" -> ""NOT AND OR""
                processed_terms_content = f'"{text}"'
            # For "machine AND learning" (TC26), expected is "machine learning" (then parenthesized for display)
            # For "A ADJ B AND C", preserve it.
            elif user_has_structured_query and any(op in text.upper() for op in ["NEAR", "ADJ", "WITH", "SAME", "/"]): # Contains proximity
                processed_terms_content = text
            else: 
                terms_for_all_op = [t for t in text.split() if not STANDALONE_BOOL_FILTER_REGEX.fullmatch(t) and t]
                if not terms_for_all_op and text.split(): return ""
                processed_terms_content = " ".join(terms_for_all_op)
                # Parenthesizing for display of FT ALL terms is handled by the main function.

        if not processed_terms_content: return ""

        selected_scopes_input = condition_data.get('selectedScopes', ['FT'])
        raw_scopes = list(selected_scopes_input) if isinstance(selected_scopes_input, (list, set)) else ['FT']
        selected_scopes = [s.upper() for s in raw_scopes if isinstance(s, str) and s.strip()]
        if not selected_scopes: selected_scopes = ['FT']

        is_ft_scope = 'FT' in selected_scopes or len(selected_scopes) == 0 or all(s == 'FT' for s in selected_scopes)

        if is_ft_scope:
            # If user typed a fully scoped query like "TI=(A) OR AB=(B)", it should be returned as is.
            if any(processed_terms_content.upper().startswith(sc_prefix + "=") for sc_prefix in ["TI", "AB", "CL", "CPC", "TAC", "SSS", "SMARTS", "MEASURE"]):
                 return processed_terms_content
            return processed_terms_content # Raw content for FT, main function handles display parens

        is_ti, is_ab, is_cl, is_cpc = 'TI' in selected_scopes, 'AB' in selected_scopes, 'CL' in selected_scopes, 'CPC' in selected_scopes
        non_ft_scopes = [s for s in selected_scopes if s != 'FT']

        if is_ti and is_ab and is_cl and len(non_ft_scopes) == 3:
            return _format_scoped_content("TAC", processed_terms_content)

        # Special handling for TC28 & TC6 (CPC ANY) and TC45 (mixed scopes ANY)
        if term_operator == 'ANY' and not user_has_structured_query:
            terms_for_any_scoping = [t for t in text.split() if t] # Original terms
            if terms_for_any_scoping:
                or_joined_terms_for_tac = f"({ ' OR '.join(terms_for_any_scoping) })" if len(terms_for_any_scoping) > 1 else terms_for_any_scoping[0]
                
                scoped_parts = []
                tac_parts_for_tc45 = []
                if is_ti: tac_parts_for_tc45.append(_format_scoped_content('TI', or_joined_terms_for_tac))
                if is_ab: tac_parts_for_tc45.append(_format_scoped_content('AB', or_joined_terms_for_tac))
                if is_cl: tac_parts_for_tc45.append(_format_scoped_content('CL', or_joined_terms_for_tac))
                
                if tac_parts_for_tc45:
                    scoped_parts.append(f"({ ' OR '.join(tac_parts_for_tc45) })" if len(tac_parts_for_tc45) > 1 else tac_parts_for_tc45[0])

                if is_cpc:
                    cpc_any_parts = [_format_scoped_content('CPC', term) for term in terms_for_any_scoping]
                    scoped_parts.append(f"({ ' OR '.join(cpc_any_parts) })" if len(cpc_any_parts) > 1 else cpc_any_parts[0])
                
                if scoped_parts:
                    return f"({ ' OR '.join(scoped_parts) })" if len(scoped_parts) > 1 else scoped_parts[0]
        
        # General multi-scope (non-ANY or user_has_structured_query)
        scope_parts_for_or = []
        if is_ti: scope_parts_for_or.append(_format_scoped_content('TI', processed_terms_content))
        if is_ab: scope_parts_for_or.append(_format_scoped_content('AB', processed_terms_content))
        if is_cl: scope_parts_for_or.append(_format_scoped_content('CL', processed_terms_content))
        
        final_query_parts = []
        if scope_parts_for_or:
            final_query_parts.append(f"({ ' OR '.join(scope_parts_for_or) })" if len(scope_parts_for_or) > 1 else scope_parts_for_or[0])
        
        if is_cpc: # For ALL, EXACT, NONE or user-structured ANY
            final_query_parts.append(_format_scoped_content('CPC', processed_terms_content))
            
        if not final_query_parts: return processed_terms_content
        return " ".join(final_query_parts) # ANDed by Google

    elif condition_type == 'CLASSIFICATION':
        cpc_code_value = condition_data.get('cpc')
        cpc_code = cpc_code_value.strip().replace('/', '') if isinstance(cpc_code_value, str) else ""
        if cpc_code: return f"cpc:{cpc_code}"
        return ""

    elif condition_type == 'CHEMISTRY':
        term_value = condition_data.get('term')
        term = term_value.strip() if isinstance(term_value, str) else ""
        operator = condition_data.get('operator', 'EXACT') 
        doc_scope = condition_data.get('docScope', 'FULL') 
        if not term: return ""
        
        query_part = ""
        if operator == 'SIMILAR': # TC87: ~(derivative (Y))
            query_part = f"~({term})" 
        elif operator == 'SUBSTRUCTURE':
            query_part = f"SSS=({term})" 
        elif operator == 'SMARTS':
            query_part = f"SMARTS=({term})"
        else: # EXACT or EXACT_BATCH
            query_part = f'"{term}"' if " " in term or "(" in term else term
        
        if operator in ['SUBSTRUCTURE', 'SMARTS']: return query_part
        if doc_scope == 'CLAIMS_ONLY': return _format_scoped_content("CL", query_part)
        
        # For FT display, single unquoted/unparenthesized chem terms need parens (handled by main func)
        return query_part


    elif condition_type == 'MEASURE': 
        measure_text_value = condition_data.get('measure_text') 
        measure_text = measure_text_value.strip() if isinstance(measure_text_value, str) else ""
        if not measure_text: return ""
        return _format_scoped_content("MEASURE", measure_text)

    elif condition_type == 'NUMBERS': 
        doc_id_text_value = condition_data.get('doc_id') 
        doc_ids_text = doc_id_text_value.strip() if isinstance(doc_id_text_value, str) else ""
        if not doc_ids_text: return ""
        doc_ids_list = [doc_id.strip() for doc_id in doc_ids_text.split('\n') if doc_id.strip()]
        if not doc_ids_list: return ""
        processed_doc_ids = [f"(patent/{item})" if not item.lower().startswith("patent/") else f"({item})" for item in doc_ids_list]
        if not processed_doc_ids: return ""
        if len(processed_doc_ids) == 1: return processed_doc_ids[0]
        return f"({ ' OR '.join(processed_doc_ids) })"

    return ""


def generate_google_patents_query(
    structured_search_conditions: list = None,
    inventors: list = None, assignees: list = None,
    after_date: str = None, after_date_type: str = None,
    before_date: str = None, before_date_type: str = None,
    patent_offices: list = None, languages: list = None, 
    status: str = None, patent_type: str = None, litigation: str = None,
    dedicated_cpc: str = None, dedicated_title: str = None, dedicated_document_id: str = None
):
    q_params_for_url = []
    display_q_terms = []
    field_params_for_display_and_url = {} # For country, lang, inventor etc.

    # Process structured conditions first
    if structured_search_conditions:
        for cond_payload in structured_search_conditions:
            # This is the raw query part for this condition, intended for q-param or scoping
            core_q_part = _process_structured_condition_to_string(cond_payload)
            if not core_q_part: continue
            
            q_params_for_url.append(core_q_part)

            # Determine display formatting
            is_field_scoped = bool(re.match(r"^[A-Za-z]{2,}(?:\[\d*\])?=", core_q_part)) # TI=, AB=, CPC=, SSS= etc.
            is_prefix_scoped = bool(re.match(r"^(cpc|title):", core_q_part, re.IGNORECASE)) # cpc:FOO
            is_quoted = core_q_part.startswith('"') and core_q_part.endswith('"')
            is_fully_parenthesized_group = core_q_part.startswith('(') and core_q_part.endswith(')')
            is_similar_op = core_q_part.startswith("~(")
            
            # A term is "FT-like" if it's not explicitly scoped, quoted, or a complex group.
            # These FT-like terms (single or multi-word) are parenthesized for display.
            # User-entered proximity like "A NEAR B" is NOT FT-like by this rule if it contains operators.
            is_ft_like_needing_display_parens = not (is_field_scoped or is_prefix_scoped or is_quoted or \
                                                     is_fully_parenthesized_group or is_similar_op or \
                                                     GOOGLE_OPERATOR_KEYWORDS_REGEX.search(core_q_part))
            
            if is_ft_like_needing_display_parens:
                display_q_terms.append(f"({core_q_part})")
            # For FT NONE operator, display is (-foo -bar) but q param is -foo -bar
            elif cond_payload.get('type') == 'TEXT' and \
                 cond_payload.get('data', {}).get('termOperator') == 'NONE' and \
                 ('FT' in cond_payload.get('data', {}).get('selectedScopes', ['FT']) or \
                  len(cond_payload.get('data', {}).get('selectedScopes', ['FT'])) == 0 or \
                  all(s == 'FT' for s in cond_payload.get('data', {}).get('selectedScopes', ['FT']))):
                display_q_terms.append(f"({core_q_part})") # core_q_part is "-foo -bar"
            else:
                display_q_terms.append(core_q_part)

    # Dedicated fields are also q-parameters
    if dedicated_cpc and dedicated_cpc.strip():
        term = f"cpc:{dedicated_cpc.replace('/', '').strip()}"
        q_params_for_url.append(term); display_q_terms.append(term)
    if dedicated_title and dedicated_title.strip():
        term = f"title:(\"{dedicated_title.strip()}\")"
        q_params_for_url.append(term); display_q_terms.append(term)
    if dedicated_document_id and dedicated_document_id.strip():
        doc_id_val = dedicated_document_id.strip()
        term = ""
        if doc_id_val.lower().startswith("patent/"): term = f"({doc_id_val})"
        elif '"' in doc_id_val or ' ' in doc_id_val or '(' in doc_id_val or ')' in doc_id_val : term = doc_id_val
        else: term = f"\"{doc_id_val}\""
        q_params_for_url.append(term); display_q_terms.append(term)

    # --- Non-q field parameters ---
    display_field_parts = []
    url_params_dict = {}

    if q_params_for_url:
        url_params_dict['q'] = [q_part for q_part in q_params_for_url if q_part.strip()]
        if not url_params_dict['q']: del url_params_dict['q']


    if patent_offices and any(po.strip() for po in patent_offices):
        val = ','.join(po.strip().upper() for po in patent_offices if po.strip())
        url_params_dict['country'] = val; display_field_parts.append(f"country:{val}")
    if languages and any(lang.strip() for lang in languages):
        val = ','.join(lang.strip().upper() for lang in languages if lang.strip())
        url_params_dict['language'] = val; display_field_parts.append(f"language:{val}")
    if inventors and any(inv.strip() for inv in inventors):
        url_params_dict['inventor'] = [inv.strip() for inv in inventors if inv.strip()]
        for inv in url_params_dict['inventor']: display_field_parts.append(f"inventor:{inv}")
    if assignees and any(asg.strip() for asg in assignees):
        url_params_dict['assignee'] = [asg.strip() for asg in assignees if asg.strip()]
        for asg in url_params_dict['assignee']: display_field_parts.append(f"assignee:{asg}")

    date_validation_regex = r"^(?:\d{4}\d{2}\d{2}|\d{4}-\d{2}-\d{2})$"
    valid_date_types = ["priority", "filing", "publication"]
    if after_date_type and after_date_type.lower() not in valid_date_types: raise ValueError(f"Invalid 'after_date_type'")
    if before_date_type and before_date_type.lower() not in valid_date_types: raise ValueError(f"Invalid 'before_date_type'")
    
    if after_date and after_date_type:
        if not re.fullmatch(date_validation_regex, str(after_date).strip()): raise ValueError(f"Invalid 'after_date' format")
        val = f"{after_date_type.lower()}:{str(after_date).strip().replace('-', '')}"
        url_params_dict['after'] = val; display_field_parts.append(f"after:{val}")
    if before_date and before_date_type:
        if not re.fullmatch(date_validation_regex, str(before_date).strip()): raise ValueError(f"Invalid 'before_date' format")
        val = f"{before_date_type.lower()}:{str(before_date).strip().replace('-', '')}"
        url_params_dict['before'] = val; display_field_parts.append(f"before:{val}")

    if status and status.strip():
        val = status.strip().upper()
        url_params_dict['status'] = val; display_field_parts.append(f"status:{val}")
    if patent_type and patent_type.strip():
        val = patent_type.strip().upper()
        url_params_dict['ptype'] = val; display_field_parts.append(f"type:{val}")
    if litigation and litigation.strip():
        norm_lit = litigation.strip().upper().replace(" ", "_")
        val = "YES" if norm_lit in ["HAS_RELATED_LITIGATION", "YES"] else ("NO" if norm_lit in ["NO_KNOWN_LITIGATION", "NO"] else "")
        if not val: raise ValueError(f"Invalid litigation value: {litigation}")
        url_params_dict['litigation'] = val; display_field_parts.append(f"litigation:{val}")

    display_query_string = " ".join(filter(None, display_q_terms + display_field_parts)).strip()
    
    base_url = "https://patents.google.com/"
    full_url = base_url
    if url_params_dict:
        query_string_for_url = urllib.parse.urlencode(url_params_dict, doseq=True)
        if query_string_for_url: full_url = f"{base_url}?{query_string_for_url}"

    return {"query_string_display": display_query_string, "url": full_url}