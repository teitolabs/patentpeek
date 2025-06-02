# uspto_generator.py
from ast_nodes import (
    ASTNode, QueryRootNode, TermNode, BooleanOpNode, ProximityOpNode,
    FieldedSearchNode, DateSearchNode, ClassificationNode
)
from typing import Optional, Dict, List

CANONICAL_TO_USPTO_FIELD: Dict[str, str] = {
    "title": "TTL", "abstract": "ABST", "claims": "ACLM", "description": "SPEC",
    "inventor_name": "IN", "assignee_name": "AN", "cpc": "CPC", "ipc": "IPC",
    "us_classification_ccls": "CCLS", "patent_number": "PN",
    "application_number": "APP", "document_id": "DID",
    "publication_date": "PD", "issue_date": "ISD", "application_date": "AD",
    "application_year": "AY", "publication_year": "PY"
}

USPTO_OP_PRECEDENCE = {
    "TERM": 100, "DATE_SEARCH": 100, "FIELD_WRAPPER": 100, 
    "NOT_OPERAND_CTX": 90, 
    "ADJ": 80, "NEAR": 80, "WITH": 80, "SAME": 80,
    "AND": 70,
    "XOR": 60, 
    "OR": 50,
    "FIELD_CONTENT_CTX": 110, 
    None: 0
}

