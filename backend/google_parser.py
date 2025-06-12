
# google_parser.py
from typing import Dict, Any, List, Optional
import pyparsing as pp
import re
from ast_nodes import (
    ASTNode, QueryRootNode, TermNode, BooleanOpNode, ProximityOpNode,
    FieldedSearchNode, DateSearchNode, ClassificationNode
)

# Google Field prefixes for direct mapping
# Maps Google's code to (canonical_name, needs_paren_around_content_in_google_syntax_by_default)
GOOGLE_FIELD_CODE_TO_CANONICAL: Dict[str, tuple[str, bool]] = {
    "TI": ("title", True),
    "AB": ("abstract", True),
    "CL": ("claims", True),
    "CPC": ("cpc", False), 
    "IPC": ("ipc", False), 
    "assignee": ("assignee_name", True),
    "inventor": ("inventor_name", True),
    "PN": ("patent_number", False),
    "country": ("country_code", False),
    "lang": ("language", False),
    "status": ("status", False),
    "type": ("patent_type", False),
    "TAC": ("text_all_core", True), # Title, Abstract, Claims
}

# Google date fields (the part after after:/before:)
GOOGLE_DATE_TYPE_TO_CANONICAL: Dict[str, str] = {
    "publication": "publication_date",
    "filing": "application_date",
    "priority": "priority_date"
}


