# query_converter.py

from typing import Literal, Union, Dict, Any, Optional
from ast_nodes import ( # ASTNode itself is not directly used here but good for context
    QueryRootNode, TermNode, ClassificationNode, BooleanOpNode,
    ProximityOpNode, FieldedSearchNode, DateSearchNode
)
from uspto_parser import USPTOQueryParser
from google_generator import ASTToGoogleQueryGenerator
from google_parser import GoogleQueryParser
from uspto_generator import ASTToUSPTOQueryGenerator


def convert_query(query_string: str,
                  source_format: Literal["google", "uspto"],
                  target_format: Literal["google", "uspto"]) -> Dict[str, Union[str, None, Dict[str, Any]]]:
    
    s_dict_for_convert: Dict[str, Any] = {} 
    ast_root: Optional[QueryRootNode] = None
    parser_error: Optional[str] = None
    output_query: Optional[str] = None
    generator_error: Optional[str] = None

    if not query_string.strip(): 
        return {"query": "", "error": None, "settings": {}}
    
    # 1. Parsing from source_format to AST
    try:
        if source_format == "google": 
            parser = GoogleQueryParser()
            ast_root = parser.parse(query_string)
            s_dict_for_convert = ast_root.settings if ast_root else {}
            # Check for stub/parse errors from GoogleParser
            if ast_root and isinstance(ast_root.query, TermNode) and \
               ("__GOOGLE_PARSE_STUB__" in ast_root.query.value or \
                "PARSE_ERROR" in ast_root.query.value): # Add more specific error checks
                parser_error = ast_root.query.value
                ast_root = None # Prevent further processing if stub/error

        elif source_format == "uspto":
            parser = USPTOQueryParser()
            ast_root = parser.parse(query_string)
            s_dict_for_convert = ast_root.settings if ast_root else {}
            if ast_root and isinstance(ast_root.query,TermNode) and \
               ("PARSE_ERROR" in ast_root.query.value or "UNEXPECTED_PARSE_ERROR" in ast_root.query.value):
                parser_error = ast_root.query.value
                ast_root = None
        else: 
            return {"query":None,"error":f"Unsupported source format: {source_format}","settings":{}}
    except Exception as e:
        parser_error = f"Parsing failed with exception: {e}"
    
    if parser_error: 
        return {"query":None,"error":f"Error parsing {source_format} query '{query_string}': {parser_error}","settings":s_dict_for_convert}
    if not ast_root:
        return {"query":None,"error":f"Unknown error creating AST from {source_format} query: {query_string}","settings":s_dict_for_convert}
    
    # 2. Generating from AST to target_format
    try:
        if target_format == "google":
            generator = ASTToGoogleQueryGenerator()
            temp_ast_root_for_google_gen = ast_root # Use the successfully parsed AST

            # Handle USPTO's "DefaultOperator=OR term1 term2" for Google conversion
            if s_dict_for_convert.get("defaultoperator","").upper() == "OR" and \
               isinstance(temp_ast_root_for_google_gen.query, BooleanOpNode) and \
               temp_ast_root_for_google_gen.query.operator == "OR":
                
                operands = temp_ast_root_for_google_gen.query.operands
                is_likely_default_or = all(
                    isinstance(op, (TermNode, FieldedSearchNode, DateSearchNode, ClassificationNode)) for op in operands
                )
                if is_likely_default_or and len(operands) > 1:
                    modified_query_ast = BooleanOpNode("AND", operands) # Google implies AND
                    temp_ast_root_for_google_gen = QueryRootNode(query=modified_query_ast, settings=s_dict_for_convert)
            
            output_query = generator.generate(temp_ast_root_for_google_gen)

        elif target_format == "uspto": 
            generator = ASTToUSPTOQueryGenerator()
            output_query = generator.generate(ast_root)
            # Check for stub/generation errors from ASTToUSPTOQueryGenerator
            if output_query and "__USPTO_GENERATE_STUB__" in output_query:
                generator_error = output_query
                output_query = None

        else: 
            return {"query":None,"error":f"Unsupported target format: {target_format}","settings":s_dict_for_convert}
        
        # Common check for error strings embedded in the output by any generator
        if isinstance(output_query, str) and \
           ("Error:" in output_query or "UnhandledASTNode" in output_query or \
            "Unsupported" in output_query or "UnknownGoogleDateType" in output_query or \
            "UnhandledYearOp" in output_query or "UnhandledDateOp" in output_query) :
            generator_error = output_query
            output_query = None

    except Exception as e:
        generator_error = f"Generation failed with exception: {e}"
    
    if generator_error: 
        return {"query":None,"error":f"Error generating {target_format} query: {generator_error}","settings":s_dict_for_convert}
    
    return {"query": output_query, "error": None, "settings": s_dict_for_convert}