# /backend/services.py
from typing import List, Dict, Any, Optional, Tuple
from fastapi import HTTPException
from pyparsing import ParseException
import uuid
import re
from urllib.parse import quote_plus, quote
import models
from ast_nodes import (
    ASTNode, QueryRootNode, TermNode, BooleanOpNode, ProximityOpNode,
    FieldedSearchNode, DateSearchNode, ClassificationNode
)
from google_parser import GoogleQueryParser
from google_generator import ASTToGoogleQueryGenerator
from uspto_parser import USPTOQueryParser
from uspto_generator import ASTToUSPTOQueryGenerator

# Instantiate parsers and generators once to be reused
PARSERS = {
    "google": GoogleQueryParser(),
    "uspto": USPTOQueryParser()
}
GENERATORS = {
    "google": ASTToGoogleQueryGenerator(),
    "uspto": ASTToUSPTOQueryGenerator()
}


# --- A simple data class to hold different parameter types ---
class UrlParam:
    def __init__(self, key: str, value: str):
        self.key = key
        self.value = value

    def to_string(self) -> str:
        # Use quote for date params to preserve the ':'
        if self.key in ['before', 'after']:
            return f"{self.key}={quote(self.value)}"
        else:
            # Use quote_plus for all other params
            encoded_value = quote_plus(self.value).replace('%2B', '%2b')
            return f"{self.key}={encoded_value}"

def _build_query_components(req: models.GenerateRequest) -> Tuple[List[ASTNode], List[UrlParam]]:
    """
    Processes the request and separates components into two lists:
    1. ast_nodes: For complex queries that will be combined into 'q' parameters.
    2. top_level_params: For simple key-value fields that become their own URL parameters.
    """
    ast_nodes: List[ASTNode] = []
    top_level_params: List[UrlParam] = []
    
    # 1. Process TEXT conditions into the main AST list.
    if req.searchConditions:
        for condition in req.searchConditions:
            if condition.type == "TEXT":
                text_data = condition.data
                text_input = text_data.text.strip()
                if not text_input:
                    continue
                parsed_ast_root = PARSERS["google"].parse(text_input)
                if not isinstance(parsed_ast_root.query, TermNode) or parsed_ast_root.query.value != "__EMPTY__":
                    ast_nodes.append(parsed_ast_root.query)

    # 2. Process all Google-like fields as top-level parameters
    if req.googleLikeFields:
        fields = req.googleLikeFields
        
        if fields.inventors:
            value = ",".join([inv.value.strip() for inv in fields.inventors if inv.value.strip()])
            if value: top_level_params.append(UrlParam("inventor", value))
        
        if fields.assignees:
            value = ",".join([asg.value.strip() for asg in fields.assignees if asg.value.strip()])
            if value: top_level_params.append(UrlParam("assignee", value))

        if fields.dateType and (fields.dateFrom or fields.dateTo):
            date_type_str = ""
            if fields.dateType == "publication": date_type_str = "publication"
            elif fields.dateType == "filing": date_type_str = "filing"
            elif fields.dateType == "priority": date_type_str = "priority"
            if date_type_str:
                if fields.dateFrom:
                    df = fields.dateFrom.replace("-", "")
                    if df.isdigit(): top_level_params.append(UrlParam("after", f"{date_type_str}:{df}"))
                if fields.dateTo:
                    dt = fields.dateTo.replace("-", "")
                    if dt.isdigit(): top_level_params.append(UrlParam("before", f"{date_type_str}:{dt}"))
        
        if fields.patentOffices:
            value = ",".join(fields.patentOffices)
            if value: top_level_params.append(UrlParam("country", value))
        
        if fields.languages:
            value = ",".join(fields.languages)
            if value: top_level_params.append(UrlParam("language", value.upper()))

        if fields.status:
            top_level_params.append(UrlParam("status", fields.status.upper()))
        
        if fields.patentType:
            top_level_params.append(UrlParam("type", fields.patentType.upper()))
        
        # --- FIX: Changed how litigation is handled to use top_level_params ---
        # This is because Google's URL structure for this is a direct param, not part of 'q'
        if fields.litigation == "YES":
            top_level_params.append(UrlParam("litigation", "YES"))
        elif fields.litigation == "NO":
            top_level_params.append(UrlParam("litigation", "NO"))

    return ast_nodes, top_level_params


