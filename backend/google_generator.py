# google_generator.py
from ast_nodes import (
    ASTNode, QueryRootNode, TermNode, BooleanOpNode, ProximityOpNode,
    FieldedSearchNode, DateSearchNode, ClassificationNode
)
from typing import Optional


class ASTToGoogleQueryGenerator:
    def __init__(self): pass

    def generate(self, ast_root: QueryRootNode) -> str:
        if not isinstance(ast_root, QueryRootNode): return "Error: Invalid AST root"
        return self._generate_node(ast_root.query, is_top_level_expr=True, parent_op_type=None, parent_node_instance=None)

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

    def _generate_node(self, node: ASTNode, is_top_level_expr: bool = False, parent_op_type: Optional[str] = None, parent_node_instance: Optional[ASTNode] = None) -> str:
        res_str = "" 
        current_node_op_type = None

        if isinstance(node, TermNode):
            current_node_op_type = "TERM"
            if node.value == "__EMPTY__" or node.value == "__EMPTY_AFTER_SET__": res_str = ""
            elif node.is_phrase: res_str = f'"{node.value}"'
            elif node.value.upper() in ["AND","OR","NOT","NEAR","ADJ","WITH","SAME"] and not node.is_phrase:
                res_str = f'"{node.value}"'
            else: res_str = node.value
        
        elif isinstance(node, FieldedSearchNode):
            if node.field_canonical_name == "application_number":
                return f"Error:UnhandledASTNode({type(node).__name__})"

            field_google = self._map_canonical_to_google_field(node.field_canonical_name)
            current_node_op_type = field_google if field_google else "FIELD_ASSIGN" 
            
            query_str = self._generate_node(node.query, False, current_node_op_type, node)
            
            if field_google in ["TI", "AB", "CL"]: res_str = f"{field_google}=({query_str})"
            elif field_google == "CPC" or field_google == "IPC":
                val_transformed = query_str
                if isinstance(node.query, TermNode):
                    val_transformed = node.query.value.replace("/", "")
                elif isinstance(node.query, ClassificationNode):
                    val_transformed = query_str

                if field_google == "CPC" and isinstance(node.query, ClassificationNode) and node.query.include_children:
                    if not val_transformed.endswith("/low"): val_transformed += "/low"
                res_str = f"{field_google}:{val_transformed}"
            elif field_google in ["assignee", "inventor", "patent_number"]:
                if field_google == "patent_number":
                    if not (query_str.startswith('"') and query_str.endswith('"')): query_str = f'"{query_str}"'
                elif (field_google == "assignee" or field_google == "inventor"):
                    if (' ' in query_str or '*' in query_str or '?' in query_str or '$' in query_str) and \
                       not (query_str.startswith('"') and query_str.endswith('"')):
                        query_str = f'"{query_str}"'
                res_str = f"{field_google}:({query_str})"
            else:
                res_str = query_str 
        
        elif isinstance(node, BooleanOpNode):
            operator_upper = node.operator.upper()
            current_node_op_type = operator_upper

            if operator_upper == "NOT" and len(node.operands) == 1:
                operand_node = node.operands[0]
                operand_str = self._generate_node(operand_node, False, "NOT_OPERATOR", node) 
                
                is_simple_term_for_not_prefix = isinstance(operand_node,TermNode) and \
                                 not operand_node.is_phrase and \
                                 " " not in operand_node.value and \
                                 not (operand_str.startswith("(") and operand_str.endswith(")")) and \
                                 not operand_str.startswith("-")

                if is_simple_term_for_not_prefix:
                    res_str = f"-{operand_str.strip('\"')}"
                    current_node_op_type = "NOT_PREFIX"
                else:
                    if isinstance(operand_node, TermNode) and operand_node.is_phrase:
                         res_str = f"NOT ({operand_str})" 
                    elif (operand_str.startswith("(") and operand_str.endswith(")")) or \
                         (isinstance(operand_node, FieldedSearchNode) and '=' in operand_str and '(' in operand_str and ')' in operand_str):
                        res_str = f"NOT {operand_str}"
                    else:
                        res_str = f"NOT ({operand_str})"
            else:
                op_strs = [self._generate_node(op, False, current_node_op_type, node) for op in node.operands]
                op_strs = [s for s in op_strs if s]

                if not op_strs: return ""
                if len(op_strs) == 1:
                    return op_strs[0] 
                
                joiner = f" {current_node_op_type} "
                if current_node_op_type == "AND" and is_top_level_expr:
                    use_space_for_top_level_and = False
                    if node.operands and len(node.operands) >= 2: 
                        all_operands_are_blocks = all(isinstance(op, (DateSearchNode, FieldedSearchNode)) for op in node.operands)
                        if all_operands_are_blocks:
                            use_space_for_top_level_and = True
                        elif len(node.operands) == 2: 
                            n1,n2 = node.operands[0],node.operands[1]
                            b1 = isinstance(n1,(DateSearchNode,FieldedSearchNode))
                            b2 = isinstance(n2,(DateSearchNode,FieldedSearchNode))
                            if (b1 and not b2) or (b2 and not b1): 
                                use_space_for_top_level_and = True
                    if use_space_for_top_level_and: joiner = " "
                res_str = joiner.join(op_strs)
        
        elif isinstance(node, ProximityOpNode):
            base_op_type = node.operator.upper()
            if node.distance is not None and base_op_type in ["ADJ", "NEAR"]:
                current_node_op_type = f"{base_op_type}{node.distance}"
            else:
                current_node_op_type = base_op_type
            
            terms_s = [self._generate_node(t, False, current_node_op_type, node) for t in node.terms]
            terms_s = [ts for ts in terms_s if ts]

            if not terms_s: return ""
            if len(terms_s) == 1:
                return terms_s[0] 
            
            joiner_op_str = current_node_op_type 
            res_str = f" {joiner_op_str} ".join(terms_s)

        elif isinstance(node, ClassificationNode):
            if node.scheme == "CPC": current_node_op_type = "CPC_FIELD"
            elif node.scheme == "IPC": current_node_op_type = "IPC_FIELD"
            else: current_node_op_type = "TERM"
            res_str = node.value.replace("/", "")
        
        elif isinstance(node, DateSearchNode):
            current_node_op_type = "DATE_EXPR"
            type_map = {"publication_date":"publication","issue_date":"publication",
                        "application_date":"filing","priority_date":"priority"}
            google_date_type = type_map.get(node.field_canonical_name)
            parts = []
            date_val_fmt = node.date_value.replace("/","")

            if not google_date_type: 
                if node.field_canonical_name in ["application_year", "publication_year"]:
                    year_val1 = date_val_fmt 
                    year_val2 = node.date_value2.replace("/","") if node.date_value2 else None 
                    base_type = "filing" if "application" in node.field_canonical_name else "publication"
                    
                    if node.operator == "=":
                        parts.extend([f"after:{base_type}:{year_val1}0101", f"before:{base_type}:{year_val1}1231"])
                    elif node.operator == ">=" and year_val2:
                        parts.extend([f"after:{base_type}:{year_val1}0101", f"before:{base_type}:{year_val2}1231"])
                    elif node.operator == ">=": parts.append(f"after:{base_type}:{year_val1}0101") 
                    elif node.operator == "<=": parts.append(f"before:{base_type}:{year_val1}1231") 
                    elif node.operator == ">": parts.append(f"after:{base_type}:{year_val1}1231") 
                    elif node.operator == "<": parts.append(f"before:{base_type}:{year_val1}0101") 
                    else: parts.append(f"Error:UnhandledYearOp({node.operator})")
                else: parts.append(f"Error:UnknownGoogleDateType({node.field_canonical_name})")
            else:
                date_val1_fmt_google = date_val_fmt 
                if node.date_value2:
                    date_val2_fmt_google = node.date_value2.replace("/","") 
                    if node.operator == ">=" : parts.append(f"after:{google_date_type}:{date_val1_fmt_google}")
                    parts.append(f"before:{google_date_type}:{date_val2_fmt_google}")
                else:
                    if node.operator == ">=" : parts.append(f"after:{google_date_type}:{date_val1_fmt_google}")
                    elif node.operator == "<=" : parts.append(f"before:{google_date_type}:{date_val1_fmt_google}")
                    elif node.operator == "=":
                        parts.extend([f"after:{google_date_type}:{date_val1_fmt_google}", f"before:{google_date_type}:{date_val1_fmt_google}"])
                    elif node.operator == ">" :
                        parts.append(f"after:{google_date_type}:{date_val1_fmt_google}") 
                    elif node.operator == "<" :
                        parts.append(f"before:{google_date_type}:{date_val1_fmt_google}")
                    else: parts.append(f"Error:UnhandledDateOp({node.operator})")
            
            res_str = " ".join(p for p in parts if p and not p.startswith("Error:"))
            if any(e_msg in res_str for e_msg in ["Error:UnhandledYearOp","Error:UnknownGoogleDateType","Error:UnhandledDateOp"]):
                return res_str
        else: 
            return f"Error:UnhandledASTNode({type(node).__name__})"

        if not is_top_level_expr and res_str:
            if isinstance(node, (BooleanOpNode, ProximityOpNode)):
                if current_node_op_type != "NOT_PREFIX":
                    parent_provides_grouping = parent_op_type in [
                        "TI", "AB", "CL", "assignee", "inventor", "patent_number", 
                        "FIELD_ASSIGN", "CPC", "IPC", "NOT_OPERATOR"
                    ]
                    if not parent_provides_grouping:
                        if not (res_str.startswith("(") and res_str.endswith(")")):
                            return f"({res_str})"
        return res_str