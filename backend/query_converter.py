# query_converter.py

from typing import List, Optional, Literal, Union, Dict, Any
import pyparsing as pp
import re

# --- 1. Abstract Syntax Tree (AST) Definition ---
class ASTNode:
    def __init__(self):
        pass 

    def __eq__(self, other):
        if type(other) is type(self):
            return all(getattr(self, k, None) == getattr(other, k, None) for k in self.get_compare_attrs())
        return False

    def get_compare_attrs(self):
        # Subclasses should override if specific attributes need custom comparison or should be ignored.
        return [k for k, v in self.__dict__.items() if not k.startswith('_')]

    def __repr__(self):
        attrs = {k: v for k, v in self.__dict__.items() if not k.startswith('_') and v is not None}
        return f"{self.__class__.__name__}({', '.join(f'{k}={v!r}' for k, v in attrs.items())})"

    def to_dict(self) -> Dict[str, Any]:
        data = {'node_type': self.__class__.__name__}
        for key, value in self.__dict__.items():
            if key.startswith('_'):
                continue
            if isinstance(value, ASTNode):
                data[key] = value.to_dict()
            elif isinstance(value, list) and all(isinstance(item, ASTNode) for item in value):
                data[key] = [item.to_dict() for item in value]
            else:
                data[key] = value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ASTNode':
        node_type_str = data.pop('node_type', None)
        if not node_type_str:
            raise ValueError("Missing 'node_type' in AST data for deserialization")
        
        target_class = globals().get(node_type_str) 
        if not target_class or not issubclass(target_class, ASTNode):
            raise ValueError(f"Unknown or invalid AST node_type: {node_type_str}")
        
        processed_args = {}
        for key, value in data.items():
            if isinstance(value, dict) and 'node_type' in value:
                processed_args[key] = ASTNode.from_dict(value)
            elif isinstance(value, list) and value and isinstance(value[0], dict) and 'node_type' in value[0]:
                processed_args[key] = [ASTNode.from_dict(item) for item in value]
            else:
                processed_args[key] = value
        
        return target_class(**processed_args)

class TermNode(ASTNode):
    def __init__(self, value: str, is_phrase: bool = False, has_wildcard: Optional[bool] = None):
        super().__init__()
        self.value = value
        self.is_phrase = is_phrase
        if has_wildcard is None:
            self.has_wildcard = bool(re.search(r'[\?\*\$]', value)) if value else False
        else:
            self.has_wildcard = has_wildcard
    def get_compare_attrs(self): return ['value', 'is_phrase', 'has_wildcard']

class ClassificationNode(ASTNode):
    def __init__(self, scheme: Literal["CPC", "IPC", "USPC", "CCLS"], value: str, include_children: bool = False):
        super().__init__()
        self.scheme = scheme
        self.value = value
        self.include_children = include_children
    def get_compare_attrs(self): return ['scheme', 'value', 'include_children']

class PatentNumberNode(ASTNode): # Not explicitly used by current parsers/generators but good for AST
    def __init__(self, number: str):
        super().__init__()
        self.number = number
    def get_compare_attrs(self): return ['number']


class BooleanOpNode(ASTNode):
    def __init__(self, operator: Literal["AND", "OR", "NOT", "XOR"], operands: List[ASTNode]):
        super().__init__()
        self.operator = operator
        self.operands = operands
    def get_compare_attrs(self): return ['operator', 'operands']

class ProximityOpNode(ASTNode):
    def __init__(self, operator: Literal["ADJ", "NEAR", "WITH", "SAME"], terms: List[ASTNode], 
                 distance: Optional[int] = None, ordered: bool = False,
                 scope_unit: Optional[Literal["word", "sentence", "paragraph"]] = None):
        super().__init__()
        self.operator = operator
        self.terms = terms
        self.distance = distance
        self.ordered = ordered
        self.scope_unit = scope_unit
    def get_compare_attrs(self): return ['operator', 'terms', 'distance', 'ordered', 'scope_unit']

