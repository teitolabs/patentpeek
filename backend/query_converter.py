# query_converter.py

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
            # Add other unary operators if any
            raise pp.ParseException(instring, loc, f"Unknown unary op: {op_str}")
        
        # Binary operator
        node = current_tokens[0]
        idx = 1
        while idx < len(current_tokens):
            op_str_full_token = current_tokens[idx] # This is the operator token itself
            # Operator token might be a string or a ParseResults if it's from a Regex like op_prox
            if isinstance(op_str_full_token, pp.ParseResults):
                op_str_full = op_str_full_token[0].upper() # Regex op_prox yields ParseResults(["ADJ5"])
            else:
                op_str_full = op_str_full_token.upper() # Simple literal ops like "AND"

            right_operand = current_tokens[idx+1]
            
            if op_str_full in ["AND", "OR", "XOR"]:
                node = BooleanOpNode(op_str_full, [node, right_operand])
            elif op_str_full.startswith(("ADJ", "NEAR", "WITH", "SAME")): # Proximity
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
        fc_tok_list = tokens[0] # pyparsing wraps Group in an outer list
        field_code_with_slash = fc_tok_list[0] # e.g., "TTL/"
        field_code = field_code_with_slash.upper().replace("/", "")
        query_node_or_term = fc_tok_list[1] # This is already an ASTNode (TermNode or nested expression)
        
        canonical_name = self.field_mapping.get(field_code, f"unknown_uspto_field_{field_code}")

        if canonical_name == "cpc" and isinstance(query_node_or_term, TermNode):
            cpc_value = query_node_or_term.value
            include_children = False
            if cpc_value.lower().endswith("/low"): # Check for USPTO specific /low suffix
                cpc_value = cpc_value[:-4] # Remove /low
                include_children = True
            # Store the cleaned CPC value and include_children flag in a ClassificationNode
            return FieldedSearchNode(canonical_name, 
                                     ClassificationNode("CPC", cpc_value, include_children=include_children), 
                                     system_field_code=field_code)
        
        # For other fields, or if CPC content is complex (already an AST node), just pass through
        return FieldedSearchNode(canonical_name, query_node_or_term, system_field_code=field_code)

    def _make_date_node(self, instring, loc, tokens):
        full_match_str = tokens[0] # The full matched date string, e.g., "@PD>=20230101"
        # Regex to parse the components of the date string
        m = re.match(r"@([A-Za-z]{2,})(=|>=|<=|>|<|<>)([0-9/]{4,10})(?:(<=)([0-9/]{4,10}))?", full_match_str)
        if m:
            field_code_str, op1_str, date_val1_str, op2_literal_str, date_val2_str = m.groups()
            field_code_upper = field_code_str.upper()
            canonical_name = self.field_mapping.get(field_code_upper, f"unknown_uspto_date_field_{field_code_upper}")
            
            # Handle date range like @PD>=YYYYMMDD<=YYYYMMDD
            if op2_literal_str and date_val2_str: # op2_literal_str would be "<="
                return DateSearchNode(canonical_name, op1_str, date_val1_str, 
                                      date_value2=date_val2_str, system_field_code=field_code_upper)
            else: # Single date comparison
                return DateSearchNode(canonical_name, op1_str, date_val1_str, system_field_code=field_code_upper)
        
        # Fallback if regex doesn't match (should ideally be caught by grammar)
        return TermNode(full_match_str) # Treat as a simple term if parsing fails


    def _define_grammar(self):
        LPAR,RPAR,QUOTE=map(pp.Suppress,"()\"")
        op_not = pp.CaselessLiteral("NOT"); op_prox = pp.Regex(r"(ADJ|NEAR|WITH|SAME)\d*",re.I)
        op_and = pp.CaselessLiteral("AND"); op_xor = pp.CaselessLiteral("XOR"); op_or = pp.CaselessLiteral("OR")
        
        # Define characters allowed in a search term atom (unquoted)
        # Added ':' for things like H04L29:06
        searchTermAtomChars = pp.alphanums + "-_/.?$*:'" 
        searchTermAtom = pp.Word(searchTermAtomChars)

        # Quoted string, allows "" to represent a single quote inside
        quotedStringAtom = QUOTE + pp.Combine(pp.ZeroOrMore(pp.CharsNotIn('"')|(pp.Literal('""').setParseAction(lambda:"\"")))) + QUOTE
        
        term = quotedStringAtom.setParseAction(lambda s,l,t: TermNode(t[0],is_phrase=True)) | \
               searchTermAtom.setParseAction(lambda s,l,t: TermNode(t[0]))
        
        # Field prefixes like TTL/, ABST/, CPC/
        # Using Regex to capture the field code part before the slash
        generic_field_prefix_re = r"([a-zA-Z]{2,4})/" # Captures like "TTL", "ABST", "CPC"
        uspto_field_prefix = pp.Regex(generic_field_prefix_re, re.I) # Case-insensitive

        # Content of a fielded search can be a parenthesized expression or a simple term/phrase
        field_content = (LPAR + self.current_expr_parser + RPAR) | term.copy()
        fielded_search = pp.Group(uspto_field_prefix + field_content).setParseAction(self._make_fielded_node)
        
        # Date search patterns like @PD>=20220101 or @AY=2022
        # Regex to capture the whole date expression for _make_date_node
        _date_val_str_pattern = r"[0-9/]{4,10}" # Date value like 20220101 or 2022/01/01 or year 2022
        uspto_date_search_regex = rf"@(?:[A-Za-z]{{2,}})(?:=|>=|<=|>|<|<>)(?:{_date_val_str_pattern})(?:<=(?:{_date_val_str_pattern}))?"
        uspto_date_search = pp.Regex(uspto_date_search_regex).setParseAction(self._make_date_node)

        # Atom: the basic building block of an expression
        atom = fielded_search | uspto_date_search | (LPAR + self.current_expr_parser + RPAR) | term.copy()
        
        # Define operator precedence and associativity for infix notation
        # Higher precedence operators are listed first or have more specific definitions.
        # USPTO typically: NOT > ADJ/NEAR/WITH/SAME > AND > XOR > OR (left-associative for binary)
        self.current_expr_parser <<= pp.infixNotation(atom, [
            (op_not, 1, pp.opAssoc.RIGHT, self._build_ast_from_infix_tokens),
            (op_prox, 2, pp.opAssoc.LEFT, self._build_ast_from_infix_tokens), # ADJ, NEAR, WITH, SAME
            (op_and, 2, pp.opAssoc.LEFT, self._build_ast_from_infix_tokens),
            (op_xor, 2, pp.opAssoc.LEFT, self._build_ast_from_infix_tokens), # XOR same as AND? Check USPTO manual.
            (op_or, 2, pp.opAssoc.LEFT, self._build_ast_from_infix_tokens)]) # OR is often lowest.
        
        # SET command parsing: SET Plural=ON,DefaultOperator=OR
        set_kw=pp.CaselessLiteral("SET").suppress()
        set_pv=pp.Word(pp.alphanums+"_") # parameter value
        set_pn=pp.Word(pp.alphas+"_")    # parameter name
        set_assign=pp.Group(set_pn+pp.Literal("=").suppress()+set_pv) # e.g. ["Plural", "ON"]
        # Optional SET command with one or more assignments
        set_cmd_opt=pp.Optional(set_kw+pp.delimitedList(set_assign,delim=",")).setResultsName("st")
        
        # A query can be just a SET command, or SET + expression, or just expression
        # The main query expression part
        query_expr_sequence = pp.Group(pp.OneOrMore(self.current_expr_parser)) # Handles implicit AND/OR between terms if no operator
        
        # Full grammar: optional SET command followed by optional query expression sequence
        return set_cmd_opt + pp.Optional(query_expr_sequence).setResultsName("qe_list")


    def parse(self, query_string: str) -> QueryRootNode:
        s_dict_local: Dict[str, Any] = {} 
        try:
            query_string_stripped = query_string.strip()
            if not query_string_stripped: return QueryRootNode(query=TermNode("__EMPTY__"))
            
            parsed = self.grammar.parseString(query_string_stripped, parseAll=True)
            
            s_tok_list=parsed.get("st") 
            if s_tok_list: # If SET command was present
                # s_tok_list might be ParseResults([GroupA, GroupB]) or Group if single assign
                if isinstance(s_tok_list, pp.ParseResults) and len(s_tok_list) > 0:
                    # If s_tok_list contains ParseResults (multiple assignments like ["P","ON"], ["D","OR"])
                    if isinstance(s_tok_list[0], pp.ParseResults):
                        for sg_group in s_tok_list: # sg_group is like ParseResults(['Plural', 'ON'])
                            if isinstance(sg_group, pp.ParseResults) and len(sg_group) == 2:
                                 s_dict_local[sg_group[0].lower()] = sg_group[1]
                    # If s_tok_list directly contains the single assignment key-value pair
                    elif isinstance(s_tok_list[0], str) and len(s_tok_list) == 2: # Single like ["P", "ON"]
                        s_dict_local[s_tok_list[0].lower()] = s_tok_list[1]

            q_ast_list_tok = parsed.get("qe_list"); q_ast: Optional[ASTNode] = None

            if q_ast_list_tok:
                # q_ast_list_tok is expected to be a Group containing a list of ASTNodes
                # due to pp.Group(pp.OneOrMore(self.current_expr_parser))
                actual_ast_nodes = q_ast_list_tok[0].asList() 

                if len(actual_ast_nodes) > 1: # Multiple expressions implies default operator
                    default_op_str = s_dict_local.get("defaultoperator", "AND").upper()
                    if default_op_str not in ["AND", "OR"]: default_op_str = "AND" # Enforce valid default
                    q_ast = BooleanOpNode(default_op_str, actual_ast_nodes) # type: ignore
                elif len(actual_ast_nodes) == 1: q_ast = actual_ast_nodes[0]
                else: q_ast = TermNode("__EMPTY__") # Should not happen if qe_list is present and OneOrMore worked
            else: # No query expression part, only SET or empty string
                q_ast = TermNode("__EMPTY_AFTER_SET__" if s_dict_local else "__EMPTY__")

            if q_ast is None: # Should ideally not be reached if logic above is sound
                q_ast = TermNode("__PARSE_FAILURE_UNSPECIFIED__")

            return QueryRootNode(query=q_ast, settings=s_dict_local)
        except pp.ParseException as pe:
            error_query_node = TermNode(f"PARSE_ERROR: {pe.line}(col {pe.column}) msg: {pe.msg}")
            return QueryRootNode(query=error_query_node, settings=s_dict_local) 
        except Exception as e:
            # import traceback
            # print(f"USPTO PARSE EXCEPTION: {e}\n{traceback.format_exc()}")
            return QueryRootNode(query=TermNode(f"UNEXPECTED_PARSE_ERROR: {str(e)}"), settings=s_dict_local)

