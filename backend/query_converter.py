# query_converter.py
# (Full code with the above refinements integrated)

from typing import List, Optional, Literal, Union, Dict, Any
import pyparsing as pp
import re

# --- 1. Abstract Syntax Tree (AST) Definition ---
class ASTNode:
    def __init__(self): pass
    def __eq__(self, other):
        if type(other) is type(self):
            return all(getattr(self, k, None) == getattr(other, k, None) for k in self.get_compare_attrs())
        return False
    def get_compare_attrs(self): return [k for k, v in self.__dict__.items() if not k.startswith('_')]
    def __repr__(self):
        attrs = {k: v for k, v in self.__dict__.items() if not k.startswith('_') and v is not None}
        return f"{self.__class__.__name__}({', '.join(f'{k}={v!r}' for k, v in attrs.items())})"
    def to_dict(self) -> Dict[str, Any]:
        data = {'node_type': self.__class__.__name__}
        for key, value in self.__dict__.items():
            if key.startswith('_'): continue
            if isinstance(value, ASTNode): data[key] = value.to_dict()
            elif isinstance(value, list) and all(isinstance(item, ASTNode) for item in value):
                data[key] = [item.to_dict() for item in value]
            else: data[key] = value
        return data
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ASTNode':
        node_type_str = data.pop('node_type', None)
        if not node_type_str: raise ValueError("Missing 'node_type'")
        target_class = globals().get(node_type_str)
        if not target_class or not issubclass(target_class, ASTNode):
            raise ValueError(f"Unknown AST node_type: {node_type_str}")
        processed_args = {}
        for key, value in data.items():
            if isinstance(value, dict) and 'node_type' in value:
                processed_args[key] = ASTNode.from_dict(value)
            elif isinstance(value, list) and value and isinstance(value[0], dict) and 'node_type' in value[0]:
                processed_args[key] = [ASTNode.from_dict(item) for item in value]
            else: processed_args[key] = value
        return target_class(**processed_args)

class TermNode(ASTNode):
    def __init__(self, value: str, is_phrase: bool = False, has_wildcard: Optional[bool] = None):
        super().__init__(); self.value = value; self.is_phrase = is_phrase
        if has_wildcard is None: self.has_wildcard = bool(re.search(r'[\?\*\$]', value)) if value else False
        else: self.has_wildcard = has_wildcard
    def get_compare_attrs(self): return ['value', 'is_phrase', 'has_wildcard']

class ClassificationNode(ASTNode):
    def __init__(self, scheme: Literal["CPC", "IPC", "USPC", "CCLS"], value: str, include_children: bool = False):
        super().__init__(); self.scheme = scheme; self.value = value; self.include_children = include_children
    def get_compare_attrs(self): return ['scheme', 'value', 'include_children']

class BooleanOpNode(ASTNode):
    def __init__(self, operator: Literal["AND", "OR", "NOT", "XOR"], operands: List[ASTNode]):
        super().__init__(); self.operator = operator; self.operands = operands
    def get_compare_attrs(self): return ['operator', 'operands']

class ProximityOpNode(ASTNode):
    def __init__(self, operator: Literal["ADJ", "NEAR", "WITH", "SAME"], terms: List[ASTNode],
                 distance: Optional[int] = None, ordered: bool = False,
                 scope_unit: Optional[Literal["word", "sentence", "paragraph"]] = None):
        super().__init__(); self.operator = operator; self.terms = terms; self.distance = distance
        self.ordered = ordered; self.scope_unit = scope_unit
    def get_compare_attrs(self): return ['operator', 'terms', 'distance', 'ordered', 'scope_unit']

class FieldedSearchNode(ASTNode):
    def __init__(self, field_canonical_name: str, query: ASTNode, system_field_code: Optional[str] = None):
        super().__init__(); self.field_canonical_name = field_canonical_name; self.query = query
        self.system_field_code = system_field_code
    def get_compare_attrs(self): return ['field_canonical_name', 'query', 'system_field_code']