def generate_query(req: models.GenerateRequest) -> models.GenerateResponse:
    # --- START: REVISED generate_query function ---
    ast_nodes, top_level_params = _build_query_components(req)

    if not ast_nodes and not top_level_params:
        return models.GenerateResponse(queryStringDisplay="", url="#")

    if req.format == "google":
        generator = GENERATORS["google"]
        display_parts = []
        
        # Process each AST node from the text boxes individually
        for node in ast_nodes:
            generated_str = generator.generate(QueryRootNode(query=node))
            if not generated_str:
                continue
            
            # The core of the fix: wrap in parentheses if it's not already complex
            # A simple heuristic: if it doesn't contain parentheses already, wrap it.
            # Also, don't wrap error messages.
            if '(' not in generated_str and not generated_str.startswith("PARSE_ERROR"):
                 display_parts.append(f"({generated_str})")
            else:
                 display_parts.append(generated_str)
        
        # This becomes the main query part, joined by spaces (implicit AND)
        term_query_string = " ".join(display_parts)
        
        # Now, build the final display string and URL params
        final_display_parts = [term_query_string] if term_query_string else []
        url_params_list = []

        # The main query part goes into the 'q' parameter
        if term_query_string:
            url_params_list.append(UrlParam('q', term_query_string).to_string())

        # The other fields become their own top-level URL parameters
        for param in top_level_params:
            final_display_parts.append(f"{param.key}:{param.value}")
            url_params_list.append(param.to_string())

        # The final string shown to the user is a space-separated list of all components
        # This is how Google's own search box displays it
        final_display_string = " ".join(final_display_parts)
        
        # The URL is built from the combined list of URL parameters
        # --- FIX: The logic for building the final URL is now different ---
        # Google patents uses a mix of `q=` for terms and top-level params for fields.
        # So we can't just put everything in 'q'.
        
        # Let's rebuild the final query string for the 'q' parameter to include everything
        # This is simpler and aligns with how Google seems to handle complex queries pasted in.
        final_q_string = " ".join(final_display_parts)
        
        url_params_list = [UrlParam('q', final_q_string).to_string()] if final_q_string else []
        final_url_query = "&".join(url_params_list)
        
        url = f"https://patents.google.com/?{final_url_query}" if final_url_query else "#"
        
        return models.GenerateResponse(queryStringDisplay=final_q_string, url=url)

    elif req.format == "uspto":
        # USPTO logic remains the same, as it's simpler
        generator = GENERATORS["uspto"]
        if not ast_nodes:
             return models.GenerateResponse(queryStringDisplay="", url="#")
        combined_query_node = BooleanOpNode("AND", ast_nodes) if len(ast_nodes) > 1 else ast_nodes[0]
        combined_query = generator.generate(QueryRootNode(query=combined_query_node))
        url_query_param = quote_plus(combined_query)
        url = f"https://ppubs.uspto.gov/pubwebapp/static/pages/ppubsadvanced.html?query={url_query_param}" if url_query_param else "#"
        return models.GenerateResponse(queryStringDisplay=combined_query, url=url)
    else:
        raise HTTPException(status_code=400, detail=f"Invalid format for generation: {req.format}")
    # --- END: REVISED generate_query function ---

