# uspto_parser.py
from typing import Dict, Any, Optional
import pyparsing as pp
import re
from ast_nodes import (
    ASTNode, QueryRootNode, TermNode, BooleanOpNode, ProximityOpNode,
    FieldedSearchNode, DateSearchNode, ClassificationNode
)

USPTO_TO_CANONICAL_FIELD: Dict[str, str] = {
    "TTL": "title", "TI": "title", "ABST": "abstract", "AB": "abstract", "ACLM": "claims", "CLM": "claims",
    "CLMS": "claims", "SPEC": "description", "DETD": "description", "IN": "inventor_name", "INV": "inventor_name",
    "AN": "assignee_name", "AS": "assignee_name", "CPC": "cpc", "CPCA": "cpc", "CPCI": "cpc", "IPC": "ipc",
    "CCLS": "us_classification_ccls", "CLAS": "us_classification_text", "PN": "patent_number",
    "APP": "application_number", "DID": "document_id", "PD": "publication_date", "ISD": "issue_date",
    "AD": "application_date", "FD": "application_date", "AY": "application_year", "FY": "application_year",
    "PY": "publication_year",
}

class USPTOQueryParser:
    def __init__(self):
        self.field_mapping = USPTO_TO_CANONICAL_FIELD
        self.current_expr_parser = pp.Forward()
        self.grammar = self._define_grammar()

    def _build_ast_from_infix_tokens(self, instring, loc, tokens):
        current_tokens = tokens[0]
        if isinstance(current_tokens[0], str) and len(current_tokens) == 2: # Unary operator
            op_str, operand_node = current_tokens[0].upper(), current_tokens[1]
            if op_str == "NOT": return BooleanOpNode(op_str, [operand_node])
            raise pp.ParseException(instring, loc, f"Unknown unary op: {op_str}")
        
        node = current_tokens[0]
        idx = 1
        while idx < len(current_tokens):
            op_str_full_token = current_tokens[idx]
            if isinstance(op_str_full_token, pp.ParseResults):
                op_str_full = op_str_full_token[0].upper()
            else:
                op_str_full = op_str_full_token.upper()

            right_operand = current_tokens[idx+1]
            
            if op_str_full in ["AND", "OR", "XOR"]:
                node = BooleanOpNode(op_str_full, [node, right_operand])
            elif op_str_full.startswith(("ADJ", "NEAR", "WITH", "SAME")):
                m = re.match(r"^(ADJ|NEAR|WITH|SAME)(\d*)$", op_str_full, re.I)
                if not m: raise pp.ParseException(instring, loc, f"Invalid prox op format: {op_str_full}")
                op_t, dist_str = m.group(1).upper(), m.group(2)
                dist = int(dist_str) if dist_str else None
                
                node = ProximityOpNode(op_t, [node, right_operand], distance=dist,
                                     ordered=(op_t=="ADJ"), 
                                     scope_unit={"WITH":"sentence","SAME":"paragraph"}.get(op_t))
            else:
                raise pp.ParseException(instring, loc, f"Unknown operator: {op_str_full}")
            idx += 2
        return node

    def _make_fielded_node(self, instring, loc, tokens):
        fc_tok_list = tokens[0]
        field_code_with_slash = fc_tok_list[0]
        field_code = field_code_with_slash.upper().replace("/", "")
        query_node_or_term = fc_tok_list[1]
        
        canonical_name = self.field_mapping.get(field_code, f"unknown_uspto_field_{field_code}")

        if canonical_name == "cpc" and isinstance(query_node_or_term, TermNode):
            cpc_value = query_node_or_term.value
            include_children = False
            if cpc_value.lower().endswith("/low"):
                cpc_value = cpc_value[:-4]
                include_children = True
            return FieldedSearchNode(canonical_name, 
                                     ClassificationNode("CPC", cpc_value, include_children=include_children), 
                                     system_field_code=field_code)
        
        return FieldedSearchNode(canonical_name, query_node_or_term, system_field_code=field_code)

    def _make_date_node(self, instring, loc, tokens):
        full_match_str = tokens[0]
        m = re.match(r"@([A-Za-z]{2,})(=|>=|<=|>|<|<>)([0-9/]{4,10})(?:(<=)([0-9/]{4,10}))?", full_match_str)
        if m:
            field_code_str, op1_str, date_val1_str, op2_literal_str, date_val2_str = m.groups()
            field_code_upper = field_code_str.upper()
            canonical_name = self.field_mapping.get(field_code_upper, f"unknown_uspto_date_field_{field_code_upper}")
            
            date_val1_str_cleaned = date_val1_str.replace("/", "")
            date_val2_str_cleaned = date_val2_str.replace("/", "") if date_val2_str else None

            if op2_literal_str and date_val2_str_cleaned:
                return DateSearchNode(canonical_name, op1_str, date_val1_str_cleaned, 
                                      date_value2=date_val2_str_cleaned, system_field_code=field_code_upper)
            else:
                return DateSearchNode(canonical_name, op1_str, date_val1_str_cleaned, system_field_code=field_code_upper)
        
        return TermNode(full_match_str)


    def _define_grammar(self):
        LPAR,RPAR,QUOTE=map(pp.Suppress,"()\"")
        op_not = pp.CaselessLiteral("NOT"); op_prox = pp.Regex(r"(ADJ|NEAR|WITH|SAME)\d*",re.I)
        op_and = pp.CaselessLiteral("AND"); op_xor = pp.CaselessLiteral("XOR"); op_or = pp.CaselessLiteral("OR")
        
        searchTermAtomChars = pp.alphanums + "-_/.?$*:'" 
        searchTermAtom = pp.Word(searchTermAtomChars)
        quotedStringAtom = QUOTE + pp.Combine(pp.ZeroOrMore(pp.CharsNotIn('"')|(pp.Literal('""').setParseAction(lambda:"\"")))) + QUOTE
        
        term = quotedStringAtom.setParseAction(lambda s,l,t: TermNode(t[0],is_phrase=True)) | \
               searchTermAtom.setParseAction(lambda s,l,t: TermNode(t[0]))
        
        generic_field_prefix_re = r"([a-zA-Z]{2,4})/"
        uspto_field_prefix = pp.Regex(generic_field_prefix_re, re.I)

        field_content = (LPAR + self.current_expr_parser + RPAR) | term.copy()
        fielded_search = pp.Group(uspto_field_prefix + field_content).setParseAction(self._make_fielded_node)
        
        _date_val_str_pattern = r"[0-9/]{4,10}"
        uspto_date_search_regex = rf"@(?:[A-Za-z]{{2,}})(?:=|>=|<=|>|<|<>)(?:{_date_val_str_pattern})(?:<=(?:{_date_val_str_pattern}))?"
        uspto_date_search = pp.Regex(uspto_date_search_regex).setParseAction(self._make_date_node)

        atom = fielded_search | uspto_date_search | (LPAR + self.current_expr_parser + RPAR) | term.copy()
        
        self.current_expr_parser <<= pp.infixNotation(atom, [
            (op_not, 1, pp.opAssoc.RIGHT, self._build_ast_from_infix_tokens),
            (op_prox, 2, pp.opAssoc.LEFT, self._build_ast_from_infix_tokens),
            (op_and, 2, pp.opAssoc.LEFT, self._build_ast_from_infix_tokens),
            (op_xor, 2, pp.opAssoc.LEFT, self._build_ast_from_infix_tokens),
            (op_or, 2, pp.opAssoc.LEFT, self._build_ast_from_infix_tokens)])
        
        set_kw=pp.CaselessLiteral("SET").suppress()
        set_pv=pp.Word(pp.alphanums+"_")
        set_pn=pp.Word(pp.alphas+"_")
        set_assign=pp.Group(set_pn+pp.Literal("=").suppress()+set_pv)
        set_cmd_opt=pp.Optional(set_kw+pp.delimitedList(set_assign,delim=",")).setResultsName("st")
        
        query_expr_sequence = pp.Group(pp.OneOrMore(self.current_expr_parser))
        
        return set_cmd_opt + pp.Optional(query_expr_sequence).setResultsName("qe_list")


    def parse(self, query_string: str) -> QueryRootNode:
        s_dict_local: Dict[str, Any] = {} 
        try:
            query_string_stripped = query_string.strip()
            if not query_string_stripped: return QueryRootNode(query=TermNode("__EMPTY__"))
            
            parsed = self.grammar.parseString(query_string_stripped, parseAll=True)
            
            s_tok_list=parsed.get("st") 
            if s_tok_list:
                if isinstance(s_tok_list, pp.ParseResults) and len(s_tok_list) > 0:
                    if isinstance(s_tok_list[0], pp.ParseResults):
                        for sg_group in s_tok_list:
                            if isinstance(sg_group, pp.ParseResults) and len(sg_group) == 2:
                                 s_dict_local[sg_group[0].lower()] = sg_group[1]
                    elif isinstance(s_tok_list[0], str) and len(s_tok_list) == 2:
                        s_dict_local[s_tok_list[0].lower()] = s_tok_list[1]

            q_ast_list_tok = parsed.get("qe_list"); q_ast: Optional[ASTNode] = None

            if q_ast_list_tok:
                actual_ast_nodes = q_ast_list_tok[0].asList() 

                if len(actual_ast_nodes) > 1:
                    default_op_str = s_dict_local.get("defaultoperator", "AND").upper()
                    if default_op_str not in ["AND", "OR"]: default_op_str = "AND"
                    q_ast = BooleanOpNode(default_op_str, actual_ast_nodes) # type: ignore
                elif len(actual_ast_nodes) == 1: q_ast = actual_ast_nodes[0]
                else: q_ast = TermNode("__EMPTY__")
            else:
                q_ast = TermNode("__EMPTY_AFTER_SET__" if s_dict_local else "__EMPTY__")

            if q_ast is None:
                q_ast = TermNode("__PARSE_FAILURE_UNSPECIFIED__")

            return QueryRootNode(query=q_ast, settings=s_dict_local)
        except pp.ParseException as pe:
            error_query_node = TermNode(f"PARSE_ERROR: {pe.line}(col {pe.column}) msg: {pe.msg}")
            return QueryRootNode(query=error_query_node, settings=s_dict_local) 
        except Exception as e:
            return QueryRootNode(query=TermNode(f"UNEXPECTED_PARSE_ERROR: {str(e)}"), settings=s_dict_local)