class DateSearchNode(ASTNode):
    def __init__(self, field_canonical_name: Literal["publication_date", "application_date", "priority_date", "issue_date", "application_year", "publication_year"],
                 operator: Literal[">=", "<=", "=", ">", "<", "<>"], date_value: str,
                 date_value2: Optional[str] = None, system_field_code: Optional[str] = None):
        super().__init__(); self.field_canonical_name = field_canonical_name; self.operator = operator
        self.date_value = date_value; self.date_value2 = date_value2; self.system_field_code = system_field_code
    def get_compare_attrs(self): return ['field_canonical_name', 'operator', 'date_value', 'date_value2', 'system_field_code']

class QueryRootNode(ASTNode):
    def __init__(self, query: ASTNode, settings: Optional[Dict[str, Any]] = None):
        super().__init__(); self.query = query; self.settings = settings if settings else {}
    def get_compare_attrs(self): return ['query', 'settings']

USPTO_TO_CANONICAL_FIELD = {
    "TTL": "title", "TI": "title", "ABST": "abstract", "AB": "abstract", "ACLM": "claims", "CLM": "claims",
    "CLMS": "claims", "SPEC": "description", "DETD": "description", "IN": "inventor_name", "INV": "inventor_name",
    "AN": "assignee_name", "AS": "assignee_name", "CPC": "cpc", "CPCA": "cpc", "CPCI": "cpc", "IPC": "ipc",
    "CCLS": "us_classification_ccls", "CLAS": "us_classification_text", "PN": "patent_number",
    "APP": "application_number", "DID": "document_id", "PD": "publication_date", "ISD": "issue_date",
    "AD": "application_date", "FD": "application_date", "AY": "application_year", "FY": "application_year",
    "PY": "publication_year",
}

