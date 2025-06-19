# /backend/services.py
from typing import List, Dict, Any, Optional, Tuple
from fastapi import HTTPException
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
        if self.key in ['before', 'after']:
            return f"{self.key}={quote(self.value)}"
        else:
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
    
    if req.searchConditions:
        for condition in req.searchConditions:
            if condition.type == "TEXT":
                text_data = condition.data
                text_input = text_data.text.strip()
                if not text_input:
                    continue
                
                # --- THIS IS THE FIX ---
                # Wrap the raw text from the search term box in parentheses before parsing.
                # This treats it as a valid grouped expression according to the new grammar rules.
                query_to_parse = f"({text_input})"
                parsed_ast_root = PARSERS["google"].parse(query_to_parse)

                if not isinstance(parsed_ast_root.query, TermNode) or parsed_ast_root.query.value != "__EMPTY__":
                    ast_nodes.append(parsed_ast_root.query)

    if req.googleLikeFields:
        fields = req.googleLikeFields
        
        if fields.inventors:
            value = ",".join([inv.value.strip() for inv in fields.inventors if inv.value.strip()])
            if value: top_level_params.append(UrlParam("inventor", value))
        
        if fields.assignees:
            value = ",".join([asg.value.strip() for asg in fields.assignees if asg.value.strip()])
            if value: top_level_params.append(UrlParam("assignee", value))

        if fields.dateType and (fields.dateFrom or fields.dateTo):
            date_type_str = fields.dateType
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
            top_level_params.append(UrlParam("litigated", "true"))
        
    return ast_nodes, top_level_params

def _create_field_nodes_from_params(top_level_params: List[UrlParam]) -> List[ASTNode]:
    """Helper to convert top-level URL params back into AST nodes for visualization."""
    nodes = []
    field_map = {
        "inventor": "inventor_name", "assignee": "assignee_name", "country": "country_code",
        "language": "language", "status": "status", "type": "patent_type"
    }
    date_map = {
        "publication": "publication_date", "filing": "application_date", "priority": "priority_date"
    }

    for param in top_level_params:
        if param.key in field_map:
            nodes.append(FieldedSearchNode(field_map[param.key], TermNode(param.value)))
        elif param.key == "litigated" and param.value == "true":
            nodes.append(TermNode("is:litigated"))
        elif param.key in ["before", "after"]:
            try:
                date_type, date_value = param.value.split(":", 1)
                canonical_field = date_map.get(date_type)
                if canonical_field:
                    op = ">=" if param.key == "after" else "<="
                    nodes.append(DateSearchNode(canonical_field, op, date_value)) # type: ignore
            except ValueError:
                continue
    return nodes


def generate_query(req: models.GenerateRequest) -> models.GenerateResponse:
    if req.format == "google":
        generator = GENERATORS["google"]
        text_ast_nodes, top_level_params = _build_query_components(req)

        if not text_ast_nodes and not top_level_params:
            return models.GenerateResponse(queryStringDisplay="", url="#", ast=None)

        url_params_list = []
        display_parts = []
        
        for node in text_ast_nodes:
            generated_str = generator.generate(QueryRootNode(query=node))
            if generated_str:
                url_params_list.append(UrlParam('q', generated_str).to_string())
                # --- THIS IS THE FIX ---
                # Always wrap expressions from the search term boxes in parentheses for clarity
                # and to ensure they are treated as a distinct group.
                display_parts.append(f"({generated_str})")

        for param in top_level_params:
            url_params_list.append(param.to_string())
            if param.key == "litigated" and param.value == "true":
                 display_parts.append("is:litigated")
            else:
                display_parts.append(f"{param.key}:{param.value}")
        
        final_url_query = "&".join(url_params_list)
        url = f"https://patents.google.com/?{final_url_query}" if final_url_query else "#"
        final_display_string = " ".join(display_parts)

        field_ast_nodes = _create_field_nodes_from_params(top_level_params)
        all_nodes = text_ast_nodes + field_ast_nodes
        
        final_ast = None
        if all_nodes:
            combined_query_node = BooleanOpNode("AND", all_nodes) if len(all_nodes) > 1 else all_nodes[0]
            final_ast = QueryRootNode(query=combined_query_node).to_dict()

        return models.GenerateResponse(queryStringDisplay=final_display_string, url=url, ast=final_ast)

    elif req.format == "uspto":
        generator = GENERATORS["uspto"]
        ast_nodes, _ = _build_query_components(req)
        
        if not ast_nodes:
             return models.GenerateResponse(queryStringDisplay="", url="#", ast=None)

        combined_query_node = BooleanOpNode("AND", ast_nodes) if len(ast_nodes) > 1 else ast_nodes[0]
        query_root = QueryRootNode(query=combined_query_node)
        combined_query = generator.generate(query_root)
        url_query_param = quote_plus(combined_query)
        url = f"https://ppubs.uspto.gov/pubwebapp/static/pages/ppubsadvanced.html?query={url_query_param}" if url_query_param else "#"
        return models.GenerateResponse(queryStringDisplay=combined_query, url=url, ast=query_root.to_dict())
    else:
        raise HTTPException(status_code=400, detail=f"Invalid format for generation: {req.format}")