class ASTToGoogleQueryGenerator:
    def __init__(self): pass

    def generate(self, ast_root: QueryRootNode) -> str:
        if not isinstance(ast_root, QueryRootNode): return "Error: Invalid AST root"
        # The main call to _generate_node for the root of the query.
        # is_top_level_expr=True indicates this is the outermost expression.
        return self._generate_node(ast_root.query, is_top_level_expr=True, parent_op_type=None, parent_node_instance=None)

    def _map_canonical_to_google_field(self, canonical_name: str) -> Optional[str]:
        if canonical_name == "title": return "TI" 
        if canonical_name == "abstract": return "AB"
        if canonical_name == "claims": return "CL"
        if canonical_name == "description": return None # Google full-text, no direct SPEC/DETD field
        if canonical_name == "cpc": return "CPC"
        if canonical_name == "ipc": return "IPC" 
        if canonical_name == "assignee_name": return "assignee" 
        if canonical_name == "inventor_name": return "inventor"
        if canonical_name == "patent_number": return "patent_number"
        # Other fields like us_classification_ccls, document_id, application_number are not directly mapped
        return None

    def _generate_node(self, node: ASTNode, is_top_level_expr: bool = False, parent_op_type: Optional[str] = None, parent_node_instance: Optional[ASTNode] = None) -> str:
        res_str = "" 
        current_node_op_type = None # The operator type of the current node itself

        if isinstance(node, TermNode):
            current_node_op_type = "TERM"
            if node.value == "__EMPTY__" or node.value == "__EMPTY_AFTER_SET__": res_str = ""
            elif node.is_phrase: res_str = f'"{node.value}"'
            elif node.value.upper() in ["AND","OR","NOT","NEAR","ADJ","WITH","SAME"] and not node.is_phrase:
                res_str = f'"{node.value}"' # Quote keywords if they are terms
            else: res_str = node.value
        
        elif isinstance(node, FieldedSearchNode):
            if node.field_canonical_name == "application_number": # Specific error for this unhandled field
                return f"Error:UnhandledASTNode({type(node).__name__})"

            field_google = self._map_canonical_to_google_field(node.field_canonical_name)
            # current_node_op_type will be like "TI", "CPC", or "FIELD_ASSIGN" if unmapped
            current_node_op_type = field_google if field_google else "FIELD_ASSIGN" 
            
            # The child query's parent_op_type is current_node_op_type (e.g., "TI")
            # The child query's parent_node_instance is the current FieldedSearchNode 'node'
            query_str = self._generate_node(node.query, False, current_node_op_type, node)
            
            if field_google in ["TI", "AB", "CL"]: res_str = f"{field_google}=({query_str})"
            elif field_google == "CPC" or field_google == "IPC":
                val_transformed = query_str # query_str is result of _generate_node(node.query,...)
                # If node.query was ClassificationNode, its _generate_node removed slashes.
                # If node.query was TermNode (e.g. direct input like CPC/H01L/00), remove slashes from term value.
                if isinstance(node.query, TermNode):
                    val_transformed = node.query.value.replace("/", "")
                elif isinstance(node.query, ClassificationNode): # Already cleaned by its own _generate_node
                    val_transformed = query_str # which is node.query.value.replace("/","") from its generation

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
            else: # Unmapped field (field_google is None), or field that doesn't use X=(Y) syntax (e.g. CCLS)
                res_str = query_str 
        
        elif isinstance(node, BooleanOpNode):
            operator_upper = node.operator.upper()
            current_node_op_type = operator_upper # Base type for AND/OR/XOR or NOT_OPERATOR

            if operator_upper == "NOT" and len(node.operands) == 1:
                operand_node = node.operands[0]
                # Child's parent_op_type is "NOT_OPERATOR", parent_node_instance is current 'NOT' node
                operand_str = self._generate_node(operand_node, False, "NOT_OPERATOR", node) 
                
                is_simple_term_for_not_prefix = isinstance(operand_node,TermNode) and \
                                 not operand_node.is_phrase and \
                                 " " not in operand_node.value and \
                                 not (operand_str.startswith("(") and operand_str.endswith(")")) and \
                                 not operand_str.startswith("-") # Avoid --term

                if is_simple_term_for_not_prefix:
                    res_str = f"-{operand_str.strip('\"')}" # Strip quotes if keyword was term, e.g. -"AND"
                    current_node_op_type = "NOT_PREFIX" # More specific type for parenthesizing logic
                else:
                    # Test "AST to Google: NOT a phrase" expects NOT ("legacy system")
                    # If operand_str itself is already a quoted phrase, wrap it in parens for NOT.
                    if isinstance(operand_node, TermNode) and operand_node.is_phrase: # operand_str is like "\"text\""
                         res_str = f"NOT ({operand_str})" 
                    # If operand_str is already a fully formed block like TI=(foo) or (A AND B)
                    elif (operand_str.startswith("(") and operand_str.endswith(")")) or \
                         (isinstance(operand_node, FieldedSearchNode) and '=' in operand_str and '(' in operand_str and ')' in operand_str):
                        res_str = f"NOT {operand_str}"
                    else: # Other complex operands for NOT, wrap them
                        res_str = f"NOT ({operand_str})"
                    # current_node_op_type remains "NOT" or "NOT_OPERATOR"
            else: # AND, OR, XOR
                # current_node_op_type is already operator_upper (e.g. "AND")
                # Operands' parent_op_type is current_node_op_type, parent_node_instance is current node
                op_strs = [self._generate_node(op, False, current_node_op_type, node) for op in node.operands]
                op_strs = [s for s in op_strs if s] # Filter out empty strings

                if not op_strs: return "" # If all operands are empty, return empty
                
                # If a BooleanOp (AND, OR, XOR) simplifies to a single operand, return that operand's string directly.
                # The parenthesizing for that single operand would have been handled in its own call.
                if len(op_strs) == 1: # No "current_node_op_type != "NOT"" check needed here, already in non-NOT branch
                    return op_strs[0] 
                
                joiner = f" {current_node_op_type} " # Default joiner " AND ", " OR ", " XOR "
                if current_node_op_type == "AND" and is_top_level_expr: # Special joiner for top-level AND
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
            # current_node_op_type includes distance for ADJ/NEAR for parenthesizing logic
            if node.distance is not None and base_op_type in ["ADJ", "NEAR"]:
                current_node_op_type = f"{base_op_type}{node.distance}"
            else:
                current_node_op_type = base_op_type
            
            # Terms' parent_op_type is current_node_op_type (e.g. "ADJ5")
            # parent_node_instance is the current ProximityOpNode 'node'
            terms_s = [self._generate_node(t, False, current_node_op_type, node) for t in node.terms]
            terms_s = [ts for ts in terms_s if ts] # Filter out empty strings

            if not terms_s: return ""
            if len(terms_s) == 1: # e.g. ADJ(A) -> A
                return terms_s[0] 
            
            # For joining, use the operator string which includes distance if applicable (ADJ5, NEAR10)
            # This current_node_op_type is what we determined (e.g. ADJ5, WITH)
            joiner_op_str = current_node_op_type 
            res_str = f" {joiner_op_str} ".join(terms_s)

        elif isinstance(node, ClassificationNode): # This is typically a child of FieldedSearchNode(CPC,...) or FieldedSearchNode(IPC,...)
            # current_node_op_type will be specific like "CPC_FIELD" or "IPC_FIELD"
            if node.scheme == "CPC": current_node_op_type = "CPC_FIELD"
            elif node.scheme == "IPC": current_node_op_type = "IPC_FIELD"
            else: current_node_op_type = "TERM" # Fallback for other schemes like USPC, CCLS if passed raw
            res_str = node.value.replace("/", "") # Ensure slashes are removed
        
        elif isinstance(node, DateSearchNode):
            current_node_op_type = "DATE_EXPR"
            type_map = {"publication_date":"publication","issue_date":"publication",
                        "application_date":"filing","priority_date":"priority"}
            google_date_type = type_map.get(node.field_canonical_name)
            parts = []
            date_val_fmt = node.date_value.replace("/","") # Remove slashes from date values

            if not google_date_type: 
                if node.field_canonical_name in ["application_year", "publication_year"]:
                    year_val1 = date_val_fmt 
                    year_val2 = node.date_value2.replace("/","") if node.date_value2 else None 
                    base_type = "filing" if "application" in node.field_canonical_name else "publication"
                    
                    if node.operator == "=":
                        parts.extend([f"after:{base_type}:{year_val1}0101", f"before:{base_type}:{year_val1}1231"])
                    elif node.operator == ">=" and year_val2: # year_val2 implies node.date_value2 was present
                        parts.extend([f"after:{base_type}:{year_val1}0101", f"before:{base_type}:{year_val2}1231"])
                    elif node.operator == ">=": parts.append(f"after:{base_type}:{year_val1}0101") 
                    elif node.operator == "<=": parts.append(f"before:{base_type}:{year_val1}1231") 
                    elif node.operator == ">": parts.append(f"after:{base_type}:{year_val1}1231") 
                    elif node.operator == "<": parts.append(f"before:{base_type}:{year_val1}0101") 
                    else: parts.append(f"Error:UnhandledYearOp({node.operator})")
                else: parts.append(f"Error:UnknownGoogleDateType({node.field_canonical_name})")
            else: # Standard date fields (PD, AD, ISD, PRD)
                date_val1_fmt_google = date_val_fmt 
                if node.date_value2: # Range date1 to date2 (USPTO format @FD>=d1<=d2)
                    date_val2_fmt_google = node.date_value2.replace("/","") 
                    if node.operator == ">=" : parts.append(f"after:{google_date_type}:{date_val1_fmt_google}")
                    parts.append(f"before:{google_date_type}:{date_val2_fmt_google}") # Second part always before
                else: # Single date comparison
                    if node.operator == ">=" : parts.append(f"after:{google_date_type}:{date_val1_fmt_google}")
                    elif node.operator == "<=" : parts.append(f"before:{google_date_type}:{date_val1_fmt_google}")
                    elif node.operator == "=": # Exact date
                        parts.extend([f"after:{google_date_type}:{date_val1_fmt_google}", f"before:{google_date_type}:{date_val1_fmt_google}"])
                    elif node.operator == ">" : # Strictly after (Google 'after' is inclusive of start of day)
                        parts.append(f"after:{google_date_type}:{date_val1_fmt_google}") 
                    elif node.operator == "<" : # Strictly before (Google 'before' is inclusive of end of day)
                        parts.append(f"before:{google_date_type}:{date_val1_fmt_google}")
                    else: parts.append(f"Error:UnhandledDateOp({node.operator})")
            
            res_str = " ".join(p for p in parts if p and not p.startswith("Error:"))
            if any(e_msg in res_str for e_msg in ["Error:UnhandledYearOp","Error:UnknownGoogleDateType","Error:UnhandledDateOp"]):
                return res_str # Return error string directly
        else: 
            return f"Error:UnhandledASTNode({type(node).__name__})" # Should not happen with complete AST

        # Final parenthesizing step:
        # Wrap BooleanOpNode or ProximityOpNode in parentheses if they are not the top-level expression
        # AND their parent isn't a field type that already provides grouping (like TI=(...)).
        if not is_top_level_expr and res_str: # Only apply to non-top-level, non-empty results
            if isinstance(node, (BooleanOpNode, ProximityOpNode)):
                # current_node_op_type should have been set correctly for Boolean/Proximity nodes
                if current_node_op_type != "NOT_PREFIX": # -term (NOT_PREFIX) should not become (-term)
                    
                    # Check if the parent operation inherently groups its content.
                    # Examples: TI=(content), CPC:content, NOT (content)
                    # Here, 'content' is the current 'node'. 'parent_op_type' refers to TI, CPC, NOT_OPERATOR.
                    parent_provides_grouping = parent_op_type in [
                        "TI", "AB", "CL", "assignee", "inventor", "patent_number", 
                        "FIELD_ASSIGN", # Generic field assignment
                        "CPC", "IPC",   # Classification field assignments
                        "NOT_OPERATOR"  # If current node is operand of NOT, NOT provides grouping like NOT (operand)
                    ]
                    
                    if not parent_provides_grouping:
                        # Avoid double parenthesizing if res_str is already like "(...)"
                        # This can happen if internal logic of an op (like complex NOT) adds parens.
                        if not (res_str.startswith("(") and res_str.endswith(")")):
                            return f"({res_str})"
        
        return res_str