class GoogleQueryParser:
    def __init__(self):
        self.current_expr_parser = pp.Forward()
        self.grammar = self._define_grammar()

    def _build_ast_from_infix_tokens(self, instring: str, loc: int, tokens: pp.ParseResults):
        op_list = tokens[0] 

        if not isinstance(op_list, (list, pp.ParseResults)):
            if isinstance(op_list, ASTNode): return op_list
            raise pp.ParseException(instring, loc, f"Expected list or ParseResults for op_list, got {type(op_list)}")

        if not op_list: raise pp.ParseException(instring, loc, "Empty operation list.")

        if len(op_list) == 1:
            if isinstance(op_list[0], ASTNode): return op_list[0]
            else: raise pp.ParseException(instring, loc, f"Single item in op_list not an ASTNode: {op_list[0]!r}")

        if len(op_list) == 2: # Unary operator like "-" or "NOT"
            op_str = op_list[0]
            operand = op_list[1]
            if not isinstance(operand, ASTNode):
                raise pp.ParseException(instring, loc, f"Operand for unary op '{op_str}' is not an ASTNode.")
            if op_str == "-": return BooleanOpNode("NOT", [operand])
            if isinstance(op_str, str) and op_str.upper() == "NOT": return BooleanOpNode("NOT", [operand])
        
        current_ast_node = op_list[0]
        if not isinstance(current_ast_node, ASTNode):
            raise pp.ParseException(instring, loc, f"Expression does not start with a valid operand. Got: {current_ast_node!r}")

        i = 1
        while i < len(op_list):
            operator_str_or_node = op_list[i] 

            if isinstance(operator_str_or_node, str): # Explicit operator
                op_upper = operator_str_or_node.upper()
                if i + 1 >= len(op_list):
                    raise pp.ParseException(instring, loc, f"Operator '{op_upper}' is missing a right operand.")
                
                right_operand_node = op_list[i+1]
                if not isinstance(right_operand_node, ASTNode):
                    raise pp.ParseException(instring, loc, f"Right operand for '{op_upper}' is not a valid ASTNode. Got: {right_operand_node!r}")

                if op_upper in ["AND", "OR", "XOR"]:
                    current_ast_node = BooleanOpNode(op_upper, [current_ast_node, right_operand_node])
                elif op_upper.startswith(("ADJ", "NEAR", "WITH", "SAME")): # Proximity
                    m = re.match(r"^(ADJ|NEAR|WITH|SAME)(\d*)$", op_upper, re.I)
                    if not m: raise pp.ParseException(instring, loc, f"Invalid proximity operator format: {op_upper}")
                    op_type, dist_val_str = m.group(1).upper(), m.group(2)
                    distance = int(dist_val_str) if dist_val_str else None
                    current_ast_node = ProximityOpNode(op_type, [current_ast_node, right_operand_node], #type: ignore
                                                       distance=distance, ordered=(op_type == "ADJ"),
                                                       scope_unit={"WITH": "sentence", "SAME": "paragraph"}.get(op_type))
                else:
                    raise pp.ParseException(instring, loc, f"Unhandled explicit operator: {op_upper}")
                i += 2 
            
            elif isinstance(operator_str_or_node, ASTNode): # Implicit AND
                right_operand_node = operator_str_or_node
                # --- FIX: Flatten consecutive implicit ANDs for a cleaner AST ---
                if isinstance(current_ast_node, BooleanOpNode) and current_ast_node.operator == "AND":
                    current_ast_node.operands.append(right_operand_node)
                else:
                    current_ast_node = BooleanOpNode("AND", [current_ast_node, right_operand_node])
                i += 1 
            else:
                raise pp.ParseException(instring, loc, f"Unexpected item in operation list: {operator_str_or_node!r}")
        
        return current_ast_node


    def _make_fielded_node(self, instring: str, loc: int, tokens: pp.ParseResults):
        field_data = tokens[0]
        google_field_code = field_data["field_code"].upper()
        query_content_node = field_data["content"]

        canonical_name, _ = GOOGLE_FIELD_CODE_TO_CANONICAL.get(google_field_code, (f"unknown_google_field_{google_field_code}", False))

        if canonical_name in ["cpc", "ipc"] and isinstance(query_content_node, TermNode):
            value = query_content_node.value
            include_children = False
            if value.lower().endswith("/low"):
                value = value[:-4]
                include_children = True
            
            scheme = "CPC" if canonical_name == "cpc" else "IPC"
            classification_node = ClassificationNode(scheme, value, include_children=include_children)
            return FieldedSearchNode(canonical_name, classification_node, system_field_code=google_field_code)

        if not isinstance(query_content_node, ASTNode):
            raise pp.ParseException(instring, loc, f"Content for field {google_field_code} is not a valid ASTNode: {query_content_node!r}")

        return FieldedSearchNode(canonical_name, query_content_node, system_field_code=google_field_code)

    def _make_date_node(self, instring: str, loc: int, tokens: pp.ParseResults):
        date_data = tokens[0] 
        keyword = date_data["keyword"].lower()
        google_date_type = date_data["type"].lower()
        date_value_str = date_data["value"]

        canonical_field_name = GOOGLE_DATE_TYPE_TO_CANONICAL.get(google_date_type)
        if not canonical_field_name:
            return TermNode(f"ERROR_UNKNOWN_DATE_TYPE_{google_date_type}:{date_value_str}")

        operator_map = {"after": ">=", "before": "<="}
        operator = operator_map[keyword]
        
        if len(date_value_str) == 4 and date_value_str.isdigit():
            year = date_value_str
            if operator == ">=":
                 return DateSearchNode(canonical_field_name, ">=", f"{year}0101", system_field_code=google_date_type) #type: ignore
            elif operator == "<=":
                 return DateSearchNode(canonical_field_name, "<=", f"{year}1231", system_field_code=google_date_type) #type: ignore

        elif len(date_value_str) == 6 and date_value_str.isdigit():
            return TermNode(f"ERROR_UNSUPPORTED_DATE_FORMAT_YYYYMM_{google_date_type}:{date_value_str}")

        return DateSearchNode(
            field_canonical_name=canonical_field_name, #type: ignore
            operator=operator, #type: ignore
            date_value=date_value_str,
            system_field_code=google_date_type 
        )

    def _define_grammar(self):
        LPAR, RPAR, QUOTE = map(pp.Suppress, "()\"")
        
        FIELD_OP = pp.Suppress(":") | pp.Suppress("=")
        
        op_not_keyword = pp.CaselessKeyword("NOT")
        op_prox_explicit = pp.Regex(r"(ADJ|NEAR|WITH|SAME)\d*", re.I)

        all_ops_keywords = op_not_keyword | op_prox_explicit

        searchTermAtomChars = pp.alphanums + "-_/.?$*#_+%&=," 
        
        searchTermWord = ~all_ops_keywords + pp.Word(searchTermAtomChars)
        
        term_as_value_node = searchTermWord.copy().set_parse_action(lambda s,l,t: TermNode(t[0]))
        
        quotedStringAtom = pp.QuotedString('"').set_parse_action(lambda t: TermNode(t[0], is_phrase=True))
        
        google_field_code_keys = "|".join(re.escape(k) for k in GOOGLE_FIELD_CODE_TO_CANONICAL.keys())
        
        google_field_prefix_re = pp.Regex(f"({google_field_code_keys})(?=\s*[:=])", re.I)("field_code")
        
        grouped_expr = (LPAR + self.current_expr_parser + RPAR)

        field_content_in_parens = grouped_expr("content")
        field_content_atom = (quotedStringAtom | term_as_value_node.copy())("content")

        fielded_search_paren_type = pp.Group(
            google_field_prefix_re + pp.Suppress("=") + field_content_in_parens
        ).set_parse_action(self._make_fielded_node)

        fielded_search_simple_type = pp.Group(
            google_field_prefix_re + FIELD_OP + field_content_atom
        ).set_parse_action(self._make_fielded_node)
        
        date_keyword = pp.CaselessKeyword("after") | pp.CaselessKeyword("before")
        date_type_keys = "|".join(re.escape(k) for k in GOOGLE_DATE_TYPE_TO_CANONICAL.keys())
        date_type_re = pp.Regex(f"({date_type_keys})", re.I)
        date_value_re = pp.Regex(r"\d{4,8}") 

        date_search = pp.Group(
            date_keyword("keyword") + pp.Suppress(":") + 
            date_type_re("type") + pp.Suppress(":") + 
            date_value_re("value")
        ).set_parse_action(self._make_date_node)
        
        litigated_term = pp.CaselessKeyword("is:litigated").set_parse_action(lambda t: TermNode(t[0]))

        atom = (
            fielded_search_paren_type |
            fielded_search_simple_type |
            date_search |
            litigated_term |
            grouped_expr | 
            quotedStringAtom |
            term_as_value_node
        )
        
        op_neg_prefix = pp.Literal("-")
        
        self.current_expr_parser <<= pp.infix_notation(atom, [
            (op_neg_prefix, 1, pp.OpAssoc.RIGHT, self._build_ast_from_infix_tokens),
            (op_not_keyword, 1, pp.OpAssoc.RIGHT, self._build_ast_from_infix_tokens),
            (op_prox_explicit, 2, pp.OpAssoc.LEFT, self._build_ast_from_infix_tokens),
            (pp.Empty(), 2, pp.OpAssoc.LEFT, self._build_ast_from_infix_tokens), 
        ])
        
        return self.current_expr_parser

    def parse(self, query_string: str) -> QueryRootNode:
        query_string_stripped = query_string.strip()
        if not query_string_stripped:
            return QueryRootNode(query=TermNode("__EMPTY__"))

        try:
            parsed_results = self.grammar.parse_string(query_string_stripped, parse_all=True)
            
            final_ast_node: ASTNode
            if parsed_results and len(parsed_results) == 1 and isinstance(parsed_results[0], ASTNode):
                final_ast_node = parsed_results[0]
            else:
                 final_ast_node = TermNode(f"UNEXPECTED_PARSE_STRUCTURE: {str(parsed_results)[:100]}")
            return QueryRootNode(query=final_ast_node)

        except pp.ParseException as pe:
            safe_msg = str(pe.msg).replace('"', "'")
            safe_line = str(pe.line).replace('"',"'")
            error_query_node = TermNode(f"PARSE_ERROR: {safe_msg} at column {pe.col}. Near: \"{safe_line}\"")
            return QueryRootNode(query=error_query_node)
        except Exception as e:
            return QueryRootNode(query=TermNode(f"UNEXPECTED_PARSE_ERROR: {type(e).__name__}: {str(e)}"))