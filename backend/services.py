
# /backend/services.py
from typing import List, Dict, Any, Optional
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

def _build_ast_groups(req: models.GenerateRequest) -> List[QueryRootNode]:
    """
    Processes the request and builds a list of separate query groups.
    Each TEXT condition becomes its own group. All other fields are
    combined into a single, final group.
    """
    text_query_groups: List[ASTNode] = []
    other_field_nodes: List[ASTNode] = []

    # 1. Process TEXT search conditions into separate, individual groups
    if req.searchConditions:
        for condition in req.searchConditions:
            if condition.type == "TEXT":
                text_data = condition.data
                text_input = text_data.text.strip()
                if not text_input:
                    continue
                
                parsed_ast_root = TEXT_BOX_PARSER.parse(text_input)
                
                if not isinstance(parsed_ast_root.query, TermNode) or parsed_ast_root.query.value != "__EMPTY__":
                    text_query_groups.append(parsed_ast_root.query)
            
            elif condition.type == "CLASSIFICATION":
                cpc_data = condition.data
                if not cpc_data.cpc.strip():
                    continue
                cpc_ast_node = ClassificationNode(
                    scheme="CPC",
                    value=cpc_data.cpc.strip(),
                    include_children=(cpc_data.option == "CHILDREN")
                )
                other_field_nodes.append(FieldedSearchNode("cpc", cpc_ast_node, system_field_code="CPC"))

    # 2. Collect all Google-like fields into the same "other" list
    if req.googleLikeFields:
        fields = req.googleLikeFields
        if fields.inventors:
            inv_nodes = [FieldedSearchNode("inventor_name", TermNode(inv.value, is_phrase=True)) for inv in fields.inventors if inv.value.strip()]
            if len(inv_nodes) == 1: other_field_nodes.append(inv_nodes[0])
            elif len(inv_nodes) > 1: other_field_nodes.append(BooleanOpNode("OR", inv_nodes))
        if fields.assignees:
            asg_nodes = [FieldedSearchNode("assignee_name", TermNode(asg.value, is_phrase=True)) for asg in fields.assignees if asg.value.strip()]
            if len(asg_nodes) == 1: other_field_nodes.append(asg_nodes[0])
            elif len(asg_nodes) > 1: other_field_nodes.append(BooleanOpNode("OR", asg_nodes))
        if fields.dateType and (fields.dateFrom or fields.dateTo):
            canonical_date_field = ""
            if fields.dateType == "publication": canonical_date_field = "publication_date"
            elif fields.dateType == "filing": canonical_date_field = "application_date"
            elif fields.dateType == "priority": canonical_date_field = "priority_date"
            if canonical_date_field:
                if fields.dateFrom:
                    df = fields.dateFrom.replace("-", "")
                    if df.isdigit(): other_field_nodes.append(DateSearchNode(canonical_date_field, ">=", df)) #type: ignore
                if fields.dateTo:
                    dt = fields.dateTo.replace("-", "")
                    if dt.isdigit(): other_field_nodes.append(DateSearchNode(canonical_date_field, "<=", dt)) #type: ignore
        if fields.patentOffices:
            nodes = [FieldedSearchNode("country_code", TermNode(o)) for o in fields.patentOffices]
            if len(nodes) == 1: other_field_nodes.append(nodes[0])
            elif len(nodes) > 1: other_field_nodes.append(BooleanOpNode("OR", nodes))
        if fields.languages:
            nodes = [FieldedSearchNode("language", TermNode(lang.lower())) for lang in fields.languages]
            if len(nodes) == 1: other_field_nodes.append(nodes[0])
            elif len(nodes) > 1: other_field_nodes.append(BooleanOpNode("OR", nodes))
        if fields.status: other_field_nodes.append(FieldedSearchNode("status", TermNode(fields.status.lower())))
        if fields.patentType: other_field_nodes.append(FieldedSearchNode("patent_type", TermNode(fields.patentType.lower())))
        if fields.litigation == "YES": other_field_nodes.append(TermNode("is:litigated"))

    # 3. Combine all collected groups
    all_groups = text_query_groups
    if other_field_nodes:
        if len(other_field_nodes) == 1:
            all_groups.append(other_field_nodes[0])
        else:
            all_groups.append(BooleanOpNode("AND", other_field_nodes))

    return [QueryRootNode(query=node) for node in all_groups if node]


def generate_query(req: models.GenerateRequest) -> models.GenerateResponse:
    ast_groups = _build_ast_groups(req)

    if not ast_groups:
        return models.GenerateResponse(queryStringDisplay="", url="#")

    if req.format == "google":
        generator = ASTToGoogleQueryGenerator()
        display_parts = []
        url_q_params = []

        for ast_root in ast_groups:
            # 1. Generate the unambiguous, explicit query string (e.g., "(a AND a) AND a")
            explicit_string = generator.generate(ast_root)
            if not explicit_string:
                continue

            # 2. Convert to Google's implicit syntax (e.g., "(a a) a")
            google_syntax_string = explicit_string.replace(" AND ", " ")
            
            # 3. For the URL, use the Google syntax string directly
            url_q_params.append(f"q={quote_plus(google_syntax_string)}")

            # 4. For the display, apply the final wrapping rule
            display_string_for_group = google_syntax_string
            # Wrap in parentheses if the string doesn't already contain any.
            if '(' not in display_string_for_group and not display_string_for_group.startswith("PARSE_ERROR"):
                 display_string_for_group = f"({display_string_for_group})"

            display_parts.append(display_string_for_group)

        # Join the parts for the final output
        final_display_string = " ".join(display_parts)
        final_url_query = "&".join(url_q_params)
        url = f"https://patents.google.com/?{final_url_query}" if final_url_query else "#"
        
        return models.GenerateResponse(queryStringDisplay=final_display_string, url=url)

    elif req.format == "uspto":
        generator = ASTToUSPTOQueryGenerator()
        combined_query = " AND ".join([generator.generate(root) for root in ast_groups])
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