
# google_generator.py
from ast_nodes import (
    ASTNode, QueryRootNode, TermNode, BooleanOpNode, ProximityOpNode,
    FieldedSearchNode, DateSearchNode, ClassificationNode
)
from typing import Optional, Dict
import re

GOOGLE_OPERATOR_KEYWORDS_REGEX = re.compile(
    r'^\s*(AND|OR|NOT|NEAR\d*|ADJ\d*|WITH|SAME)\s*$', 
    re.IGNORECASE
)

GOOGLE_OP_PRECEDENCE = {
    "TERM": 100, "DATE_EXPR_ATOM": 100, "FIELD_WRAPPER": 100, "CLASSIFICATION_ATOM": 100,
    "NOT_PREFIX": 90,
    "ADJ": 80, "NEAR": 80, "WITH": 80, "SAME": 80,
    "NOT_OPERAND": 70, 
    "AND": 60,
    "XOR": 50,
    "OR": 40,
    None: 0 
}

CANONICAL_TO_GOOGLE_DATE_TYPE: Dict[str, str] = {
    "publication_date": "publication",
    "application_date": "filing",
    "priority_date": "priority"
}

class ASTToGoogleQueryGenerator:
    def __init__(self):
        pass

    def _format_field_equals_value(self, field_code: str, value_str: str) -> str:
        if not value_str:
            return ""
        is_quoted = value_str.startswith('"') and value_str.endswith('"')
        is_parenthesized = value_str.startswith('(') and value_str.endswith(')')
        if field_code in ["CPC", "IPC", "PN"]:
            if is_quoted or is_parenthesized:
                return f"{field_code}={value_str}"
            elif " " in value_str or GOOGLE_OPERATOR_KEYWORDS_REGEX.search(value_str):
                 return f"{field_code}=({value_str})"
            else:
                return f"{field_code}={value_str}"
        else:
            if is_parenthesized:
                return f"{field_code}={value_str}"
            else:
                return f"{field_code}=({value_str})"

    def generate(self, ast_root: QueryRootNode) -> str:
        if not isinstance(ast_root, QueryRootNode): 
            return "Error: Invalid AST root"
        
        query_part = self._generate_node(ast_root.query, parent_op_type=None)
        
        return query_part.strip()


    def _map_canonical_to_google_field(self, canonical_name: str) -> Optional[str]:
        field_map = {
            "title": "TI", "abstract": "AB", "claims": "CL", "cpc": "CPC",
            "ipc": "IPC", "assignee_name": "assignee", "inventor_name": "inventor",
            "patent_number": "PN", "country_code": "country", "language": "lang",
            "status": "status", "patent_type": "type",
        }
        return field_map.get(canonical_name)

    def _needs_paren_google(self, current_op_type_str: Optional[str], parent_op_type_str: Optional[str]) -> bool:
        if not parent_op_type_str:
            return False
        current_op_base = current_op_type_str.rstrip('0123456789') if current_op_type_str else None
        parent_op_base = parent_op_type_str.rstrip('0123456789') if parent_op_type_str else None
        current_prec = GOOGLE_OP_PRECEDENCE.get(current_op_base, 0)
        parent_prec = GOOGLE_OP_PRECEDENCE.get(parent_op_base, 0)
        
        # Wrap if the inner operator has lower-or-equal precedence
        if current_prec <= parent_prec:
            return True
        return False

    def _generate_node(self, node: ASTNode, parent_op_type: Optional[str] = None) -> str:
        res_str = ""
        current_node_op_type_str = ""

        if isinstance(node, TermNode):
            current_node_op_type_str = "TERM"
            if node.value == "__EMPTY__": return ""
            if node.is_phrase: res_str = f'"{node.value}"'
            elif GOOGLE_OPERATOR_KEYWORDS_REGEX.match(node.value): res_str = f'"{node.value}"'
            else: res_str = node.value
        
        elif isinstance(node, FieldedSearchNode):
            field_google = self._map_canonical_to_google_field(node.field_canonical_name)
            if not field_google:
                return self._generate_node(node.query, parent_op_type)
            query_str = self._generate_node(node.query, field_google)
            if not query_str: return ""
            res_str = self._format_field_equals_value(field_google, query_str)
            current_node_op_type_str = "FIELD_WRAPPER"
        
        elif isinstance(node, BooleanOpNode):
            operator_upper = node.operator.upper()
            current_node_op_type_str = operator_upper
            if operator_upper == "NOT" and len(node.operands) == 1:
                operand_str = self._generate_node(node.operands[0], "NOT_OPERAND")
                if not operand_str: return ""
                res_str = f"NOT {operand_str}"
            else:
                op_strs = [self._generate_node(op, current_node_op_type_str) for op in node.operands]
                op_strs_filtered = [s for s in op_strs if s]
                if not op_strs_filtered: return ""
                if len(op_strs_filtered) == 1: return op_strs_filtered[0]
                
                joiner = f" {operator_upper} "
                res_str = joiner.join(op_strs_filtered)

        elif isinstance(node, ProximityOpNode):
            base_op_type = node.operator.upper()
            if node.distance is not None and base_op_type in ["ADJ", "NEAR"]:
                current_node_op_type_str = f"{base_op_type}{node.distance}"
            else:
                current_node_op_type_str = base_op_type
            terms_s = [self._generate_node(t, current_node_op_type_str) for t in node.terms]
            terms_s_filtered = [ts for ts in terms_s if ts]
            if not terms_s_filtered: return ""
            if len(terms_s_filtered) == 1: return terms_s_filtered[0]
            res_str = f" {current_node_op_type_str} ".join(terms_s_filtered)

        elif isinstance(node, ClassificationNode):
            current_node_op_type_str = "CLASSIFICATION_ATOM"
            base_val = node.value.replace("/", "")
            if node.scheme == "CPC" and node.include_children:
                base_val += "/low"
            res_str = base_val
        
        elif isinstance(node, DateSearchNode):
            current_node_op_type_str = "DATE_EXPR_ATOM"
            google_date_type = CANONICAL_TO_GOOGLE_DATE_TYPE.get(node.field_canonical_name)
            if not google_date_type: return f"Error:UnknownDateK-V({node.field_canonical_name})"
            operator_map = {">=": "after", "<=": "before"}
            keyword = operator_map.get(node.operator)
            if not keyword: return f"Error:UnhandledDateOp({node.operator})"
            res_str = f"{keyword}:{google_date_type}:{node.date_value}"
        
        else: 
            return f"Error:UnhandledASTNode({type(node).__name__})"

        if self._needs_paren_google(current_node_op_type_str, parent_op_type):
            return f"({res_str})"
            
        return res_str