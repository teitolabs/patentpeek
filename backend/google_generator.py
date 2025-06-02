# google_generator.py
from ast_nodes import (
    ASTNode, QueryRootNode, TermNode, BooleanOpNode, ProximityOpNode,
    FieldedSearchNode, DateSearchNode, ClassificationNode
)
from typing import Optional

GOOGLE_OP_PRECEDENCE = {
    "TERM": 100, "DATE_EXPR_ATOM": 100, "FIELD_WRAPPER": 100,
    "NOT_PREFIX": 90,
    "ADJ": 80, "NEAR": 80, "WITH": 80, "SAME": 80,
    "NOT_OPERAND": 70, 
    "AND": 60,
    "XOR": 50,
    "OR": 40,
    None: 0 
}

class ASTToGoogleQueryGenerator:
    def __init__(self): pass

    def generate(self, ast_root: QueryRootNode) -> str:
        if not isinstance(ast_root, QueryRootNode): return "Error: Invalid AST root"
        return self._generate_node(ast_root.query, is_top_level_expr=True, parent_op_type=None)

    def _map_canonical_to_google_field(self, canonical_name: str) -> Optional[str]:
        if canonical_name == "title": return "TI" 
        if canonical_name == "abstract": return "AB"
        if canonical_name == "claims": return "CL"
        if canonical_name == "description": return None 
        if canonical_name == "cpc": return "CPC"
        if canonical_name == "ipc": return "IPC" 
        if canonical_name == "assignee_name": return "assignee" 
        if canonical_name == "inventor_name": return "inventor"
        if canonical_name == "patent_number": return "patent_number"
        return None

    def _needs_paren_google(self, current_op_type_str: Optional[str], parent_op_type_str: Optional[str], node_instance: ASTNode, is_top_level_expr: bool) -> bool:
        if is_top_level_expr and not isinstance(node_instance, TermNode): # Top-level ops don't get wrapped by this, except maybe terms if they were part of an implicit AND.
             # But if the top node itself IS an operation, its operands will be checked.
            pass # Let the structure dictate.

        if not parent_op_type_str or not current_op_type_str: return False
        
        # If current node is an atom-like thing, it generally doesn't need parens from its parent op
        # unless it's something like a NOT_PREFIX that needs to be part of a larger NOT expression.
        if isinstance(node_instance, (TermNode, DateSearchNode, ClassificationNode)) and current_op_type_str != "NOT_PREFIX":
            return False
        if current_op_type_str == "NOT_PREFIX": # -term never gets further parens like (-term)
            return False

        strong_grouping_parents = ["TI", "AB", "CL", "assignee", "inventor", "patent_number", "CPC", "IPC", "FIELD_WRAPPER"]
        if parent_op_type_str in strong_grouping_parents:
             return isinstance(node_instance, (BooleanOpNode, ProximityOpNode)) # Ops inside fields need parens

        current_op_base = current_op_type_str.rstrip('0123456789') if current_op_type_str else None
        parent_op_base = parent_op_type_str.rstrip('0123456789') if parent_op_type_str else None

        current_prec = GOOGLE_OP_PRECEDENCE.get(current_op_base, 0)
        parent_prec = GOOGLE_OP_PRECEDENCE.get(parent_op_base, 0)
            
        if parent_op_type_str == "NOT_OPERAND": 
            return current_prec > 0 and current_prec < GOOGLE_OP_PRECEDENCE["NOT_OPERAND"] # Is an op
            
        if current_prec == 0 or parent_prec == 0: return False

        if current_prec < parent_prec: return True # (A OR B) AND C
        
        if current_prec == parent_prec and current_op_base != parent_op_base:
             # e.g. A ADJ (B NEAR C). Current is B NEAR C. Parent is ADJ.
             # This also handles (A ADJ B) NEAR C. If (A ADJ B) is current_op_type_str.
             return True
            
        return False

    def _generate_node(self, node: ASTNode, is_top_level_expr: bool = False, parent_op_type: Optional[str] = None) -> str:
        res_str = ""
        current_node_op_type_str = "" 

        if isinstance(node, TermNode):
            current_node_op_type_str = "TERM"
            if node.value == "__EMPTY__" or node.value == "__EMPTY_AFTER_SET__": res_str = ""
            elif node.is_phrase: res_str = f'"{node.value}"'
            elif node.value.upper() in ["AND","OR","NOT","NEAR","ADJ","WITH","SAME", "XOR"] and not node.is_phrase:
                res_str = f'"{node.value}"'
            else: res_str = node.value
        
        elif isinstance(node, FieldedSearchNode):
            if node.field_canonical_name == "application_number":
                return f"Error:UnhandledASTNode(FieldedSearchNode_UnsupportedField_{node.field_canonical_name})"
            field_google = self._map_canonical_to_google_field(node.field_canonical_name)
            current_node_op_type_str = field_google if field_google else "FIELD_WRAPPER"
            query_str = self._generate_node(node.query, False, current_node_op_type_str) # Pass field code as parent context
            if field_google in ["TI", "AB", "CL"]: res_str = f"{field_google}=({query_str})"
            elif field_google == "CPC" or field_google == "IPC":
                val_transformed = query_str 
                if isinstance(node.query, TermNode): val_transformed = node.query.value.replace("/", "")
                if field_google == "CPC" and isinstance(node.query, ClassificationNode) and node.query.include_children:
                    if not val_transformed.endswith("/low"): val_transformed += "/low"
                res_str = f"{field_google}:{val_transformed}"
            elif field_google in ["assignee", "inventor", "patent_number"]:
                if isinstance(node.query, TermNode) and not node.query.is_phrase:
                    if field_google == "patent_number" or \
                       (' ' in query_str or any(c in query_str for c in ['*', '?', '$'])):
                        query_str = f'"{query_str}"'
                res_str = f"{field_google}:({query_str})"
            else: res_str = query_str 
        
        elif isinstance(node, BooleanOpNode):
            operator_upper = node.operator.upper()
            current_node_op_type_str = operator_upper

            if operator_upper == "NOT" and len(node.operands) == 1:
                operand_node = node.operands[0]
                operand_str = self._generate_node(operand_node, False, "NOT_OPERAND")
                is_simple_term_for_not_prefix = isinstance(operand_node, TermNode) and \
                                 not operand_node.is_phrase and " " not in operand_node.value and \
                                 not (operand_str.startswith("(") and operand_str.endswith(")")) and \
                                 not operand_str.startswith("-") and \
                                 not (isinstance(operand_node, TermNode) and operand_node.value.upper() in ["AND", "OR", "NOT", "XOR"])
                if is_simple_term_for_not_prefix:
                    current_node_op_type_str = "NOT_PREFIX"
                    res_str = f"-{operand_str.strip('\"')}"
                else:
                    res_str = f"NOT {operand_str}"
            else: # AND, OR, XOR
                op_strs = [self._generate_node(op_node, False, current_node_op_type_str) for op_node in node.operands]
                op_strs_filtered = [s for s in op_strs if s]
                if not op_strs_filtered: return ""
                if len(op_strs_filtered) == 1: return op_strs_filtered[0]
                
                joiner = f" {current_node_op_type_str} " # Default e.g. " OR ", " XOR "
                if current_node_op_type_str == "AND":
                    # If this AND is top-level AND its operands are simple terms/phrases or blocks, use space.
                    # Otherwise, (e.g. nested AND, or AND with complex operands like NOTs) use explicit " AND ".
                    if is_top_level_expr:
                        # Check if all operands are "simple" enough for implicit AND.
                        # "Simple" means terms, phrases, or self-contained blocks like TI=() or dates.
                        # If any operand is a NOT_PREFIX (-term), then explicit AND is clearer.
                        if all(isinstance(op, (TermNode, FieldedSearchNode, DateSearchNode)) for op in node.operands) and \
                           not any(op_str.startswith("-") for op_str in op_strs_filtered): # Check generated strings for NOT_PREFIX
                            joiner = " "
                        else:
                            joiner = " AND " # For -A AND -B or X AND (Y OR Z) at top level
                    else: # Non-top-level AND is always explicit
                        joiner = " AND " 
                
                res_str = joiner.join(op_strs_filtered)
        
        elif isinstance(node, ProximityOpNode):
            base_op_type = node.operator.upper()
            current_node_op_type_str = base_op_type # e.g. ADJ, NEAR
            if node.distance is not None and base_op_type in ["ADJ", "NEAR"]:
                current_node_op_type_str = f"{base_op_type}{node.distance}" # e.g. ADJ5
            terms_s = [self._generate_node(t_node, False, current_node_op_type_str) for t_node in node.terms]
            terms_s_filtered = [ts for ts in terms_s if ts]
            if not terms_s_filtered: return ""
            if len(terms_s_filtered) == 1: return terms_s_filtered[0]
            res_str = f" {current_node_op_type_str} ".join(terms_s_filtered)

        elif isinstance(node, ClassificationNode):
            current_node_op_type_str = f"{node.scheme}_CLASSIFICATION_ATOM"
            res_str = node.value.replace("/", "")
        
        elif isinstance(node, DateSearchNode):
            current_node_op_type_str = "DATE_EXPR_ATOM"
            # ... (Date logic same) ...
            type_map = {"publication_date":"publication","issue_date":"publication", "application_date":"filing","priority_date":"priority"}
            google_date_type = type_map.get(node.field_canonical_name)
            parts = []; date_val_fmt = node.date_value.replace("/","")
            if not google_date_type: 
                if node.field_canonical_name in ["application_year", "publication_year"]:
                    year_val1 = date_val_fmt[:4]; year_val2 = node.date_value2.replace("/","")[:4] if node.date_value2 else None 
                    base_type_for_year = "filing" if "application" in node.field_canonical_name else "publication"
                    if node.operator == "=":
                        if len(year_val1) == 4: parts.extend([f"after:{base_type_for_year}:{year_val1}0101", f"before:{base_type_for_year}:{year_val1}1231"])
                        else: parts.append(f"Error:InvalidYearFormat({year_val1})")
                    elif node.operator == ">=" and year_val2 and len(year_val1)==4 and len(year_val2)==4: parts.extend([f"after:{base_type_for_year}:{year_val1}0101", f"before:{base_type_for_year}:{year_val2}1231"])
                    elif node.operator == ">=" and len(year_val1)==4 : parts.append(f"after:{base_type_for_year}:{year_val1}0101") 
                    elif node.operator == "<=" and len(year_val1)==4 : parts.append(f"before:{base_type_for_year}:{year_val1}1231") 
                    elif node.operator == ">" and len(year_val1)==4 : parts.append(f"after:{base_type_for_year}:{year_val1}1231") 
                    elif node.operator == "<" and len(year_val1)==4 : parts.append(f"before:{base_type_for_year}:{year_val1}0101") 
                    else: parts.append(f"Error:UnhandledYearOp({node.operator}, Year:{year_val1})")
                else: parts.append(f"Error:UnknownGoogleDateType({node.field_canonical_name})")
            else: 
                if len(date_val_fmt) != 8: parts.append(f"Error:InvalidDateFormat({date_val_fmt})")
                else:
                    date_val1_fmt_google = date_val_fmt 
                    if node.date_value2: 
                        date_val2_fmt_google = node.date_value2.replace("/","");
                        if len(date_val2_fmt_google) != 8: parts.append(f"Error:InvalidDate2Format({date_val2_fmt_google})")
                        else:
                            if node.operator == ">=" : parts.append(f"after:{google_date_type}:{date_val1_fmt_google}"); parts.append(f"before:{google_date_type}:{date_val2_fmt_google}")
                            else: parts.append(f"Error:UnhandledDateRangeOp({node.operator})")
                    else: 
                        if node.operator == ">=" : parts.append(f"after:{google_date_type}:{date_val1_fmt_google}")
                        elif node.operator == "<=" : parts.append(f"before:{google_date_type}:{date_val1_fmt_google}")
                        elif node.operator == "=": parts.extend([f"after:{google_date_type}:{date_val1_fmt_google}", f"before:{google_date_type}:{date_val1_fmt_google}"])
                        elif node.operator == ">" : parts.append(f"after:{google_date_type}:{date_val1_fmt_google}") 
                        elif node.operator == "<" : parts.append(f"before:{google_date_type}:{date_val1_fmt_google}")
                        else: parts.append(f"Error:UnhandledDateOp({node.operator})")
            res_str = " ".join(p for p in parts if p and not p.startswith("Error:"))
            if any(e_msg in res_str for e_msg in ["Error:UnhandledYearOp","Error:UnknownGoogleDateType","Error:UnhandledDateOp", "Error:InvalidDateFormat", "Error:InvalidYearFormat"]): return res_str
        else: 
            return f"Error:UnhandledASTNode({type(node).__name__})"

        if not (res_str.startswith("(") and res_str.endswith(")")) and \
           not (res_str.startswith('"') and res_str.endswith('"')):
            if self._needs_paren_google(current_node_op_type_str, parent_op_type, node, is_top_level_expr):
                if not (current_node_op_type_str == "NOT_PREFIX" and res_str.startswith("-")):
                    return f"({res_str})"
            
        return res_str