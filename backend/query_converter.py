# query_converter.py

from typing import Literal, Union, Dict, Any, Optional
from ast_nodes import ( 
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
            if ast_root and isinstance(ast_root.query, TermNode) and \
               ("PARSE_ERROR:" in ast_root.query.value or \
                "UNEXPECTED_GOOGLE_PARSE_ERROR:" in ast_root.query.value or \
                "UNEXPECTED_GOOGLE_PARSE_ROOT_NOT_AST_NODE:" in ast_root.query.value or \
                "UNEXPECTED_GOOGLE_PARSE_STRUCTURE:" in ast_root.query.value):
                parser_error = ast_root.query.value
                ast_root = None 

        elif source_format == "uspto":
            parser = USPTOQueryParser()
            ast_root = parser.parse(query_string)
            s_dict_for_convert = ast_root.settings if ast_root else {}
            if ast_root and isinstance(ast_root.query,TermNode) and \
               ("PARSE_ERROR:" in ast_root.query.value or \
                "UNEXPECTED_PARSE_ERROR:" in ast_root.query.value):
                parser_error = ast_root.query.value
                ast_root = None
        else: 
            return {"query":None,"error":f"Unsupported source format: {source_format}","settings":{}}
    except Exception as e:
        # import traceback; traceback.print_exc() # For deep debugging
        parser_error = f"Parsing failed with exception: {type(e).__name__}: {e}"
    
    if parser_error: 
        return {"query":None,"error":f"Error parsing {source_format} query '{query_string}': {parser_error}","settings":s_dict_for_convert}
    if not ast_root: # Should be caught by parser_error if parsing failed
        return {"query":None,"error":f"Unknown error creating AST from {source_format} query: {query_string}","settings":s_dict_for_convert}
    
    # 2. Generating from AST to target_format
    try:
        if target_format == "google":
            generator = ASTToGoogleQueryGenerator()
            ast_root_to_generate = ast_root # Start with the original

            # Handle USPTO's "DefaultOperator=OR term1 term2" for Google conversion
            if source_format == "uspto" and \
               s_dict_for_convert.get("defaultoperator","").upper() == "OR" and \
               isinstance(ast_root.query, BooleanOpNode) and \
               ast_root.query.operator == "OR":
                
                operands = ast_root.query.operands
                # This transformation assumes the OR was due to DefaultOperator.
                # A more robust check might involve looking at how the operands are structured.
                # For now, if top is OR and DefaultOperator=OR, assume it needs conversion to AND for Google.
                if len(operands) > 1:
                    # Check if all operands are "simple" enough that implicit AND is intended
                    is_simple_sequence = all(
                        isinstance(op, (TermNode, FieldedSearchNode, DateSearchNode, ClassificationNode))
                        for op in operands
                    )
                    if is_simple_sequence:
                        modified_query_ast = BooleanOpNode("AND", operands) 
                        ast_root_to_generate = QueryRootNode(query=modified_query_ast, settings=s_dict_for_convert)
            
            output_query = generator.generate(ast_root_to_generate)

        elif target_format == "uspto": 
            generator = ASTToUSPTOQueryGenerator()
            output_query = generator.generate(ast_root)

        else: 
            return {"query":None,"error":f"Unsupported target format: {target_format}","settings":s_dict_for_convert}
        
        # Common check for error strings embedded in the output by any generator
        if isinstance(output_query, str):
            # More specific error markers from generators
            if output_query.startswith("ERROR_") or \
               "UNHANDLED_AST_NODE" in output_query or \
               "UNKNOWN_USPTO_DATE_FIELD" in output_query or \
               "Error:UnhandledASTNode" in output_query or \
               "Error:UnknownGoogleDateType" in output_query or \
               "Error:Invalid" in output_query or \
               "Error:Unhandled" in output_query:
                generator_error = output_query
                output_query = None

    except Exception as e:
        # import traceback; traceback.print_exc() # For deep debugging
        generator_error = f"Generation failed with exception: {type(e).__name__}: {e}"
    
    if generator_error: 
        # Format the error message to match test expectations if possible
        # The test bench expects "Error generating {target_format} query: {generator_error_from_generator}"
        return {"query":None,"error":f"Error generating {target_format} query: {generator_error}","settings":s_dict_for_convert}
    
    return {"query": output_query, "error": None, "settings": s_dict_for_convert}