class ASTToUSPTOQueryGenerator:
    def __init__(self): pass

    def _get_uspto_field_code(self, canonical_name: str, system_field_code: Optional[str] = None) -> Optional[str]:
        return CANONICAL_TO_USPTO_FIELD.get(canonical_name)

    def _format_cpc_for_uspto(self, cpc_node: ClassificationNode) -> str:
        value = cpc_node.value # ... (same)
        if len(value) > 4 and value[:4].isalnum() and value[4:].isalnum():
            if value[0].isalpha() and value[1:3].isdigit() and value[3].isalpha(): 
                if len(value) >= 6 and value[4:6].isdigit(): return f"{value[:4]}{value[4:6]}/{value[6:]}" if len(value) > 6 else f"{value[:4]}{value[4:6]}"
                return f"{value[:4]}/{value[4:]}"
            elif value[0].isalpha() and value[1:4].isdigit(): 
                if len(value) >= 6 and value[4:6].isdigit(): return f"{value[:4]}{value[4:6]}/{value[6:]}" if len(value) > 6 else f"{value[:4]}{value[4:6]}"
                if len(value) > 5 : return f"{value[:4]}{value[4]}/{value[5:]}"
        return value

    def _format_ipc_for_uspto(self, ipc_node: ClassificationNode) -> str:
        value = ipc_node.value # ... (same)
        if len(value) > 4 and value[:4].isalnum() and value[4:].isalnum():
            if value[0].isalpha() and value[1:3].isdigit() and value[3].isalpha():
                 if len(value) >= 6 and value[4:6].isdigit(): return f"{value[:4]}{value[4:6]}/{value[6:]}" if len(value) > 6 else f"{value[:4]}{value[4:6]}"
                 return f"{value[:4]}/{value[4:]}"
            elif value[0].isalpha() and value[1:4].isdigit():
                if len(value) >= 6 and value[4:6].isdigit(): return f"{value[:4]}{value[4:6]}/{value[6:]}" if len(value) > 6 else f"{value[:4]}{value[4:6]}"
                if len(value) > 5 : return f"{value[:4]}{value[4]}/{value[5:]}"
        return value

    def _needs_paren_uspto(self, current_op_type_str: Optional[str], parent_op_context: Optional[str], node_instance: ASTNode, res_str_for_check: str) -> bool:
        if not parent_op_context: return False 
        
        # If already parenthesized or a quoted phrase, usually no more needed from this level
        if (res_str_for_check.startswith("(") and res_str_for_check.endswith(")")) or \
           (res_str_for_check.startswith('"') and res_str_for_check.endswith('"')):
            return False

        if isinstance(node_instance, (DateSearchNode, FieldedSearchNode)):
            # These "blocks" need parentheses if they are operands of AND, OR, XOR, PROX
            if parent_op_context in ["AND", "OR", "XOR", "ADJ", "NEAR", "WITH", "SAME"]:
                return True
            return False
        
        # Simple terms usually don't get wrapped in parens just for being operands, unless tests force it.
        # Current tests imply terms don't get wrapped: `term1 AND term2`
        if isinstance(node_instance, TermNode):
            return False
        
        # If current is an operation itself:
        if not current_op_type_str : return False

        current_op_base = current_op_type_str.rstrip('0123456789')
        parent_op_base = parent_op_context.rstrip('0123456789')
        
        current_prec = USPTO_OP_PRECEDENCE.get(current_op_base, 0)
        parent_prec = USPTO_OP_PRECEDENCE.get(parent_op_base, 0)

        if current_prec == 0: return False

        strong_grouping_contexts = ["NOT_OPERAND_CTX", "FIELD_CONTENT_CTX"]
        if parent_op_context in strong_grouping_contexts:
            # If current node is an actual operation, it needs parens inside these contexts.
            return current_prec > 0 and current_prec < USPTO_OP_PRECEDENCE["TERM"] # i.e., it's an op

        if parent_prec == 0: return False

        if current_prec < parent_prec: return True
        if current_prec == parent_prec and current_op_base != parent_op_base: return True
        if current_op_base in ["AND", "OR", "XOR"] and parent_op_base in ["ADJ", "NEAR", "WITH", "SAME"]: return True
            
        return False

    def _generate_node_uspto(self, node: ASTNode, parent_op_context: Optional[str] = None) -> str:
        res_str = ""
        current_node_op_type_str = "" 

        if isinstance(node, TermNode):
            current_node_op_type_str = "TERM"
            if node.value == "__EMPTY__" or node.value == "__EMPTY_AFTER_SET__": res_str = ""
            elif node.is_phrase: res_str = f'"{node.value}"'
            else:
                if node.value.upper() in ["AND", "OR", "NOT", "XOR", "ADJ", "NEAR", "WITH", "SAME"] and not node.is_phrase:
                    res_str = f'"{node.value}"'
                else: res_str = node.value
        
        elif isinstance(node, BooleanOpNode):
            operator_upper = node.operator.upper()
            current_node_op_type_str = operator_upper

            if operator_upper == "NOT":
                if len(node.operands) == 1:
                    operand_node = node.operands[0]
                    operand_str = self._generate_node_uspto(operand_node, parent_op_context="NOT_OPERAND_CTX")
                    res_str = f"NOT {operand_str}" 
                else: return f"ERROR_UNHANDLED_NOT_OPERANDS_LEN_{len(node.operands)}"
            else: # AND, OR, XOR
                op_strs = [self._generate_node_uspto(op_node, parent_op_context=current_node_op_type_str) for op_node in node.operands]
                op_strs_filtered = [s for s in op_strs if s]
                if not op_strs_filtered: return ""
                if len(op_strs_filtered) == 1: return op_strs_filtered[0]
                res_str = f" {operator_upper} ".join(op_strs_filtered)

        elif isinstance(node, ProximityOpNode):
            base_op_type = node.operator.upper()
            current_node_op_type_str = base_op_type
            if node.distance is not None and base_op_type in ["ADJ", "NEAR"]:
                current_node_op_type_str = f"{base_op_type}{node.distance}"
            terms_s = [self._generate_node_uspto(t_node, parent_op_context=current_node_op_type_str) for t_node in node.terms]
            terms_s_filtered = [ts for ts in terms_s if ts]
            if not terms_s_filtered: return ""
            if len(terms_s_filtered) == 1: return terms_s_filtered[0]
            res_str = f" {current_node_op_type_str} ".join(terms_s_filtered)

        elif isinstance(node, FieldedSearchNode):
            uspto_field_code = self._get_uspto_field_code(node.field_canonical_name, node.system_field_code)
            current_node_op_type_str = "FIELD_WRAPPER" 

            if not uspto_field_code:
                return self._generate_node_uspto(node.query, parent_op_context="FIELD_CONTENT_ONLY")

            query_str = ""
            if node.field_canonical_name == "cpc" and isinstance(node.query, ClassificationNode):
                query_str = self._format_cpc_for_uspto(node.query)
            elif node.field_canonical_name == "ipc" and isinstance(node.query, ClassificationNode):
                query_str = self._format_ipc_for_uspto(node.query)
            else:
                query_str = self._generate_node_uspto(node.query, parent_op_context="FIELD_CONTENT_CTX")

            if not query_str: return ""
            
            # Avoid FIELD/((content))
            if query_str.startswith("((") and query_str.endswith("))"):
                 inner_content = query_str[1:-1]
                 balance = 0; is_single_balanced_group = True
                 for i_char, char_val in enumerate(inner_content):
                     if char_val == '(': balance += 1
                     elif char_val == ')': balance -= 1
                     if balance == 0 and i_char < len(inner_content) - 1: is_single_balanced_group = False; break
                 if balance != 0: is_single_balanced_group = False
                 if is_single_balanced_group and inner_content.startswith("(") and inner_content.endswith(")"):
                     query_str = inner_content
            res_str = f"{uspto_field_code}/({query_str})"

        elif isinstance(node, DateSearchNode):
            current_node_op_type_str = "DATE_SEARCH"
            uspto_field_code = self._get_uspto_field_code(node.field_canonical_name, node.system_field_code)
            if not uspto_field_code: return f"ERROR_UNKNOWN_USPTO_DATE_FIELD_{node.field_canonical_name}"
            op = node.operator; date_val = node.date_value; date_val2 = node.date_value2
            if node.field_canonical_name in ["application_year", "publication_year"]:
                if not date_val.isdigit() or len(date_val) != 4: return f"ERROR_INVALID_YEAR_FORMAT_{date_val}"
                res_str = f"@{uspto_field_code}{op}{date_val}"
                if date_val2: 
                    if not date_val2.isdigit() or len(date_val2) != 4: return f"ERROR_INVALID_YEAR2_FORMAT_{date_val2}"
                    res_str += f"<={date_val2}" 
            else: 
                if not date_val.isdigit() or len(date_val) != 8: return f"ERROR_INVALID_DATE_FORMAT_{date_val}"
                res_str = f"@{uspto_field_code}{op}{date_val}"
                if date_val2:
                    if not date_val2.isdigit() or len(date_val2) != 8: return f"ERROR_INVALID_DATE2_FORMAT_{date_val2}"
                    res_str += f"<={date_val2}"
        elif isinstance(node, ClassificationNode):
            current_node_op_type_str = "CLASSIFICATION_ATOM"
            return f"ERROR_STANDALONE_CLASSIFICATION_NODE_{node.scheme}_{node.value}"
        else:
            return f"ERROR_UNHANDLED_AST_NODE_FOR_USPTO_{type(node).__name__}"

        if self._needs_paren_uspto(current_node_op_type_str, parent_op_context, node, res_str):
            return f"({res_str})"
            
        return res_str

    def generate(self, ast_root: QueryRootNode) -> str:
        if not isinstance(ast_root, QueryRootNode):
            return "Error: Invalid AST root for USPTO generation"
        query_part = self._generate_node_uspto(ast_root.query, parent_op_context=None)
        if "ERROR_" in query_part.upper() or "UNHANDLED_" in query_part.upper():
            return query_part
        return query_part.strip()