# ... (the rest of the file, parse_query and convert_query_service, remains unchanged)
def parse_query(req: models.ParseRequest) -> models.ParseResponse:
    if req.format not in PARSERS:
        raise HTTPException(status_code=400, detail=f"No parser available for format: {req.format}")

    parser = PARSERS[req.format]
    generator = GENERATORS[req.format]
    
    ast_root = parser.parse(req.queryString)
    if isinstance(ast_root.query, TermNode) and (ast_root.query.value.startswith("PARSE_ERROR") or ast_root.query.value == "__EMPTY__"):
        return models.ParseResponse(
            searchConditions=[models.SearchCondition(
                id=str(uuid.uuid4()), type="TEXT", data={"type": "TEXT", "text": req.queryString}
            )],
            googleLikeFields=models.GoogleLikeSearchFields(dateFrom="", dateTo="", dateType="publication", inventors=[], assignees=[], patentOffices=[], languages=[], status="", patentType="", litigation=""),
            usptoSpecificSettings=models.UsptoSpecificSettings(defaultOperator="AND", plurals=False, britishEquivalents=True, selectedDatabases=['US-PGPUB', 'USPAT', 'USOCR'], highlights='SINGLE_COLOR', showErrors=True)
        )

    def is_field_or_date(node: ASTNode) -> bool:
        if isinstance(node, FieldedSearchNode):
            # These fields are handled by the dedicated UI elements
            return node.field_canonical_name in ["inventor_name", "assignee_name", "country_code", "language", "status", "patent_type"]
        if isinstance(node, DateSearchNode): return True
        if isinstance(node, TermNode) and node.value.lower() == "is:litigated": return True
        return False
    
    field_nodes, text_nodes_ast = parser._walk_ast_and_split(ast_root.query, is_field_or_date)

    glf = models.GoogleLikeSearchFields(dateFrom="", dateTo="", dateType="publication", inventors=[], assignees=[], patentOffices=[], languages=[], status="", patentType="", litigation="")
    for node in field_nodes:
        if isinstance(node, FieldedSearchNode) and isinstance(node.query, TermNode):
            val = node.query.value
            if node.field_canonical_name == "inventor_name": glf.inventors.extend([models.DynamicEntry(id=str(uuid.uuid4()), value=v.strip()) for v in val.split(',')])
            elif node.field_canonical_name == "assignee_name": glf.assignees.extend([models.DynamicEntry(id=str(uuid.uuid4()), value=v.strip()) for v in val.split(',')])
            elif node.field_canonical_name == "country_code": glf.patentOffices.extend([v.strip() for v in val.split(',')])
            elif node.field_canonical_name == "language": glf.languages.extend([v.strip().upper() for v in val.split(',')])
            elif node.field_canonical_name == "status": glf.status = val.upper()
            elif node.field_canonical_name == "patent_type": glf.patentType = val.upper()
        elif isinstance(node, DateSearchNode):
            if node.operator in [">=", ">"]:
                glf.dateFrom = f"{node.date_value[:4]}-{node.date_value[4:6]}-{node.date_value[6:]}"
                if node.field_canonical_name == "publication_date": glf.dateType = "publication"
                elif node.field_canonical_name == "application_date": glf.dateType = "filing"
                elif node.field_canonical_name == "priority_date": glf.dateType = "priority"
            elif node.operator in ["<=", "<"]:
                glf.dateTo = f"{node.date_value[:4]}-{node.date_value[4:6]}-{node.date_value[6:]}"
        elif isinstance(node, TermNode) and node.value.lower() == "is:litigated": glf.litigation = "YES"

    text_search_string = ""
    if text_nodes_ast:
        # Re-combine the remaining text nodes into a single AST
        text_root_node = BooleanOpNode("AND", text_nodes_ast) if len(text_nodes_ast) > 1 else text_nodes_ast[0]
        # Use the appropriate generator to create the string representation
        text_search_string = generator.generate(QueryRootNode(query=text_root_node))
        
    return models.ParseResponse(
        searchConditions=[models.SearchCondition(
            id=str(uuid.uuid4()), type="TEXT", data={"type": "TEXT", "text": text_search_string}
        )],
        googleLikeFields=glf,
        usptoSpecificSettings=models.UsptoSpecificSettings(defaultOperator="AND", plurals=False, britishEquivalents=True, selectedDatabases=['US-PGPUB', 'USPAT', 'USOCR'], highlights='SINGLE_COLOR', showErrors=True)
    )

def convert_query_service(req: models.ConvertRequest) -> models.ConvertResponse:
    # This service remains a placeholder for now
    converted_text = f"Placeholder conversion of '{req.query_string}'"
    return models.ConvertResponse(converted_text=converted_text, settings={})