class USPTOQueryParser: # Using the version from previous successful step
    def __init__(self):
        self.field_mapping = USPTO_TO_CANONICAL_FIELD
        self.current_expr_parser = pp.Forward()
        self.grammar = self._define_grammar()

    def _build_ast_from_infix_tokens(self, instring, loc, tokens):
        current_tokens = tokens[0]
        if isinstance(current_tokens[0], str) and len(current_tokens) == 2:
            op_str, operand_node = current_tokens[0].upper(), current_tokens[1]
            if op_str == "NOT": return BooleanOpNode(op_str, [operand_node])
            raise pp.ParseException(instring, loc, f"Unknown unary op: {op_str}")
        node = current_tokens[0]
        idx = 1
        while idx < len(current_tokens):
            op_str_full_token = current_tokens[idx]
            if isinstance(op_str_full_token, pp.ParseResults): op_str_full = op_str_full_token[0].upper()
            else: op_str_full = op_str_full_token.upper()
            right_operand = current_tokens[idx+1]
            if op_str_full in ["AND", "OR", "XOR"]: node = BooleanOpNode(op_str_full, [node, right_operand])
            elif op_str_full.startswith(("ADJ", "NEAR", "WITH", "SAME")):
                m = re.match(r"^(ADJ|NEAR|WITH|SAME)(\d*)$", op_str_full, re.I)
                if not m: raise pp.ParseException(instring, loc, f"Invalid prox op: {op_str_full}")
                op_t, dist_str = m.group(1).upper(), m.group(2)
                dist = int(dist_str) if dist_str else None
                node = ProximityOpNode(op_t, [node, right_operand], distance=dist,
                                     ordered=(op_t=="ADJ"), scope_unit={"WITH":"sentence","SAME":"paragraph"}.get(op_t))
            else: raise pp.ParseException(instring, loc, f"Unknown op: {op_str_full}")
            idx += 2
        return node

    def _make_fielded_node(self, instring, loc, tokens):
        fc_tok_list = tokens[0]
        field_code = fc_tok_list[0].upper()
        query_node_or_term = fc_tok_list[1]
        canonical_name = self.field_mapping.get(field_code, f"unknown_uspto_field_{field_code}")
        if canonical_name == "cpc" and isinstance(query_node_or_term, TermNode):
            cpc_value = query_node_or_term.value
            include_children = False
            if cpc_value.lower().endswith("/low"):
                cpc_value = cpc_value[:-4]; include_children = True
            return FieldedSearchNode(canonical_name,
                                     ClassificationNode("CPC", cpc_value, include_children=include_children),
                                     system_field_code=field_code)
        return FieldedSearchNode(canonical_name, query_node_or_term, system_field_code=field_code)

    def _make_date_node(self, instring, loc, tokens):
        expr = tokens[0]; m = re.match(r"@([A-Za-z]{2,})(=|>=|<=|>|<|<>)([\d/]+)(?:(<=)([\d/]+))?", expr)
        if m:
            fc,op,v1,op2r,v2r = m.groups(); fc=fc.upper()
            cn=self.field_mapping.get(fc,f"unknown_uspto_date_field_{fc}")
            if op2r and v2r: return DateSearchNode(cn,op,v1,date_value2=v2r,system_field_code=fc)
            return DateSearchNode(cn,op,v1,system_field_code=fc)
        return TermNode(expr)

    def _define_grammar(self):
        LPAR,RPAR,QUOTE=map(pp.Suppress,"()\"")
        op_not = pp.CaselessLiteral("NOT"); op_prox = pp.Regex(r"(ADJ|NEAR|WITH|SAME)\d*",re.I)
        op_and = pp.CaselessLiteral("AND"); op_xor = pp.CaselessLiteral("XOR"); op_or = pp.CaselessLiteral("OR")
        searchTermAtom = pp.Word(pp.alphanums + "-_/.?$*:")
        quotedStringAtom = QUOTE + pp.Combine(pp.ZeroOrMore(pp.CharsNotIn('"')|(pp.Literal('""').setParseAction(lambda:"\"")))) + QUOTE
        term = quotedStringAtom.setParseAction(lambda s,l,t: TermNode(t[0],is_phrase=True)) | \
               searchTermAtom.setParseAction(lambda s,l,t: TermNode(t[0]))
        field_keys_re = "|".join(re.escape(k) for k in self.field_mapping.keys())
        uspto_field_prefix = pp.Regex(f"({field_keys_re})/", re.I).setParseAction(lambda t: t[0].upper().replace("/", ""))
        field_content = (LPAR + self.current_expr_parser + RPAR) | term.copy()
        fielded_search = pp.Group(uspto_field_prefix + field_content).setParseAction(self._make_fielded_node)
        uspto_date_expr_regex = r"@[A-Za-z]{2,}(?:=|>=|<=|>|<|<>)\d+(?:/\d+)?(?:<=\d+(?:/\d+)?)?"
        uspto_date_search = pp.Regex(uspto_date_expr_regex).setParseAction(self._make_date_node)
        atom = fielded_search | uspto_date_search | (LPAR + self.current_expr_parser + RPAR) | term.copy()
        self.current_expr_parser <<= pp.infixNotation(atom, [
            (op_not, 1, pp.opAssoc.RIGHT, self._build_ast_from_infix_tokens),
            (op_prox, 2, pp.opAssoc.LEFT, self._build_ast_from_infix_tokens),
            (op_and, 2, pp.opAssoc.LEFT, self._build_ast_from_infix_tokens),
            (op_xor, 2, pp.opAssoc.LEFT, self._build_ast_from_infix_tokens),
            (op_or, 2, pp.opAssoc.LEFT, self._build_ast_from_infix_tokens)])
        set_kw=pp.CaselessLiteral("SET").suppress()
        set_pv=pp.Word(pp.alphanums+"_");set_pn=pp.Word(pp.alphas+"_")
        set_assign=pp.Group(set_pn+pp.Literal("=").suppress()+set_pv)
        set_cmd_opt=pp.Optional(set_kw+pp.delimitedList(set_assign,delim=",")).setResultsName("st")
        query_expr_sequence = pp.Group(pp.OneOrMore(self.current_expr_parser))
        return set_cmd_opt + pp.Optional(query_expr_sequence).setResultsName("qe_list")

    def parse(self, query_string: str) -> QueryRootNode:
        try:
            query_string_stripped = query_string.strip()
            if not query_string_stripped: return QueryRootNode(query=TermNode("__EMPTY__"))
            parsed = self.grammar.parseString(query_string_stripped, parseAll=True)
            s_dict={}; s_tok_list=parsed.get("st")
            if s_tok_list:
                if isinstance(s_tok_list, pp.ParseResults) and len(s_tok_list) > 0:
                    if isinstance(s_tok_list[0], pp.ParseResults):
                        for sg_group in s_tok_list:
                            if isinstance(sg_group, pp.ParseResults) and len(sg_group) == 2:
                                 s_dict[sg_group[0].lower()] = sg_group[1]
                    elif isinstance(s_tok_list[0], str) and len(s_tok_list) == 2:
                        s_dict[s_tok_list[0].lower()] = s_tok_list[1]
            q_ast_list_tok = parsed.get("qe_list"); q_ast: Optional[ASTNode] = None
            if q_ast_list_tok:
                actual_ast_nodes = q_ast_list_tok[0].asList()
                if len(actual_ast_nodes) > 1:
                    default_op_str = s_dict.get("defaultoperator", "AND").upper()
                    if default_op_str not in ["AND", "OR"]: default_op_str = "AND"
                    q_ast = BooleanOpNode(default_op_str, actual_ast_nodes) # type: ignore
                elif len(actual_ast_nodes) == 1: q_ast = actual_ast_nodes[0]
                else: q_ast = TermNode("__EMPTY__")
            else: q_ast = TermNode("__EMPTY_AFTER_SET__" if s_dict else "__EMPTY__")
            if q_ast is None: q_ast = TermNode("__PARSE_FAILURE_UNSPECIFIED__")
            return QueryRootNode(query=q_ast, settings=s_dict)
        except pp.ParseException as pe:
            return QueryRootNode(query=TermNode(f"PARSE_ERROR: {pe.line}(col {pe.column}) msg: {pe.msg}"))
        except Exception as e:
            return QueryRootNode(query=TermNode(f"UNEXPECTED_PARSE_ERROR: {str(e)}"))

