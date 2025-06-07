
# /backend/services.py
from typing import List, Dict, Any, Optional, Tuple
from fastapi import HTTPException
from pyparsing import ParseException
import uuid
import pprint
from urllib.parse import quote_plus
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

# --- MODIFIED: Helper now returns a tuple with a flag ---
def _build_ast_from_structure(req: models.GenerateRequest) -> Tuple[QueryRootNode, bool]:
    query_nodes: List[ASTNode] = []
    user_started_with_paren = False

    if req.searchConditions:
        for condition in req.searchConditions:
            if condition.type == "TEXT":
                text_data = condition.data
                text_input = text_data.text.strip()
                if not text_input:
                    continue

                # --- NEW: Check if the user provided their own parenthesis ---
                if text_input.startswith('('):
                    user_started_with_paren = True

                try:
                    parsed_ast_root = TEXT_BOX_PARSER.parse(text_input)
                    if not isinstance(parsed_ast_root.query, TermNode) or parsed_ast_root.query.value != "__EMPTY__":
                         query_nodes.append(parsed_ast_root.query)
                except Exception as e:
                    print(f"Could not parse text box content '{text_input}': {e}")
                    # Create an error node to display the parsing issue to the user
                    query_nodes.append(TermNode(f"PARSE_ERROR: {e}"))

            elif condition.type == "CLASSIFICATION":
                cpc_data = condition.data
                if not cpc_data.cpc.strip():
                    continue
                cpc_ast_node = ClassificationNode(
                    scheme="CPC",
                    value=cpc_data.cpc.strip(),
                    include_children=(cpc_data.option == "CHILDREN")
                )
                query_nodes.append(FieldedSearchNode("cpc", cpc_ast_node, system_field_code="CPC"))

    if req.googleLikeFields:
        fields = req.googleLikeFields
        if fields.inventors:
            inv_nodes = [FieldedSearchNode("inventor_name", TermNode(inv.value, is_phrase=True)) for inv in fields.inventors if inv.value.strip()]
            if len(inv_nodes) == 1: query_nodes.append(inv_nodes[0])
            elif len(inv_nodes) > 1: query_nodes.append(BooleanOpNode("OR", inv_nodes))
        if fields.assignees:
            asg_nodes = [FieldedSearchNode("assignee_name", TermNode(asg.value, is_phrase=True)) for asg in fields.assignees if asg.value.strip()]
            if len(asg_nodes) == 1: query_nodes.append(asg_nodes[0])
            elif len(asg_nodes) > 1: query_nodes.append(BooleanOpNode("OR", asg_nodes))
        if fields.dateType and (fields.dateFrom or fields.dateTo):
            canonical_date_field = ""
            if fields.dateType == "publication": canonical_date_field = "publication_date"
            elif fields.dateType == "filing": canonical_date_field = "application_date"
            elif fields.dateType == "priority": canonical_date_field = "priority_date"
            if canonical_date_field:
                if fields.dateFrom:
                    date_from_cleaned = fields.dateFrom.replace("-", "")
                    if date_from_cleaned.isdigit(): query_nodes.append(DateSearchNode(field_canonical_name=canonical_date_field, operator=">=", date_value=date_from_cleaned)) #type: ignore
                if fields.dateTo:
                    date_to_cleaned = fields.dateTo.replace("-", "")
                    if date_to_cleaned.isdigit(): query_nodes.append(DateSearchNode(field_canonical_name=canonical_date_field, operator="<=", date_value=date_to_cleaned)) #type: ignore
        if fields.patentOffices:
            office_nodes = [FieldedSearchNode("country_code", TermNode(office)) for office in fields.patentOffices]
            if len(office_nodes) == 1: query_nodes.append(office_nodes[0])
            elif len(office_nodes) > 1: query_nodes.append(BooleanOpNode("OR", office_nodes))
        if fields.languages:
            lang_nodes = [FieldedSearchNode("language", TermNode(lang.lower())) for lang in fields.languages]
            if len(lang_nodes) == 1: query_nodes.append(lang_nodes[0])
            elif len(lang_nodes) > 1: query_nodes.append(BooleanOpNode("OR", lang_nodes))
        if fields.status: query_nodes.append(FieldedSearchNode("status", TermNode(fields.status.lower())))
        if fields.patentType: query_nodes.append(FieldedSearchNode("patent_type", TermNode(fields.patentType.lower())))
        if fields.litigation == "YES": query_nodes.append(TermNode("is:litigated"))

    ast_root: QueryRootNode
    if not query_nodes:
        ast_root = QueryRootNode(query=TermNode("__EMPTY__"))
    elif len(query_nodes) == 1:
        ast_root = QueryRootNode(query=query_nodes[0])
    else:
        ast_root = QueryRootNode(query=BooleanOpNode(operator="AND", operands=query_nodes))
    
    return ast_root, user_started_with_paren


def generate_query(req: models.GenerateRequest) -> models.GenerateResponse:
    ast_root, user_started_with_paren = _build_ast_from_structure(req)

    print("\n--- GENERATED AST ---")
    pprint.pprint(ast_root.to_dict())
    print("---------------------\n")

    if req.format == "google":
        generator = ASTToGoogleQueryGenerator()
        
        # Generate the base string for both display and URL (using implicit ANDs)
        base_query_string = generator.generate(ast_root, use_implicit_and=True)
        
        # Logic for the final display string
        display_string = base_query_string
        if base_query_string and not user_started_with_paren:
            # Add parentheses by default if the user didn't provide them
            display_string = f"({base_query_string})"
        
        # The URL string is just the base string, which then gets encoded
        url_string = base_query_string
        url_query_param = quote_plus(url_string)
        url = f"https://patents.google.com/?q={url_query_param}" if url_query_param else "#"
        
        return models.GenerateResponse(queryStringDisplay=display_string, url=url)

    elif req.format == "uspto":
        generator = ASTToUSPTOQueryGenerator()
        query_string = generator.generate(ast_root)
        url_query_param = quote_plus(query_string)
        url = f"https://ppubs.uspto.gov/pubwebapp/static/pages/ppubsadvanced.html?query={url_query_param}" if url_query_param else "#"
        return models.GenerateResponse(queryStringDisplay=query_string, url=url)
    else:
        raise HTTPException(status_code=400, detail=f"Invalid format for generation: {req.format}")


def parse_query(req: models.ParseRequest) -> models.ParseResponse:
    parser = GoogleQueryParser()
    ast_root = parser.parse(req.queryString)
    raise HTTPException(status_code=501, detail="Parsing from string not fully implemented yet.")

def convert_query_service(req: models.ConvertRequest) -> models.ConvertResponse:
    converted_text = f"Placeholder conversion of '{req.query_string}'"
    return models.ConvertResponse(converted_text=converted_text, settings={})