def _extract_field_data(node: ASTNode) -> Tuple[List[ASTNode], Optional[ASTNode]]:
    """
    Recursively walks an AST, separating nodes that belong in the structured
    search form from the nodes that represent the free-text query part.
    """
    field_nodes: List[ASTNode] = []

    def is_field_form_node(n: ASTNode) -> bool:
        if isinstance(n, FieldedSearchNode):
            return n.field_canonical_name in [
                "inventor_name", "assignee_name", "country_code", 
                "language", "status", "patent_type"
            ]
        if isinstance(n, DateSearchNode):
            return True
        if isinstance(n, TermNode) and n.value.lower() == "is:litigated":
            return True
        return False

    def walk(current_node: ASTNode) -> Optional[ASTNode]:
        nonlocal field_nodes
        
        if is_field_form_node(current_node):
            field_nodes.append(current_node)
            return None

        if isinstance(current_node, BooleanOpNode):
            new_operands = [walk(op) for op in current_node.operands]
            new_operands_filtered = [op for op in new_operands if op is not None]
            
            if not new_operands_filtered:
                return None
            if len(new_operands_filtered) == 1:
                return new_operands_filtered[0]
            
            current_node.operands = new_operands_filtered
            return current_node
        
        return current_node

    remaining_ast = walk(node)
    return field_nodes, remaining_ast


def parse_query(req: models.ParseRequest) -> models.ParseResponse:
    if req.format not in PARSERS:
        raise HTTPException(status_code=400, detail=f"No parser available for format: {req.format}")

    parser = PARSERS[req.format]
    generator = GENERATORS[req.format]
    
    ast_root = parser.parse(req.queryString)
    if isinstance(ast_root.query, TermNode) and ast_root.query.value.startswith("PARSE_ERROR"):
        return models.ParseResponse(
            searchConditions=[models.SearchCondition(
                id=str(uuid.uuid4()), type="TEXT", data={"type": "TEXT", "text": req.queryString, "error": ast_root.query.value}
            )],
            googleLikeFields=models.GoogleLikeSearchFields(dateFrom="", dateTo="", dateType="publication", inventors=[], assignees=[], patentOffices=[], languages=[], status="", patentType="", litigation=""),
            usptoSpecificSettings=models.UsptoSpecificSettings(defaultOperator="AND", plurals=False, britishEquivalents=True, selectedDatabases=['US-PGPUB', 'USPAT', 'USOCR'], highlights='SINGLE_COLOR', showErrors=True)
        )

    field_nodes, text_query_ast = _extract_field_data(ast_root.query)

    glf = models.GoogleLikeSearchFields(dateFrom="", dateTo="", dateType="publication", inventors=[], assignees=[], patentOffices=[], languages=[], status="", patentType="", litigation="")
    for node in field_nodes:
        if isinstance(node, FieldedSearchNode) and isinstance(node.query, TermNode):
            val = node.query.value
            if node.field_canonical_name == "inventor_name": glf.inventors.extend([models.DynamicEntry(id=str(uuid.uuid4()), value=v.strip()) for v in val.split(',') if v.strip()])
            elif node.field_canonical_name == "assignee_name": glf.assignees.extend([models.DynamicEntry(id=str(uuid.uuid4()), value=v.strip()) for v in val.split(',') if v.strip()])
            elif node.field_canonical_name == "country_code": glf.patentOffices.extend([v.strip() for v in val.split(',') if v.strip()])
            elif node.field_canonical_name == "language": glf.languages.extend([v.strip().upper() for v in val.split(',') if v.strip()])
            elif node.field_canonical_name == "status": glf.status = val.upper()
            elif node.field_canonical_name == "patent_type": glf.patentType = val.upper()
        elif isinstance(node, DateSearchNode):
            date_obj = node.date_value
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
    if text_query_ast:
        text_search_string = generator.generate(QueryRootNode(query=text_query_ast))
        
    return models.ParseResponse(
        searchConditions=[models.SearchCondition(
            id=str(uuid.uuid4()), type="TEXT", data={"type": "TEXT", "text": text_search_string}
        )],
        googleLikeFields=glf,
        usptoSpecificSettings=models.UsptoSpecificSettings(defaultOperator="AND", plurals=False, britishEquivalents=True, selectedDatabases=['US-PGPUB', 'USPAT', 'USOCR'], highlights='SINGLE_COLOR', showErrors=True)
    )

def convert_query_service(req: models.ConvertRequest) -> models.ConvertResponse:
    try:
        source_parser = PARSERS[req.source_format]
        target_generator = GENERATORS[req.target_format]
        ast = source_parser.parse(req.query_string)
        
        if isinstance(ast.query, TermNode) and ast.query.value.startswith("PARSE_ERROR"):
            return models.ConvertResponse(converted_text=None, error=f"Could not parse source query: {ast.query.value}", settings={})

        converted_text = target_generator.generate(ast)
        return models.ConvertResponse(converted_text=converted_text, error=None, settings={})
    except Exception as e:
        return models.ConvertResponse(converted_text=None, error=str(e), settings={})