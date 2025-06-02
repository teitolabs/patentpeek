# google_parser.py
from typing import Dict, Any, List, Optional
import pyparsing as pp
import re
from ast_nodes import (
    ASTNode, QueryRootNode, TermNode, BooleanOpNode, ProximityOpNode,
    FieldedSearchNode, DateSearchNode, ClassificationNode
)

# Google Field prefixes for direct mapping
# Maps Google's code to (canonical_name, needs_paren_around_content_in_google_syntax)
GOOGLE_FIELD_CODE_TO_CANONICAL: Dict[str, tuple[str, bool]] = {
    "TI": ("title", True),
    "AB": ("abstract", True),
    "CL": ("claims", True),
    "CPC": ("cpc", False), # CPC:H01L
    "IPC": ("ipc", False), # IPC:G06F
    "assignee": ("assignee_name", True),
    "inventor": ("inventor_name", True),
    "patent_number": ("patent_number", True)
    # 'description' is full-text, not a specific Google field prefix
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
        # Set to True for very detailed parsing trace from pyparsing:
        # self.current_expr_parser.setDebug(True)
        self.grammar = self._define_grammar()

    def _build_ast_from_infix_tokens(self, instring: str, loc: int, tokens: pp.ParseResults):
        # This function is the parse action for infixNotation.
        # 'tokens' is a ParseResults object.
        # For unary ops, tokens might be like: [op, operand_node]
        # For binary ops, tokens might be like: [operand1_node, op, operand2_node, op, operand3_node ...]
        # Crucially, pyparsing often wraps the actual list of tokens in another list/ParseResults,
        # so tokens[0] is often the list we need to work with.

        # print(f"DEBUG _build_ast_from_infix_tokens >>> instring='{instring}', loc={loc}, tokens={tokens!r} (len={len(tokens)})")
        # if len(tokens) > 0:
        #     print(f"DEBUG _build_ast_from_infix_tokens >>> tokens[0]={tokens[0]!r} (type={type(tokens[0])})")


        # Case 1: A single atom was parsed and no operators applied by infixNotation yet.
        # 'tokens' itself contains the single ASTNode.
        if isinstance(tokens[0], ASTNode) and len(tokens) == 1:
            # print(f"DEBUG _build_ast_from_infix_tokens >>> Path 1 - Single ASTNode directly. Returning: {tokens[0]!r}")
            return tokens[0]

        # Case 2: Operators were involved. tokens[0] is the list of [operand, op, operand, ...]
        # This list is what we process left-to-right based on precedence.
        # Or, it could be a single ASTNode wrapped in a list if it came from a parenthesized expression.
        
        # The 'tokens' object from infixNotation is a ParseResults that typically has one element, 
        # which is another ParseResults (list-like) containing the sequence of operands and operators.
        if len(tokens) == 0: # Should not happen
            raise pp.ParseException(instring, loc, "InfixNotation action called with empty tokens list.")

        op_list = tokens[0] # This should be the list [operand, op, operand, ...] or [op, operand]
        
        # print(f"DEBUG _build_ast_from_infix_tokens >>> Path 2 - op_list: {op_list!r} (len={len(op_list)})")

        if not isinstance(op_list, (list, pp.ParseResults)):
            # If op_list is already a single ASTNode, it means it was likely a sole atom.
            # This path might be redundant if Case 1 catches all single atoms correctly.
            if isinstance(op_list, ASTNode):
                # print(f"DEBUG _build_ast_from_infix_tokens >>> Path 2b - op_list is single ASTNode. Returning: {op_list!r}")
                return op_list
            raise pp.ParseException(instring, loc, f"Expected list or ParseResults for op_list, got {type(op_list)}")

        if not op_list:
             raise pp.ParseException(instring, loc, "Empty operation list.")

        # If op_list contains a single item, it should be an ASTNode (e.g. from parentheses)
        if len(op_list) == 1:
            if isinstance(op_list[0], ASTNode):
                # print(f"DEBUG _build_ast_from_infix_tokens >>> Path 2c - Single ASTNode in op_list. Returning: {op_list[0]!r}")
                return op_list[0]
            else:
                raise pp.ParseException(instring, loc, f"Single item in op_list not an ASTNode: {op_list[0]!r}")

        # Handle unary operators (e.g., '-', 'NOT')
        # These come as [op_str, operand_node] in op_list
        if len(op_list) == 2:
            op_str = op_list[0]
            operand = op_list[1]
            if not isinstance(operand, ASTNode):
                raise pp.ParseException(instring, loc, f"Operand for unary op '{op_str}' is not an ASTNode.")
            if op_str == "-":
                return BooleanOpNode("NOT", [operand])
            if isinstance(op_str, str) and op_str.upper() == "NOT":
                return BooleanOpNode("NOT", [operand])
            # If it's not a known unary op, it might be an error or an implicit AND of two terms
            # that somehow got grouped as two items by a higher-level rule.
            # For now, assume valid unary or fall through to binary.
            # However, infixNotation should group binary ops as [LHS, OP, RHS] so len=2 is usually unary.

        # Handle binary operators (or implicit ANDs)
        # op_list is [LHS, op, RHS, op, RHS, ...] or [LHS, RHS, RHS, ...] for implicit
        
        # The first element must be an ASTNode (the leftmost operand)
        current_ast_node = op_list[0]
        if not isinstance(current_ast_node, ASTNode):
            raise pp.ParseException(instring, loc, f"Expression does not start with a valid operand. Got: {current_ast_node!r}")

        i = 1
        while i < len(op_list):
            operator_str = op_list[i] # This is the explicit operator string (e.g., "AND", "OR")
                                     # OR it's the next ASTNode for implicit AND

            if isinstance(operator_str, str): # Explicit operator
                op_upper = operator_str.upper()
                if i + 1 >= len(op_list):
                    raise pp.ParseException(instring, loc, f"Operator '{op_upper}' is missing a right operand.")
                
                right_operand_node = op_list[i+1]
                if not isinstance(right_operand_node, ASTNode):
                    raise pp.ParseException(instring, loc, f"Right operand for '{op_upper}' is not a valid ASTNode. Got: {right_operand_node!r}")

                if op_upper in ["AND", "OR", "XOR"]:
                    current_ast_node = BooleanOpNode(op_upper, [current_ast_node, right_operand_node])
                elif op_upper.startswith(("ADJ", "NEAR", "WITH", "SAME")):
                    m = re.match(r"^(ADJ|NEAR|WITH|SAME)(\d*)$", op_upper, re.I)
                    if not m: raise pp.ParseException(instring, loc, f"Invalid proximity operator format: {op_upper}")
                    op_type, dist_val_str = m.group(1).upper(), m.group(2)
                    distance = int(dist_val_str) if dist_val_str else None
                    current_ast_node = ProximityOpNode(op_type, [current_ast_node, right_operand_node], #type: ignore
                                                       distance=distance, ordered=(op_type == "ADJ"),
                                                       scope_unit={"WITH": "sentence", "SAME": "paragraph"}.get(op_type))
                else:
                    # This should not be reached if grammar ops match these checks
                    raise pp.ParseException(instring, loc, f"Unhandled explicit operator: {op_upper}")
                i += 2 # Consumed operator and right operand
            
            elif isinstance(operator_str, ASTNode): # Implicit AND: operator_str is the right_operand_node
                right_operand_node = operator_str # operator_str is actually the next ASTNode
                current_ast_node = BooleanOpNode("AND", [current_ast_node, right_operand_node])
                i += 1 # Consumed only the right operand (operator was implicit)
            else:
                raise pp.ParseException(instring, loc, f"Unexpected item in operation list: {operator_str!r}")
        
        return current_ast_node


    def _make_fielded_node(self, instring: str, loc: int, tokens: pp.ParseResults):
        # tokens[0] because of pp.Group
        field_data = tokens[0]
        google_field_code = field_data[0].upper()
        # query_content_node is the ASTNode returned by self.current_expr_parser (for parens)
        # or by term_as_phrase_node/classification_code_term (for colon)
        query_content_node = field_data[1]

        canonical_name, _ = GOOGLE_FIELD_CODE_TO_CANONICAL.get(google_field_code, (f"unknown_google_field_{google_field_code}", False))

        if canonical_name in ["cpc", "ipc"] and isinstance(query_content_node, TermNode):
            value = query_content_node.value
            include_children = False
            if value.lower().endswith("/low"):
                value = value[:-4]
                include_children = True
            
            scheme = "CPC" if canonical_name == "cpc" else "IPC"
            # Value stored as is, e.g. G06F3/048 or H01L2100
            # Generator will handle output formatting (e.g. removing slash for H01L2100)
            classification_node = ClassificationNode(scheme, value, include_children=include_children)
            return FieldedSearchNode(canonical_name, classification_node, system_field_code=google_field_code)

        # Ensure query_content_node is an ASTNode
        if not isinstance(query_content_node, ASTNode):
            # This might happen if current_expr_parser didn't reduce to a single ASTNode correctly
            raise pp.ParseException(instring, loc, f"Content for field {google_field_code} is not a valid ASTNode: {query_content_node!r}")

        return FieldedSearchNode(canonical_name, query_content_node, system_field_code=google_field_code)

    def _make_date_node(self, instring: str, loc: int, tokens: pp.ParseResults):
        date_data = tokens[0] # From pp.Group
        keyword = date_data["keyword"].lower()
        google_date_type = date_data["type"].lower()
        date_value = date_data["value"] # YYYYMMDD

        canonical_field_name = GOOGLE_DATE_TYPE_TO_CANONICAL.get(google_date_type)
        if not canonical_field_name:
            # This case should be prevented by the grammar's Regex for date_type_re
            return TermNode(f"ERROR_UNKNOWN_DATE_TYPE_{google_date_type}:{date_value}")

        operator_map = {"after": ">=", "before": "<="}
        operator = operator_map[keyword]
        
        return DateSearchNode(
            field_canonical_name=canonical_field_name, #type: ignore
            operator=operator, #type: ignore
            date_value=date_value,
            system_field_code=google_date_type 
        )

    def _define_grammar(self):
        LPAR = pp.Suppress("(")
        RPAR = pp.Suppress(")")
        QUOTE = pp.Suppress('"')
        COLON = pp.Suppress(":")

        op_and = pp.CaselessKeyword("AND")
        op_or = pp.CaselessKeyword("OR")
        op_not_keyword = pp.CaselessKeyword("NOT")
        op_xor = pp.CaselessKeyword("XOR") 
        op_prox_explicit = pp.Regex(r"(ADJ|NEAR|WITH|SAME)\d*", re.I)

        all_ops_keywords = op_and | op_or | op_not_keyword | op_xor | op_prox_explicit

        quotedStringAtom = QUOTE + pp.Combine(pp.ZeroOrMore(pp.CharsNotIn('"') | (pp.Literal('""').setParseAction(lambda: '"')))) + QUOTE
        term_as_phrase_node = quotedStringAtom.copy().setParseAction(lambda s,l,t: TermNode(t[0], is_phrase=True))
        
        searchTermAtomChars = pp.alphanums + "-_/.?$*:'" 
        searchTermWord = ~all_ops_keywords + pp.Word(searchTermAtomChars)
        term_as_value_node = searchTermWord.copy().setParseAction(lambda s,l,t: TermNode(t[0]))

        google_field_code_keys = "|".join(re.escape(k) for k in GOOGLE_FIELD_CODE_TO_CANONICAL.keys())
        google_field_prefix_re = pp.Regex(f"({google_field_code_keys})", re.I)("field_code")
        
        # This is what goes inside TI=(...) or CL=(...)
        # It should be a full expression, parsed by current_expr_parser
        field_content_in_parens = (LPAR + self.current_expr_parser + RPAR)
        
        # This is what goes after CPC: or assignee:
        # It's typically a single term or a phrase for these Google fields.
        # Using term_as_value_node for CPC/IPC codes that might contain slashes but aren't phrases.
        field_content_for_colon_atom = term_as_phrase_node | term_as_value_node.copy()


        fielded_search_paren_type = pp.Group(
            google_field_prefix_re + field_content_in_parens # field_content_in_parens will produce an ASTNode
        ).setParseAction(self._make_fielded_node)

        fielded_search_colon_type = pp.Group(
            google_field_prefix_re + COLON + field_content_for_colon_atom # field_content_for_colon_atom produces TermNode
        ).setParseAction(self._make_fielded_node)
        
        date_keyword = pp.CaselessKeyword("after") | pp.CaselessKeyword("before")
        date_type_keys = "|".join(re.escape(k) for k in GOOGLE_DATE_TYPE_TO_CANONICAL.keys())
        date_type_re = pp.Regex(f"({date_type_keys})", re.I)
        date_value_re = pp.Regex(r"\d{8}") 

        date_search = pp.Group(
            date_keyword("keyword") + COLON + date_type_re("type") + COLON + date_value_re("value")
        ).setParseAction(self._make_date_node)
        
        # Atom must be defined such that its components return ASTNode derivatives.
        atom = (
            fielded_search_paren_type |  # TI=(...), AB=(...), CL=(...), assignee=(...), inventor=(...), patent_number=(...)
            fielded_search_colon_type |  # CPC:..., IPC:... (assignee:term also allowed but less common than assignee:(...))
            date_search |                # after:..., before:...
            # Parenthesized expression should be an alternative *within* current_expr_parser,
            # not necessarily at the same level as fielded searches if it causes ambiguity.
            # However, infixNotation handles LPAR expr RPAR correctly if 'expr' is current_expr_parser.
            (LPAR + self.current_expr_parser + RPAR) | 
            term_as_phrase_node |        # "quoted phrase"
            term_as_value_node           # simple_term
        )
        
        minus_sign = pp.Literal("-")
        
        self.current_expr_parser <<= pp.infixNotation(atom, [
            (minus_sign, 1, pp.opAssoc.RIGHT, self._build_ast_from_infix_tokens),
            (op_not_keyword, 1, pp.opAssoc.RIGHT, self._build_ast_from_infix_tokens),
            (op_prox_explicit, 2, pp.opAssoc.LEFT, self._build_ast_from_infix_tokens),
            (op_and, 2, pp.opAssoc.LEFT, self._build_ast_from_infix_tokens),
            (op_xor, 2, pp.opAssoc.LEFT, self._build_ast_from_infix_tokens),
            (op_or, 2, pp.opAssoc.LEFT, self._build_ast_from_infix_tokens),
            (pp.Empty(), 2, pp.opAssoc.LEFT, self._build_ast_from_infix_tokens) # Implicit AND
        ])
        
        return self.current_expr_parser

    def parse(self, query_string: str) -> QueryRootNode:
        query_string_stripped = query_string.strip()
        if not query_string_stripped:
            return QueryRootNode(query=TermNode("__EMPTY__"), settings={})

        try:
            # Result of parseString for infixNotation is a ParseResults of length 1,
            # containing the single root ASTNode.
            parsed_results = self.grammar.parseString(query_string_stripped, parseAll=True)
            
            if parsed_results and len(parsed_results) == 1:
                final_ast_node = parsed_results[0]
                if not isinstance(final_ast_node, ASTNode):
                    # This implies an issue in _build_ast_from_infix_tokens or an atom's parse action
                    # if it didn't return a single ASTNode.
                    final_ast_node = TermNode(f"UNEXPECTED_GOOGLE_PARSE_ROOT_NOT_AST_NODE: Type {type(final_ast_node)}, Value {str(final_ast_node)[:100]}")
            else: # Should not happen if parseAll=True and grammar is valid for the input
                 final_ast_node = TermNode(f"UNEXPECTED_GOOGLE_PARSE_STRUCTURE: Results count {len(parsed_results)}")

            return QueryRootNode(query=final_ast_node, settings={})
        except pp.ParseException as pe:
            error_line_str = pp.line(pe.loc, query_string_stripped)
            error_col = pp.col(pe.loc, query_string_stripped)
            safe_msg = str(pe.msg).replace('"', "'").replace("\\", "/")
            safe_line = str(error_line_str).replace('"',"'").replace("\\", "/")
            error_query_node = TermNode(f"PARSE_ERROR: Col {error_col}: {safe_msg}. Near: \"{safe_line}\"")
            return QueryRootNode(query=error_query_node, settings={})
        except Exception as e:
            # import traceback # Uncomment for detailed debugging
            # print(f"UNEXPECTED_GOOGLE_PARSE_ERROR Exception: {type(e).__name__} - {e}")
            # traceback.print_exc()
            return QueryRootNode(query=TermNode(f"UNEXPECTED_GOOGLE_PARSE_ERROR: {type(e).__name__}: {str(e)}"), settings={})