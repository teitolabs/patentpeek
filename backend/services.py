# /backend/services.py
from typing import List, Dict, Any, Optional, Tuple
from fastapi import HTTPException
from pyparsing import ParseException
import uuid
import pprint
from urllib.parse import quote_plus, quote
import models
from ast_nodes import (
    ASTNode, QueryRootNode, TermNode, BooleanOpNode, ProximityOpNode,
    FieldedSearchNode, DateSearchNode, ClassificationNode
)
# We now need the real parser for the text boxes
from google_parser import GoogleQueryParser
from google_generator import ASTToGoogleQueryGenerator
from uspto_parser import USPTOQueryParser
from uspto_generator import ASTToUSPTOQueryGenerator

# Instantiate the parser once to be reused
TEXT_BOX_PARSER = GoogleQueryParser()

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
    # Other condition types like CLASSIFICATION have been removed from the UI
    # and are no longer sent as structured data.
    if req.searchConditions:
        for condition in req.searchConditions:
            if condition.type == "TEXT":
                text_data = condition.data
                text_input = text_data.text.strip()
                if not text_input:
                    continue
                # The text from each search term box is parsed into an AST
                parsed_ast_root = TEXT_BOX_PARSER.parse(text_input)
                # Ignore empty results from the parser
                if not isinstance(parsed_ast_root.query, TermNode) or parsed_ast_root.query.value != "__EMPTY__":
                    ast_nodes.append(parsed_ast_root.query)
            
            # REMOVED: elif block for CLASSIFICATION as it's no longer a structured input.
            # The parser can still handle user-typed CPC queries like "CPC:H01L...".

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
        
        if fields.litigation == "YES":
            top_level_params.append(UrlParam("litigation", "YES"))
        elif fields.litigation == "NO":
            top_level_params.append(UrlParam("litigation", "NO"))

    return ast_nodes, top_level_params


def generate_query(req: models.GenerateRequest) -> models.GenerateResponse:
    ast_nodes, top_level_params = _build_query_components(req)

    if not ast_nodes and not top_level_params:
        return models.GenerateResponse(queryStringDisplay="", url="#")

    if req.format == "google":
        generator = ASTToGoogleQueryGenerator()
        display_parts = []
        url_params = [p.to_string() for p in top_level_params]

        # Process complex AST nodes into 'q' parameters
        for node in ast_nodes:
            ast_root = QueryRootNode(query=node)
            explicit_string = generator.generate(ast_root)
            if not explicit_string:
                continue
            
            google_syntax_string = explicit_string.replace(" AND ", " ")
            url_params.insert(0, UrlParam('q', google_syntax_string).to_string())

            display_string = google_syntax_string
            if '(' not in display_string and not display_string.startswith("PARSE_ERROR"):
                display_string = f"({display_string})"
            display_parts.append(display_string)

        # Process simple top-level parameters for display
        for param in top_level_params:
            display_parts.append(f"{param.key}:{param.value}")

        # Join the parts for the final output
        final_display_string = " ".join(display_parts)
        final_url_query = "&".join(url_params)
        url = f"https://patents.google.com/?{final_url_query}" if final_url_query else "#"
        
        return models.GenerateResponse(queryStringDisplay=final_display_string, url=url)

    elif req.format == "uspto":
        generator = ASTToUSPTOQueryGenerator()
        combined_query = " AND ".join([generator.generate(QueryRootNode(n)) for n in ast_nodes])
        url_query_param = quote_plus(combined_query)
        url = f"https://ppubs.uspto.gov/pubwebapp/static/pages/ppubsadvanced.html?query={url_query_param}" if url_query_param else "#"
        return models.GenerateResponse(queryStringDisplay=combined_query, url=url)
    else:
        raise HTTPException(status_code=400, detail=f"Invalid format for generation: {req.format}")


def parse_query(req: models.ParseRequest) -> models.ParseResponse:
    raise HTTPException(status_code=501, detail="Parsing from string not fully implemented yet.")

def convert_query_service(req: models.ConvertRequest) -> models.ConvertResponse:
    converted_text = f"Placeholder conversion of '{req.query_string}'"
    return models.ConvertResponse(converted_text=converted_text, settings={})