class FieldedSearchNode(ASTNode):
    def __init__(self, field_canonical_name: str, query: ASTNode, system_field_code: Optional[str] = None):
        super().__init__()
        self.field_canonical_name = field_canonical_name
        self.query = query
        self.system_field_code = system_field_code
    def get_compare_attrs(self): return ['field_canonical_name', 'query', 'system_field_code']

class DateSearchNode(ASTNode):
    def __init__(self, field_canonical_name: Literal["publication_date", "application_date", "priority_date", "issue_date", "application_year", "publication_year"], 
                 operator: Literal[">=", "<=", "=", ">", "<", "<>"], date_value: str,
                 date_value2: Optional[str] = None, system_field_code: Optional[str] = None):
        super().__init__()
        self.field_canonical_name = field_canonical_name
        self.operator = operator
        self.date_value = date_value
        self.date_value2 = date_value2
        self.system_field_code = system_field_code
    def get_compare_attrs(self): return ['field_canonical_name', 'operator', 'date_value', 'date_value2', 'system_field_code']

class QueryRootNode(ASTNode):
    def __init__(self, query: ASTNode, settings: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.query = query
        self.settings = settings if settings else {}
    def get_compare_attrs(self): return ['query', 'settings']

# --- Mappings ---
USPTO_TO_CANONICAL_FIELD = {
    "TTL": "title", "TI": "title", "ABST": "abstract", "AB": "abstract",
    "ACLM": "claims", "CLM": "claims", "CLMS": "claims", "SPEC": "description", "DETD": "description",
    "IN": "inventor_name", "INV": "inventor_name", "AN": "assignee_name", "AS": "assignee_name",
    "CPC": "cpc", "CPCA": "cpc", "CPCI": "cpc", "IPC": "ipc", "CCLS": "us_classification_ccls",
    "CLAS": "us_classification_text", "PN": "patent_number", "APP": "application_number",
    "DID": "document_id", "PD": "publication_date", "ISD": "issue_date",
    "AD": "application_date", "FD": "application_date", "AY": "application_year", "FY": "application_year",
    "PY": "publication_year",
}
GOOGLE_TO_CANONICAL_FIELD = { # Used if parsing Google queries; also for AST->Google hints
    "TI": "title", "AB": "abstract", "CL": "claims", "CPC": "cpc",
    "INVENTOR": "inventor_name", "ASSIGNEE": "assignee_name", "PN": "patent_number",
    "TITLE": "title", # For dedicated_title from google_generate_query
}

# --- USPTO Parser ---
class USPTOQueryParser:
    def __init__(self):
        self.field_mapping = USPTO_TO_CANONICAL_FIELD 
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
            op_str_full, right_operand = current_tokens[idx].upper(), current_tokens[idx+1]
            if op_str_full in ["AND", "OR", "XOR"]:
                node = BooleanOpNode(op_str_full, [node, right_operand])
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
        fc_tok_list = tokens[0]; fc=fc_tok_list[0].upper(); qn=fc_tok_list[1]
        cn=self.field_mapping.get(fc, f"unknown_uspto_field_{fc}")
        return FieldedSearchNode(cn, qn, system_field_code=fc)

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
        ops_map={n:pp.CaselessLiteral(n) for n in ["AND","OR","NOT","XOR"]}
        ops_map["PROX"]=pp.Regex(r"(ADJ|NEAR|WITH|SAME)\d*",re.I)
        
        # searchTermAtom should not consume parts of field codes like "TTL/" if not quoted.
        # This is tricky. One way is to ensure field codes are parsed with higher precedence or distinctively.
        # For now, Word(alphanums + "-_/.?$*:") is greedy.
        # Let's try a negative lookahead for field prefixes if possible, or make it simpler.
        # Simpler: define field prefixes and operators first.
        searchTermAtom = pp.Word(pp.alphanums + "-_/.?$*:") # Original, might be too greedy
        
        # A more restricted term that doesn't include / if it's followed by typical field characters
        # This is still hard to get perfect without a full lexer.
        # For now, rely on pyparsing's longest match and operator definition order.

        quotedStringAtom = QUOTE + pp.Combine(pp.ZeroOrMore(pp.CharsNotIn('"') | (pp.Literal('""').setParseAction(lambda:"\"")))) + QUOTE
        
        term = quotedStringAtom.setParseAction(lambda s,l,t: TermNode(t[0], is_phrase=True)) | \
               searchTermAtom.setParseAction(lambda s,l,t: TermNode(t[0]))

        expr = pp.Forward()

        # Corrected field prefix regex to ensure it matches the whole prefix ending with /
        field_keys_re = "|".join(re.escape(k) for k in self.field_mapping.keys())
        uspto_field_prefix = pp.Regex(f"({field_keys_re})/", re.I).setParseAction(lambda t: t[0].upper().replace("/", ""))
        
        field_content = (LPAR + expr + RPAR) | term.copy()
        fielded_search = pp.Group(uspto_field_prefix + field_content).setParseAction(self._make_fielded_node)
        
        uspto_date_expr_regex = r"@[A-Za-z]{2,}(?:=|>=|<=|>|<|<>)\d+(?:/\d+)?(?:<=\d+(?:/\d+)?)?"
        uspto_date_search = pp.Regex(uspto_date_expr_regex).setParseAction(self._make_date_node)

        atom = fielded_search | uspto_date_search | (LPAR + expr + RPAR) | term.copy()
        
        expr <<= pp.infixNotation(atom,[
            (ops_map["NOT"],1,pp.opAssoc.RIGHT,self._build_ast_from_infix_tokens),
            (ops_map["PROX"],2,pp.opAssoc.LEFT,self._build_ast_from_infix_tokens),
            (ops_map["AND"],2,pp.opAssoc.LEFT,self._build_ast_from_infix_tokens),
            (ops_map["XOR"],2,pp.opAssoc.LEFT,self._build_ast_from_infix_tokens),
            (ops_map["OR"],2,pp.opAssoc.LEFT,self._build_ast_from_infix_tokens)])
        
        set_kw=pp.CaselessLiteral("SET").suppress()
        set_pv=pp.Word(pp.alphanums+"_");set_pn=pp.Word(pp.alphas+"_")
        set_assign=pp.Group(set_pn+pp.Literal("=").suppress()+set_pv)
        set_cmd_opt=pp.Optional(set_kw+pp.delimitedList(set_assign,delim=",")).setResultsName("st")
        
        # To handle "IN/Doe AN/Acme" (implicitly ANDed), we need a list of expressions.
        # This assumes that if no operator is present between `expr` items, they are ANDed.
        # This is a significant change to how `expr` is defined and processed.
        # For now, this parser will require explicit ANDs for such cases.
        # The test cases that fail with "Expected end of text" highlight this limitation.
        return set_cmd_opt + pp.Optional(expr).setResultsName("qe")

    def parse(self, query_string: str) -> QueryRootNode:
        try:
            if not query_string.strip(): return QueryRootNode(query=TermNode("__EMPTY__"))
            # Add a whitespace skipper that respects quoted strings
            # self.grammar.setDefaultWhitespaceChars(" \t\r") # pyparsing default is " \t\r\n"
            # pp.ParserElement.setDefaultWhitespaceChars(" \t\r") # This is global, be careful

            parsed = self.grammar.parseString(query_string, parseAll=True)
            q_ast_tok = parsed.get("qe")
            q_ast:Optional[ASTNode]=None
            if q_ast_tok:
                if isinstance(q_ast_tok,ASTNode):q_ast=q_ast_tok
                elif isinstance(q_ast_tok,pp.ParseResults)and len(q_ast_tok)==1 and isinstance(q_ast_tok[0],ASTNode):q_ast=q_ast_tok[0]
                elif isinstance(q_ast_tok,str):q_ast=TermNode(q_ast_tok) # Single term query
                else:raise pp.ParseException(query_string,0,f"Parsed query is not ASTNode. Got: {type(q_ast_tok)}")
            else:q_ast=TermNode("__EMPTY_AFTER_SET__")
            s_dict={}
            s_tok_list=parsed.get("st")
            if s_tok_list:
                for sg_group in s_tok_list: # s_tok_list is a list of groups if multiple settings
                    if isinstance(sg_group, pp.ParseResults) and len(sg_group) == 2:
                         s_dict[sg_group[0].lower()] = sg_group[1]
                    # Handle if s_tok_list is a single group (ParseResults of 2 elements)
                    elif isinstance(s_tok_list, pp.ParseResults) and len(s_tok_list) == 2 and isinstance(s_tok_list[0], str):
                        s_dict[s_tok_list[0].lower()] = s_tok_list[1]
                        break # Only one setting group
            return QueryRootNode(query=q_ast,settings=s_dict)
        except pp.ParseException as pe:
            return QueryRootNode(query=TermNode(f"PARSE_ERROR: {pe.line}(col {pe.column}) msg: {pe.msg}"))
        except Exception as e:
            # import traceback; traceback.print_exc()
            return QueryRootNode(query=TermNode(f"UNEXPECTED_PARSE_ERROR: {str(e)}"))

# --- AST to Google Generator (Further Refined) ---
class ASTToGoogleQueryGenerator:
    def __init__(self): pass

    def generate(self, ast_root: QueryRootNode) -> str:
        if not isinstance(ast_root, QueryRootNode): return "Error: Invalid AST root"
        return self._generate_node(ast_root.query, is_top_level_expr=True, parent_op_type=None)

    def _get_op_precedence(self, op_str: Optional[str]) -> int:
        if op_str is None: return -1 
        if op_str in ["TI", "AB", "CL", "CPC_FIELD", "assignee", "inventor", "patent_number"]: return 5 
        if op_str.startswith(("ADJ", "NEAR", "WITH", "SAME")): return 4 
        if op_str == "NOT_OPERATOR" or op_str == "NOT_PREFIX": return 3
        if op_str == "AND": return 2
        if op_str == "OR" or op_str == "XOR": return 1
        return 0 

    def _generate_node(self, node: ASTNode, is_top_level_expr: bool = False, parent_op_type: Optional[str] = None) -> str:
        res_str = ""
        current_node_op_type = None 

        if isinstance(node, TermNode):
            if node.value == "__EMPTY__" or node.value == "__EMPTY_AFTER_SET__": return ""
            current_node_op_type = "TERM"
            if node.is_phrase: res_str = f'"{node.value}"'
            elif node.value.upper() in ["AND", "OR", "NOT", "NEAR", "ADJ", "WITH", "SAME"] and not node.is_phrase:
                res_str = f'"{node.value}"'
            else: res_str = node.value
        
        elif isinstance(node, FieldedSearchNode):
            field_google = self._map_canonical_to_google_field(node.field_canonical_name)
            current_node_op_type = field_google or "FIELD_ASSIGN" 
            query_str = self._generate_node(node.query, is_top_level_expr=True, parent_op_type=None) 
            
            if field_google in ["TI", "AB", "CL"]:
                res_str = f"{field_google}=({query_str})"
            elif field_google == "CPC":
                cpc_val = query_str.strip('\"()') 
                original_query_node = node.query
                if isinstance(original_query_node, ClassificationNode) and original_query_node.include_children:
                    if not cpc_val.endswith("/low"): cpc_val += "/low"
                elif isinstance(original_query_node, TermNode) and "/low" in original_query_node.value.lower():
                     if not cpc_val.endswith("/low"): cpc_val += "/low"
                res_str = f"CPC:{cpc_val}"
            elif field_google in ["assignee", "inventor", "patent_number"]: 
                res_str = f"{field_google}:({query_str})" 
            else: res_str = query_str 

        elif isinstance(node, BooleanOpNode):
            current_node_op_type = node.operator.upper()
            if current_node_op_type == "NOT" and len(node.operands) == 1:
                operand_node = node.operands[0]
                operand_str = self._generate_node(operand_node, is_top_level_expr=False, parent_op_type="NOT_OPERATOR")
                is_simple_for_prefix = isinstance(operand_node, TermNode) and \
                                   not operand_node.is_phrase and \
                                   " " not in operand_node.value and \
                                   not (operand_node.value.startswith("(") and operand_node.value.endswith(")")) and \
                                   not operand_str.startswith("-")
                if is_simple_for_prefix:
                    res_str = f"-{operand_str.strip('\"')}"
                    current_node_op_type = "NOT_PREFIX" 
                else:
                    res_str = f"NOT ({operand_str})"
            else: # AND, OR, XOR
                op_strs = [self._generate_node(op, is_top_level_expr=False, parent_op_type=current_node_op_type) for op in node.operands]
                op_strs = [s for s in op_strs if s]
                if not op_strs: return ""
                if len(op_strs) == 1 and current_node_op_type != "NOT" : return op_strs[0]
                
                joiner = f" {current_node_op_type} "
                # Critical fix for: USPTO to Google: XOR and Date, and similar top-level ANDs
                if current_node_op_type == "AND" and is_top_level_expr:
                    joiner = " " 
                res_str = joiner.join(op_strs)
        
        elif isinstance(node, ProximityOpNode):
            current_node_op_type = node.operator.upper()
            terms_s = [self._generate_node(t, is_top_level_expr=False, parent_op_type=current_node_op_type) for t in node.terms]
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
            if node.include_children and not res_str.endswith("/low"): 
                res_str += "/low"
            
        elif isinstance(node, DateSearchNode):
            current_node_op_type = "DATE_EXPR" 
            type_map = {"publication_date": "publication", "issue_date": "publication",
                        "application_date": "filing", "priority_date": "priority"}
            google_date_type = type_map.get(node.field_canonical_name)
            parts = []
            if not google_date_type:
                if node.field_canonical_name in ["application_year", "publication_year"]:
                    year_val = node.date_value.replace("-","").replace("/","")
                    base_type = "filing" if "application" in node.field_canonical_name else "publication"
                    if node.operator == "=": parts.extend([f"after:{base_type}:{year_val}0101", f"before:{base_type}:{year_val}1231"])
                    elif node.operator == ">=": parts.append(f"after:{base_type}:{year_val}0101")
                    elif node.operator == "<=": parts.append(f"before:{base_type}:{year_val}1231")
                    else: parts.append(f"Error:GYOp({node.operator})") # Shorter error
                else: parts.append(f"Error:GDateType({node.field_canonical_name})")
            else:
                date_val_fmt = node.date_value.replace("-","").replace("/","")
                if node.date_value2: 
                    date_val2_fmt = node.date_value2.replace("-","").replace("/","")
                    if node.operator == ">=" : parts.append(f"after:{google_date_type}:{date_val_fmt}")
                    parts.append(f"before:{google_date_type}:{date_val2_fmt}")
                else:
                    if node.operator == ">=" : parts.append(f"after:{google_date_type}:{date_val_fmt}")
                    elif node.operator == "<=" : parts.append(f"before:{google_date_type}:{date_val_fmt}")
                    elif node.operator == "=": 
                        parts.extend([f"after:{google_date_type}:{date_val_fmt}", f"before:{google_date_type}:{date_val_fmt}"])
                    elif node.operator == ">" : parts.append(f"after:{google_date_type}:{date_val_fmt}") 
                    elif node.operator == "<" : parts.append(f"before:{google_date_type}:{date_val_fmt}")
                    else: parts.append(f"Error:GDateOp({node.operator})")
            res_str = " ".join(p for p in parts if p and not p.startswith("Error:"))
            if any(e in res_str for e in ["Error:GYOp", "Error:GDateType", "Error:GDateOp"]): return res_str 
        else:
            res_str = f"Error:UnhandledASTNode({type(node).__name__})"

        # Parenthesizing logic (final check)
        # Only add parentheses if it's an operator node, not top level, and its precedence requires it,
        # and it's not already a field assignment like TI=(...) which handles its own parens.
        if isinstance(node, (BooleanOpNode, ProximityOpNode)) and \
           not is_top_level_expr and \
           self._needs_paren(current_node_op_type, parent_op_type):
            # Avoid double parenthesizing if res_str is already e.g. "(A OR B)" from a recursive call
            if not (res_str.startswith("(") and res_str.endswith(")")):
                 return f"({res_str})"
        
        return res_str

    def _map_canonical_to_google_field(self, canonical_name: str) -> Optional[str]:
        if canonical_name == "title": return "TI"
        if canonical_name == "abstract": return "AB"
        if canonical_name == "claims": return "CL"
        if canonical_name == "cpc": return "CPC"
        if canonical_name == "assignee_name": return "assignee"
        if canonical_name == "inventor_name": return "inventor"
        if canonical_name == "patent_number": return "patent_number" 
        return None

# --- Main Conversion Function ---
def convert_query(query_string: str, 
                  source_format: Literal["google", "uspto"], 
                  target_format: Literal["google", "uspto"]) -> Dict[str, Union[str, None, Dict[str, Any]]]:
    if not query_string.strip():
         return {"query": "", "error": None, "settings": {}} 

    ast_root: Optional[QueryRootNode] = None
    parser_error: Optional[str] = None
    parsed_settings: Dict[str, Any] = {}

    try:
        if source_format == "google":
            return {"query": None, "error": "Google to AST parser not yet implemented.", "settings": {}}
        elif source_format == "uspto":
            parser = USPTOQueryParser()
            ast_root = parser.parse(query_string)
            if isinstance(ast_root.query, TermNode) and ("PARSE_ERROR" in ast_root.query.value or "UNEXPECTED_PARSE_ERROR" in ast_root.query.value):
                parser_error = ast_root.query.value
                ast_root = None 
            elif ast_root:
                parsed_settings = ast_root.settings
        else:
            return {"query": None, "error": f"Unsupported source format: {source_format}", "settings": {}}
    except Exception as e:
        # import traceback; print(traceback.format_exc()) # For deeper debugging
        parser_error = f"Parsing failed with exception: {e}"


    if parser_error:
        return {"query": None, "error": f"Error parsing {source_format} query '{query_string}': {parser_error}", "settings": parsed_settings}
    if not ast_root: 
        return {"query": None, "error": f"Unknown error parsing {source_format} query: {query_string}", "settings": parsed_settings}

    output_query: Optional[str] = None
    generator_error: Optional[str] = None
    try:
        if target_format == "google":
            generator = ASTToGoogleQueryGenerator()
            output_query = generator.generate(ast_root)
        elif target_format == "uspto":
            return {"query": None, "error": "AST to USPTO generator not yet implemented.", "settings": parsed_settings}
        else:
            return {"query": None, "error": f"Unsupported target format: {target_format}", "settings": parsed_settings}
        
        if isinstance(output_query, str) and \
           ("Error:" in output_query or "UnhandledASTNode" in output_query or "Unsupported" in output_query) : 
            generator_error = output_query
            output_query = None
    except Exception as e:
        # import traceback; print(traceback.format_exc()) # For deeper debugging
        generator_error = f"Generation failed with exception: {e}"

    if generator_error:
        return {"query": None, "error": f"Error generating {target_format} query: {generator_error}", "settings": parsed_settings}
    
    return {"query": output_query, "error": None, "settings": parsed_settings}