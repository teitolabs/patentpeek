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
# Proximity operators are still special
PROXIMITY_OPERATOR_REGEX = re.compile(r"^(ADJ\d*|NEAR\d*|WITH|SAME)$", re.IGNORECASE)


class GoogleQueryParser:

    def _parse_expression(self, tokens: List[str]) -> ASTNode:
        """
        Parses a list of tokens into an AST.
        This simplified version treats all non-proximity operators as regular terms.
        """
        if not tokens:
            return TermNode("__EMPTY__")

        # Handle proximity operators first
        if len(tokens) == 3 and PROXIMITY_OPERATOR_REGEX.match(tokens[1]):
            op_token = tokens[1]
            m = re.match(r"^(ADJ|NEAR|WITH|SAME)(\d*)$", op_token, re.I)
            op_type, dist_val_str = m.group(1).upper(), m.group(2)
            distance = int(dist_val_str) if dist_val_str else None
            
            left = self._parse_atom(tokens[0])
            right = self._parse_atom(tokens[2])
            return ProximityOpNode(op_type, [left, right], distance=distance) # type: ignore

        # Otherwise, treat all tokens as terms to be AND'ed together
        nodes = [self._parse_atom(t) for t in tokens]
        
        if len(nodes) == 1:
            return nodes[0]
        else:
            return BooleanOpNode("AND", nodes)

    def _parse_atom(self, token: str) -> ASTNode:
        """Parses a single token (which can be a group) into an ASTNode."""
        token = token.strip()

        if token.startswith('(') and token.endswith(')'):
            inner_content = token[1:-1]
            inner_tokens = TOKENIZE_REGEX.findall(inner_content)
            return self._parse_expression(inner_tokens)

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

            final_ast = self._parse_expression(tokens)
            return QueryRootNode(query=final_ast)
        
        except Exception as e:
            return QueryRootNode(query=TermNode(f"PARSE_ERROR: {str(e)}"))