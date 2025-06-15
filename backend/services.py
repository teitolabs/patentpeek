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
            # Use quote_plus for all other params, which handles spaces as '+'
            encoded_value = quote_plus(self.value)
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
                # Use the Google parser as the intermediate for building the AST
                parsed_ast_root = PARSERS["google"].parse(text_input)
                if not isinstance(parsed_ast_root.query, TermNode) or parsed_ast_root.query.value != "__EMPTY__":
                    ast_nodes.append(parsed_ast_root.query)

    # 2. Process all Google-like fields as top-level parameters
    if req.googleLikeFields:
        fields = req.googleLikeFields
        
        if fields.inventors:
            # Join multiple inventors with a comma, as per Google's UI behavior
            value = ",".join([inv.value.strip() for inv in fields.inventors if inv.value.strip()])
            if value: top_level_params.append(UrlParam("inventor", value))
        
        if fields.assignees:
            value = ",".join([asg.value.strip() for asg in fields.assignees if asg.value.strip()])
            if value: top_level_params.append(UrlParam("assignee", value))

        if fields.dateType and (fields.dateFrom or fields.dateTo):
            date_type_str = fields.dateType  # 'publication', 'filing', 'priority'
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
        
        # FIX: Correctly map litigation to Google's URL parameter 'litigated=true'
        if fields.litigation == "YES":
            top_level_params.append(UrlParam("litigated", "true"))
        
    return ast_nodes, top_level_params


def generate_query(req: models.GenerateRequest) -> models.GenerateResponse:
    if req.format == "google":
        generator = GENERATORS["google"]
        ast_nodes, top_level_params = _build_query_components(req)

        if not ast_nodes and not top_level_params:
            return models.GenerateResponse(queryStringDisplay="", url="#")

        url_params_list = []
        display_parts = []

        # --- Build the 'q' parameters and display parts from text boxes ---
        for node in ast_nodes:
            generated_str = generator.generate(QueryRootNode(query=node))
            if generated_str:
                url_params_list.append(UrlParam('q', generated_str).to_string())
                # For display, wrap multi-word or complex terms in parentheses for clarity
                if " " in generated_str and not (generated_str.startswith('(') and generated_str.endswith(')')):
                    display_parts.append(f"({generated_str})")
                else:
                    display_parts.append(generated_str)

        # --- Build the top-level field parameters and display parts ---
        for param in top_level_params:
            url_params_list.append(param.to_string())
            # For display, use the 'key:value' format, with a special case for litigation
            if param.key == "litigated" and param.value == "true":
                 display_parts.append("is:litigated")
            else:
                display_parts.append(f"{param.key}:{param.value}")

        # --- Assemble final URL and Display String ---
        final_url_query = "&".join(url_params_list)
        url = f"https://patents.google.com/?{final_url_query}" if final_url_query else "#"
        final_display_string = " ".join(display_parts)

        return models.GenerateResponse(queryStringDisplay=final_display_string, url=url)

    elif req.format == "uspto":
        # The USPTO logic remains simpler and is handled separately
        generator = GENERATORS["uspto"]
        ast_nodes, _ = _build_query_components(req) # USPTO doesn't use top-level params in the same way
        
        if not ast_nodes:
             return models.GenerateResponse(queryStringDisplay="", url="#")

        # Combine all AST nodes with AND for a single USPTO query
        combined_query_node = BooleanOpNode("AND", ast_nodes) if len(ast_nodes) > 1 else ast_nodes[0]
        combined_query = generator.generate(QueryRootNode(query=combined_query_node))
        url_query_param = quote_plus(combined_query)
        url = f"https://ppubs.uspto.gov/pubwebapp/static/pages/ppubsadvanced.html?query={url_query_param}" if url_query_param else "#"
        return models.GenerateResponse(queryStringDisplay=combined_query, url=url)
    else:
        raise HTTPException(status_code=400, detail=f"Invalid format for generation: {req.format}")


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
        # Check for the term 'is:litigated' to handle it as a field
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
            date_obj = node.date_value
            # Handle both full dates (YYYYMMDD) and years (YYYY)
            date_str = f"{date_obj[:4]}-{date_obj[4:6]}-{date_obj[6:]}" if len(date_obj) > 4 else date_obj

            if node.operator in [">=", ">"]:
                glf.dateFrom = date_str
                if node.field_canonical_name == "publication_date": glf.dateType = "publication"
                elif node.field_canonical_name == "application_date": glf.dateType = "filing"
                elif node.field_canonical_name == "priority_date": glf.dateType = "priority"
            elif node.operator in ["<=", "<"]:
                glf.dateTo = date_str
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
    try:
        source_parser = PARSERS[req.source_format]
        target_generator = GENERATORS[req.target_format]
        ast = source_parser.parse(req.query_string)
        
        # Check for parse errors
        if isinstance(ast.query, TermNode) and ast.query.value.startswith("PARSE_ERROR"):
            return models.ConvertResponse(error=f"Could not parse source query: {ast.query.value}")

        converted_text = target_generator.generate(ast)
        return models.ConvertResponse(converted_text=converted_text, settings={})
    except Exception as e:
        return models.ConvertResponse(error=str(e))