def convert_query(query_string: str,
                  source_format: Literal["google", "uspto"],
                  target_format: Literal["google", "uspto"]) -> Dict[str, Union[str, None, Dict[str, Any]]]:
    s_dict_local_for_convert: Dict[str, Any] = {} 
    if not query_string.strip(): return {"query": "", "error": None, "settings": {}}
    
    ast_root: Optional[QueryRootNode] = None; parser_error: Optional[str] = None
    try:
        if source_format == "google": 
            return {"query":None,"error":"Google to AST parser not yet implemented.","settings":{}}
        elif source_format == "uspto":
            parser = USPTOQueryParser(); ast_root = parser.parse(query_string)
            s_dict_local_for_convert = ast_root.settings if ast_root else {} # Get settings from parsed AST
            if ast_root and isinstance(ast_root.query,TermNode) and \
               ("PARSE_ERROR" in ast_root.query.value or "UNEXPECTED_PARSE_ERROR" in ast_root.query.value):
                parser_error = ast_root.query.value; ast_root = None # Prevent further processing
        else: 
            return {"query":None,"error":f"Unsupported source format: {source_format}","settings":{}}
    except Exception as e:
        # import traceback # For debugging
        # print(f"CONVERT_QUERY PARSE EXCEPTION: {e}\n{traceback.format_exc()}")
        parser_error = f"Parsing failed with exception: {e}" 
    
    final_settings = s_dict_local_for_convert # Settings from parser (SET command)
    if ast_root and ast_root.settings: # This might be redundant if parser always puts settings in s_dict_local
        final_settings.update(ast_root.settings)


    if parser_error: 
        return {"query":None,"error":f"Error parsing {source_format} query '{query_string}': {parser_error}","settings":final_settings}
    if not ast_root: # Should be caught by parser_error if parsing failed
        return {"query":None,"error":f"Unknown error creating AST from {source_format} query: {query_string}","settings":final_settings}
    
    output_query: Optional[str] = None; generator_error: Optional[str] = None
    try:
        if target_format == "google":
            generator = ASTToGoogleQueryGenerator()
            temp_ast_root = ast_root # Use the successfully parsed AST

            # Handle USPTO's "DefaultOperator=OR term1 term2" for Google conversion
            # If USPTO default is OR, and top AST is OR of simple items, Google often implies AND for space-separation.
            if final_settings.get("defaultoperator","").upper() == "OR" and \
               isinstance(temp_ast_root.query, BooleanOpNode) and \
               temp_ast_root.query.operator == "OR":
                
                operands = temp_ast_root.query.operands
                is_likely_default_or = all(
                    isinstance(op, (TermNode, FieldedSearchNode, DateSearchNode, ClassificationNode)) for op in operands
                )
                
                if is_likely_default_or and len(operands) > 1:
                    # Convert top-level OR (from USPTO default) to AND for Google style.
                    modified_query_ast = BooleanOpNode("AND", operands)
                    temp_ast_root = QueryRootNode(query=modified_query_ast, settings=final_settings)
            
            output_query = generator.generate(temp_ast_root)

        elif target_format == "uspto": 
            return {"query":None,"error":"AST to USPTO generator not yet implemented.","settings":final_settings}
        else: 
            return {"query":None,"error":f"Unsupported target format: {target_format}","settings":final_settings}
        
        # Check for error strings embedded in the output by the generator
        if isinstance(output_query, str) and \
           ("Error:" in output_query or "UnhandledASTNode" in output_query or \
            "Unsupported" in output_query or "UnknownGoogleDateType" in output_query or \
            "UnhandledYearOp" in output_query or "UnhandledDateOp" in output_query) :
            generator_error = output_query; output_query = None # Set output to None if it's an error message

    except Exception as e:
        # import traceback # For debugging
        # print(f"CONVERT_QUERY GENERATE EXCEPTION: {e}\n{traceback.format_exc()}")
        generator_error = f"Generation failed with exception: {e}"
    
    if generator_error: 
        return {"query":None,"error":f"Error generating {target_format} query: {generator_error}","settings":final_settings}
    
    return {"query": output_query, "error": None, "settings": final_settings}