class ASTToGoogleQueryGenerator:
    def __init__(self): pass
    def generate(self, ast_root: QueryRootNode) -> str:
        if not isinstance(ast_root, QueryRootNode): return "Error: Invalid AST root"
        return self._generate_node(ast_root.query, is_top_level_expr=True, parent_op_type=None, parent_node_instance=None)

    def _get_op_precedence(self, op_str: Optional[str]) -> int:
        if op_str is None: return -1
        if op_str in ["TERM", "DATE_EXPR", "CPC_FIELD"]: return 6
        if op_str in ["TI", "AB", "CL", "assignee", "inventor", "patent_number", "FIELD_ASSIGN"]: return 5
        if op_str == "NOT_OPERATOR" or op_str == "NOT_PREFIX": return 4
        if op_str.startswith(("ADJ", "NEAR", "WITH", "SAME")): return 3
        if op_str == "AND": return 2
        if op_str == "XOR": return 1
        if op_str == "OR": return 0
        return -2

    def _node_was_explicitly_parenthesized(self, node: ASTNode, parent_node_instance: Optional[ASTNode]) -> bool:
        # This is a placeholder for a more robust mechanism.
        # True if 'node' is Op2 in an AST structure like Op1(Left, Op2(Mid,Right))
        # where Op1 and Op2 are the same operator type (e.g. both AND).
        # This indicates user parentheses like "A AND (B AND C)".
        if parent_node_instance and isinstance(node, type(parent_node_instance)):
            if isinstance(node, BooleanOpNode) and isinstance(parent_node_instance, BooleanOpNode):
                if node.operator == parent_node_instance.operator:
                    # Check if 'node' is the right-hand operand of 'parent_node_instance' (for left-associative)
                    if len(parent_node_instance.operands) > 1 and parent_node_instance.operands[-1] is node:
                        return True
            elif isinstance(node, ProximityOpNode) and isinstance(parent_node_instance, ProximityOpNode):
                if node.operator == parent_node_instance.operator:
                    if len(parent_node_instance.terms) > 1 and parent_node_instance.terms[-1] is node:
                        return True
        return False

    def _needs_paren(self, current_op_type: Optional[str], parent_op_type: Optional[str], was_explicitly_parenthesized: bool) -> bool:
        if parent_op_type is None or current_op_type is None: return False
        if current_op_type in ["TERM", "DATE_EXPR", "CPC_FIELD", "NOT_PREFIX"]: return False
        if parent_op_type in ["TI", "AB", "CL", "assignee", "inventor", "patent_number", "FIELD_ASSIGN"]: return False
        
        parent_prec = self._get_op_precedence(parent_op_type)
        current_prec = self._get_op_precedence(current_op_type)

        if current_prec == -2 or parent_prec == -2: return False
        
        if current_prec < parent_prec: return True
        
        if current_prec == parent_prec:
            if current_op_type != parent_op_type: return True
            if was_explicitly_parenthesized: return True # A op (B op C) case
            
        return False

    def _generate_node(self, node: ASTNode, is_top_level_expr: bool = False, parent_op_type: Optional[str] = None, parent_node_instance: Optional[ASTNode] = None) -> str:
        res_str = ""; current_node_op_type = None
        was_explicitly_parenthesized = self._node_was_explicitly_parenthesized(node, parent_node_instance)

        if isinstance(node, TermNode):
            if node.value == "__EMPTY__" or node.value == "__EMPTY_AFTER_SET__": return ""
            current_node_op_type = "TERM"
            if node.is_phrase: res_str = f'"{node.value}"'
            elif node.value.upper() in ["AND","OR","NOT","NEAR","ADJ","WITH","SAME"] and not node.is_phrase: res_str = f'"{node.value}"'
            else: res_str = node.value
        elif isinstance(node, FieldedSearchNode):
            field_google = self._map_canonical_to_google_field(node.field_canonical_name)
            current_node_op_type = field_google if field_google else "FIELD_ASSIGN"
            query_str = self._generate_node(node.query, False, current_node_op_type, node)
            if field_google in ["TI", "AB", "CL"]: res_str = f"{field_google}=({query_str})"
            elif field_google == "CPC":
                cpc_val = query_str 
                if isinstance(node.query, ClassificationNode) and node.query.include_children:
                    if not cpc_val.endswith("/low"): cpc_val += "/low"
                res_str = f"CPC:{cpc_val}"
            elif field_google in ["assignee", "inventor", "patent_number"]:
                if field_google == "patent_number":
                    if not (query_str.startswith('"') and query_str.endswith('"')): query_str = f'"{query_str}"'
                elif (field_google == "assignee" or field_google == "inventor"):
                    if (' ' in query_str or '*' in query_str or '?' in query_str or '$' in query_str) and \
                       not (query_str.startswith('"') and query_str.endswith('"')): query_str = f'"{query_str}"'
                res_str = f"{field_google}:({query_str})"
            else: res_str = query_str
        elif isinstance(node, BooleanOpNode):
            current_node_op_type = node.operator.upper()
            if current_node_op_type == "NOT" and len(node.operands) == 1:
                operand_node = node.operands[0]
                operand_str = self._generate_node(operand_node, False, "NOT_OPERATOR", node)
                is_simple = isinstance(operand_node,TermNode) and not operand_node.is_phrase and " " not in operand_node.value and not (operand_str.startswith("(") and operand_str.endswith(")")) and not operand_str.startswith("-")
                if is_simple: res_str = f"-{operand_str.strip('\"')}"; current_node_op_type = "NOT_PREFIX"
                else:
                    is_grouped = (operand_str.startswith("(") and operand_str.endswith(")")) and not (isinstance(operand_node,FieldedSearchNode) or (isinstance(operand_node,TermNode) and operand_node.is_phrase and ' ' in operand_node.value)or (isinstance(operand_node,DateSearchNode) and ' ' in operand_str ))
                    if is_grouped: res_str = f"NOT {operand_str}"
                    else: res_str = f"NOT ({operand_str})"
            else: 
                op_strs = [self._generate_node(op, False, current_node_op_type, node) for op in node.operands]
                op_strs = [s for s in op_strs if s]
                if not op_strs: return ""
                if len(op_strs) == 1 and current_node_op_type != "NOT" : return op_strs[0]
                joiner = f" {current_node_op_type} "
                if current_node_op_type == "AND" and is_top_level_expr:
                    use_space = False
                    if node.operands:
                        is_blocks = all(isinstance(op, (DateSearchNode, FieldedSearchNode)) for op in node.operands)
                        if is_blocks and len(node.operands) > 1: use_space = True
                        elif len(node.operands) == 2:
                            n1,n2 = node.operands[0],node.operands[1]
                            b1,b2 = isinstance(n1,(DateSearchNode,FieldedSearchNode)), isinstance(n2,(DateSearchNode,FieldedSearchNode))
                            c1,c2 = isinstance(n1,(BooleanOpNode,ProximityOpNode)), isinstance(n2,(BooleanOpNode,ProximityOpNode))
                            if (b1 and (b2 or c2)) or (b2 and (b1 or c1)): use_space = True
                    if use_space: joiner = " "
                res_str = joiner.join(op_strs)
        elif isinstance(node, ProximityOpNode):
            current_node_op_type = node.operator.upper()
            terms_s = [self._generate_node(t, False, current_node_op_type, node) for t in node.terms]
            terms_s = [ts for ts in terms_s if ts]
            if not terms_s: return ""
            if len(terms_s) == 1: return terms_s[0]
            op_key = current_node_op_type
            if node.distance is not None and current_node_op_type in ["ADJ", "NEAR"]:
                op_key = f"{current_node_op_type}{node.distance}"
            res_str = f" {op_key} ".join(terms_s)
        elif isinstance(node, ClassificationNode):
            current_node_op_type = "TERM" 
            res_str = node.value.replace("/", "") 
        elif isinstance(node, DateSearchNode):
            current_node_op_type = "DATE_EXPR"; type_map = {"publication_date":"publication","issue_date":"publication","application_date":"filing","priority_date":"priority"}
            google_date_type = type_map.get(node.field_canonical_name); parts = []; date_val_fmt = node.date_value.replace("-","").replace("/","")
            if not google_date_type:
                if node.field_canonical_name in ["application_year","publication_year"]:
                    yr = date_val_fmt; base = "filing" if "app" in node.field_canonical_name else "publication"
                    if node.operator == "=": parts.extend([f"after:{base}:{yr}0101",f"before:{base}:{yr}1231"])
                    elif node.operator == ">=": parts.append(f"after:{base}:{yr}0101")
                    elif node.operator == "<=": parts.append(f"before:{base}:{yr}1231")
                    elif node.operator == ">": parts.append(f"after:{base}:{yr}1231")
                    elif node.operator == "<": parts.append(f"before:{base}:{yr}0101")
                    else: parts.append(f"Error:UnhandledYearOp({node.operator})")
                else: parts.append(f"Error:UnknownGoogleDateType({node.field_canonical_name})")
            else:
                if node.date_value2:
                    d2fmt = node.date_value2.replace("-","").replace("/","")
                    if node.operator == ">=": parts.append(f"after:{google_date_type}:{date_val_fmt}")
                    parts.append(f"before:{google_date_type}:{d2fmt}")
                else:
                    if node.operator == ">=": parts.append(f"after:{google_date_type}:{date_val_fmt}")
                    elif node.operator == "<=": parts.append(f"before:{google_date_type}:{date_val_fmt}")
                    elif node.operator == "=": parts.extend([f"after:{google_date_type}:{date_val_fmt}",f"before:{google_date_type}:{date_val_fmt}"])
                    elif node.operator == ">": parts.append(f"after:{google_date_type}:{date_val_fmt}")
                    elif node.operator == "<": parts.append(f"before:{google_date_type}:{date_val_fmt}")
                    else: parts.append(f"Error:UnhandledDateOp({node.operator})")
            res_str = " ".join(p for p in parts if p and not p.startswith("Error:"))
            if any(e in res_str for e in ["Error:Unha","Error:Unkn","Error:Unha"]): return res_str
        else: res_str = f"Error:UnhandledASTNode({type(node).__name__})"

        if not is_top_level_expr and isinstance(node, (BooleanOpNode, ProximityOpNode)):
            if not (parent_op_type in ["TI", "AB", "CL", "assignee", "inventor", "patent_number", "FIELD_ASSIGN"]):
                # This is the aggressive parenthesizing for non-top-level operators not directly under a field.
                # It relies on _needs_paren to be correct for more subtle cases if this is too broad.
                # For now, let's try this simpler approach.
                # The _needs_paren call was: self._needs_paren(current_node_op_type, parent_op_type, was_explicitly_parenthesized)
                # If this simple rule is too aggressive, we revert to the _needs_paren call.
                if not (res_str.startswith("(") and res_str.endswith(")")):
                    return f"({res_str})"
        return res_str

    def _map_canonical_to_google_field(self, canonical_name: str) -> Optional[str]:
        if canonical_name == "title": return "TI";  
        if canonical_name == "abstract": return "AB"
        if canonical_name == "claims": return "CL"; 
        if canonical_name == "cpc": return "CPC"
        if canonical_name == "assignee_name": return "assignee"; 
        if canonical_name == "inventor_name": return "inventor"
        if canonical_name == "patent_number": return "patent_number"; return None

