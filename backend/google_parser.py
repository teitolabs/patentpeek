# google_parser.py
from typing import Dict, Any, List, Optional, Callable, Tuple
import re
from ast_nodes import (
    ASTNode, QueryRootNode, TermNode, BooleanOpNode, ProximityOpNode,
    FieldedSearchNode, DateSearchNode, ClassificationNode
)

# Maps Google's code to (canonical_name, needs_paren_around_content_in_google_syntax_by_default)
GOOGLE_FIELD_CODE_TO_CANONICAL: Dict[str, tuple[str, bool]] = {
    "TI": ("title", True), "AB": ("abstract", True), "CL": ("claims", True),
    "CPC": ("cpc", False), "IPC": ("ipc", False), "assignee": ("assignee_name", True),
    "inventor": ("inventor_name", True), "PN": ("patent_number", False),
    "country": ("country_code", False), "lang": ("language", False),
    "status": ("status", False), "type": ("patent_type", False),
    "TAC": ("text_all_core", True),
}
# Create a case-insensitive version of the map for robust lookups.
CASE_INSENSITIVE_FIELD_MAP = {k.lower(): v for k, v in GOOGLE_FIELD_CODE_TO_CANONICAL.items()}


# Google date fields
GOOGLE_DATE_TYPE_TO_CANONICAL: Dict[str, str] = {
    "publication": "publication_date", "filing": "application_date", "priority": "priority_date"
}

# Regex to capture different parts of a query
TOKENIZE_REGEX = re.compile(
    r'''
    (
        \( .*? \) |  # Match content within parentheses non-greedily
        "[^"]+" |  # Match content within double quotes
        \S+  # Match any non-whitespace characters
    )
    ''',
    re.VERBOSE
)
FIELD_REGEX = re.compile(r"^(\w+)([:=])(.+)$", re.IGNORECASE)
DATE_REGEX = re.compile(r"^(after|before):(\w+):(.+)$", re.IGNORECASE)
OPERATOR_REGEX = re.compile(r"^(AND|OR|NOT|XOR|ADJ\d*|NEAR\d*|WITH|SAME)$", re.IGNORECASE)


class GoogleQueryParser:

    def _insert_implicit_ands(self, tokens: List[str]) -> List[str]:
        """Inserts 'AND' operators between adjacent terms that are not operators."""
        if not tokens:
            return []
        
        processed_tokens = [tokens[0]]
        for i in range(1, len(tokens)):
            # If the previous token and current token are not operators, insert AND
            is_prev_op = OPERATOR_REGEX.match(tokens[i-1]) or tokens[i-1] == '('
            is_curr_op = OPERATOR_REGEX.match(tokens[i]) or tokens[i] == ')'
            if not is_prev_op and not is_curr_op:
                processed_tokens.append("AND")
            processed_tokens.append(tokens[i])
        return processed_tokens

    def _parse_expression(self, tokens: List[str]) -> ASTNode:
        """Parses a list of tokens into an AST, handling operators."""
        
        values: List[ASTNode] = []
        ops: List[str] = []
        
        precedence = {"OR": 1, "XOR": 2, "AND": 3, "NEAR": 4, "ADJ": 4, "WITH": 4, "SAME": 4, "NOT": 5}

        def apply_op():
            op = ops.pop().upper()
            
            # Unary operators
            if op == 'NOT':
                right = values.pop()
                values.append(BooleanOpNode("NOT", [right]))
                return

            # Binary operators
            right = values.pop()
            left = values.pop()

            if op.startswith(("ADJ", "NEAR", "WITH", "SAME")):
                 m = re.match(r"^(ADJ|NEAR|WITH|SAME)(\d*)$", op, re.I)
                 op_type, dist_val_str = m.group(1).upper(), m.group(2)
                 distance = int(dist_val_str) if dist_val_str else None
                 values.append(ProximityOpNode(op_type, [left, right], distance=distance)) # type: ignore
            else:
                # Handle repeated ANDs, e.g. a AND b AND c
                if isinstance(left, BooleanOpNode) and left.operator == op:
                    left.operands.append(right)
                    values.append(left)
                else:
                    values.append(BooleanOpNode(op, [left, right])) # type: ignore

        for token in tokens:
            if OPERATOR_REGEX.match(token):
                op_upper = token.upper()
                base_op = re.match(r"^\D+", op_upper).group(0)
                
                while ops and precedence.get(ops[-1].upper(), 0) >= precedence.get(base_op, 0):
                    apply_op()
                ops.append(token)
            else:
                values.append(self._parse_atom(token))

        while ops:
            apply_op()
        
        return values[0] if values else TermNode("__EMPTY__")


    def _parse_atom(self, token: str) -> ASTNode:
        """Parses a single token (which can be a group) into an ASTNode."""
        token = token.strip()

        if token.startswith('(') and token.endswith(')'):
            inner_content = token[1:-1]
            # --- THIS IS THE FIX ---
            # Tokenize the inner content and apply implicit ANDs before parsing
            inner_tokens = TOKENIZE_REGEX.findall(inner_content)
            processed_inner_tokens = self._insert_implicit_ands(inner_tokens)
            return self._parse_expression(processed_inner_tokens)

        if token.startswith('"') and token.endswith('"'):
            return TermNode(token[1:-1], is_phrase=True)
            
        field_match = FIELD_REGEX.match(token)
        if field_match:
            key, _, value = field_match.groups()
            key_lower = key.lower()

            date_match = DATE_REGEX.match(token)
            if date_match:
                op_keyword, date_type, date_val = date_match.groups()
                canonical_field = GOOGLE_DATE_TYPE_TO_CANONICAL.get(date_type.lower())
                if canonical_field:
                     op = ">=" if op_keyword.lower() == "after" else "<="
                     return DateSearchNode(canonical_field, op, date_val) # type: ignore
            
            canonical_name_tuple = CASE_INSENSITIVE_FIELD_MAP.get(key_lower)
            if canonical_name_tuple:
                canonical_name = canonical_name_tuple[0]
                # The value of a field can also be a parenthesized expression
                return FieldedSearchNode(canonical_name, self._parse_atom(value), system_field_code=key.upper())
        
        if token.lower() == "is:litigated":
            return TermNode("is:litigated")

        return TermNode(token)

    def parse(self, query_string: str) -> QueryRootNode:
        query_string = query_string.strip()
        if not query_string:
            return QueryRootNode(query=TermNode("__EMPTY__"))

        try:
            tokens = TOKENIZE_REGEX.findall(query_string)
            if not tokens:
                 return QueryRootNode(query=TermNode("__EMPTY__"))

            # Top-level validation rule
            for token in tokens:
                if not (token.startswith('(') or OPERATOR_REGEX.match(token) or FIELD_REGEX.match(token)):
                     raise ValueError(f"Invalid standalone text: '{token}'")

            # Insert implicit ANDs at the top level
            processed_tokens = self._insert_implicit_ands(tokens)
            
            final_ast = self._parse_expression(processed_tokens)
            return QueryRootNode(query=final_ast)
        
        except Exception as e:
            error_msg = str(e) if isinstance(e, ValueError) else "Invalid Expression"
            return QueryRootNode(query=TermNode(f"PARSE_ERROR: {error_msg}"))