def convert_query(query_string: str,
                  source_format: Literal["google", "uspto"],
                  target_format: Literal["google", "uspto"]) -> Dict[str, Union[str, None, Dict[str, Any]]]:
    if not query_string.strip(): return {"query": "", "error": None, "settings": {}}
    ast_root: Optional[QueryRootNode] = None; parser_error: Optional[str] = None; parsed_settings: Dict[str, Any] = {}
    try:
        if source_format == "google": return {"query":None,"error":"Google to AST parser not yet implemented.","settings":{}}
        elif source_format == "uspto":
            parser = USPTOQueryParser(); ast_root = parser.parse(query_string)
            if isinstance(ast_root.query,TermNode) and ("PARSE_ERROR" in ast_root.query.value or "UNEXPECTED_PARSE_ERROR" in ast_root.query.value):
                parser_error = ast_root.query.value; ast_root = None
            elif ast_root: parsed_settings = ast_root.settings
        else: return {"query":None,"error":f"Unsupported source format: {source_format}","settings":{}}
    except Exception as e: parser_error = f"Parsing failed with exception: {e}" # type: ignore
    if parser_error: return {"query":None,"error":f"Error parsing {source_format} query '{query_string}': {parser_error}","settings":parsed_settings}
    if not ast_root: return {"query":None,"error":f"Unknown error creating AST from {source_format} query: {query_string}","settings":parsed_settings}
    output_query: Optional[str] = None; generator_error: Optional[str] = None
    try:
        if target_format == "google":
            generator = ASTToGoogleQueryGenerator(); temp_ast_root = ast_root
            if ast_root.settings.get("defaultoperator","").upper() == "OR" and \
               isinstance(ast_root.query, BooleanOpNode) and ast_root.query.operator == "OR":
                likely_from_default_op = all(isinstance(op, (FieldedSearchNode,DateSearchNode,TermNode)) for op in ast_root.query.operands)
                if likely_from_default_op and len(ast_root.query.operands) > 1:
                    modified_query = BooleanOpNode("AND", ast_root.query.operands)
                    temp_ast_root = QueryRootNode(query=modified_query, settings=ast_root.settings)
            output_query = generator.generate(temp_ast_root)
        elif target_format == "uspto": return {"query":None,"error":"AST to USPTO generator not yet implemented.","settings":parsed_settings}
        else: return {"query":None,"error":f"Unsupported target format: {target_format}","settings":parsed_settings}
        if isinstance(output_query, str) and \
           ("Error:" in output_query or "UnhandledASTNode" in output_query or "Unsupported" in output_query or "UnknownGoogleDateType" in output_query) :
            generator_error = output_query; output_query = None
    except Exception as e: generator_error = f"Generation failed with exception: {e}" # type: ignore
    if generator_error: return {"query":None,"error":f"Error generating {target_format} query: {generator_error}","settings":parsed_settings}
    return {"query": output_query, "error": None, "settings": parsed_settings}