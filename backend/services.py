# /backend/services.py
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from pyparsing import ParseException
import uuid
import pprint # Import the pretty-print library

import models
from ast_nodes import (
    ASTNode, QueryRootNode, TermNode, BooleanOpNode, ProximityOpNode,
    FieldedSearchNode, DateSearchNode, ClassificationNode
)
# We will use the placeholder versions of the parsers and generators for now
from google_parser import GoogleQueryParser
from google_generator import ASTToGoogleQueryGenerator
from uspto_parser import USPTOQueryParser
from uspto_generator import ASTToUSPTOQueryGenerator

# --- Helper to Build AST from Structured JSON ---
# This function converts the frontend's state into a universal AST
def _build_ast_from_structure(req: models.GenerateRequest) -> QueryRootNode:
    query_nodes: List[ASTNode] = []

    # 1. Process the main search conditions (text boxes, classifications, etc.)
    if req.searchConditions:
        for condition in req.searchConditions:
            # --- Handle TEXT conditions ---
            if condition.type == "TEXT":
                text_data = condition.data
                if not text_data.text.strip():
                    continue

                # For simplicity, we'll treat the whole text as a single TermNode for now.
                # A more advanced version would parse operators within the text.
                text_node = TermNode(text_data.text.strip())
                
                # For now, we assume the scope is always Full Text (FT)
                # and don't create fielded nodes for TI, AB, CL yet.
                query_nodes.append(text_node)

            # --- Handle CLASSIFICATION conditions ---
            elif condition.type == "CLASSIFICATION":
                cpc_data = condition.data
                if not cpc_data.cpc.strip():
                    continue
                
                # Create a ClassificationNode for the CPC data
                cpc_ast_node = ClassificationNode(
                    scheme="CPC",
                    value=cpc_data.cpc.strip(),
                    include_children=(cpc_data.option == "CHILDREN")
                )
                # Wrap it in a FieldedSearchNode
                query_nodes.append(FieldedSearchNode("cpc", cpc_ast_node, system_field_code="CPC"))

    # 2. Process the Google-like specific fields (dates, inventors, assignees)
    if req.googleLikeFields:
        fields = req.googleLikeFields
        
        # --- Handle Inventors ---
        if fields.inventors:
            # Create a TermNode for each inventor and wrap it in a FieldedSearchNode
            inv_nodes = [
                FieldedSearchNode("inventor_name", TermNode(inv.value, is_phrase=True)) 
                for inv in fields.inventors if inv.value.strip()
            ]
            # If there are multiple inventors, OR them together
            if len(inv_nodes) == 1:
                query_nodes.append(inv_nodes[0])
            elif len(inv_nodes) > 1:
                query_nodes.append(BooleanOpNode("OR", inv_nodes))

        # --- Handle Assignees ---
        if fields.assignees:
            asg_nodes = [
                FieldedSearchNode("assignee_name", TermNode(asg.value, is_phrase=True))
                for asg in fields.assignees if asg.value.strip()
            ]
            if len(asg_nodes) == 1:
                query_nodes.append(asg_nodes[0])
            elif len(asg_nodes) > 1:
                query_nodes.append(BooleanOpNode("OR", asg_nodes))

        # --- Handle Dates ---
        # Map the UI dateType to the canonical field name used in our AST
        date_map = {"publication": "publication_date", "filing": "application_date", "priority": "priority_date"}
        canonical_date_field = date_map.get(fields.dateType)

        if canonical_date_field:
            # Handle the 'From' date (e.g., after:2022-01-15)
            if fields.dateFrom:
                # Convert YYYY-MM-DD to YYYYMMDD for the AST
                date_val = fields.dateFrom.replace("-", "")
                query_nodes.append(DateSearchNode(canonical_date_field, ">=", date_val)) # type: ignore
            
            # Handle the 'To' date (e.g., before:2023-12-31)
            if fields.dateTo:
                date_val = fields.dateTo.replace("-", "")
                query_nodes.append(DateSearchNode(canonical_date_field, "<=", date_val)) # type: ignore

    # 3. Combine all collected nodes into a single root
    if not query_nodes:
        return QueryRootNode(query=TermNode("__EMPTY__"))
    if len(query_nodes) == 1:
        return QueryRootNode(query=query_nodes[0])
    
    # Default to ANDing all top-level conditions together
    return QueryRootNode(query=BooleanOpNode(operator="AND", operands=query_nodes))


# --- Public Service Functions ---

def generate_query(req: models.GenerateRequest) -> models.GenerateResponse:
    """
    Builds an AST from the request and prints it to the console.
    Then, uses a placeholder generator to return a response.
    """
    # This function now correctly builds the AST from the UI state
    ast_root = _build_ast_from_structure(req)

    # --- FEATURE 2: Display the mapped structure in the console ---
    print("\n--- GENERATED AST ---")
    # Use pprint for a more readable, multi-line output of the AST
    pprint.pprint(ast_root.to_dict())
    print("---------------------\n")

    # The rest of the logic uses the placeholder generators for now
    if req.format == "google":
        generator = ASTToGoogleQueryGenerator()
        query_string = generator.generate(ast_root)
        url = "#" # Placeholder URL
    elif req.format == "uspto":
        generator = ASTToUSPTOQueryGenerator()
        query_string = generator.generate(ast_root)
        url = "#" # Placeholder URL
    else:
        raise HTTPException(status_code=400, detail=f"Invalid format for generation: {req.format}")
    
    return models.GenerateResponse(queryStringDisplay=query_string, url=url)

def parse_query(req: models.ParseRequest) -> models.ParseResponse:
    """
    Placeholder: Returns a default, empty state for the UI.
    """
    default_text_condition = models.SearchCondition(
        type="TEXT",
        data=models.TextSearchData(
            type="TEXT", text=f"Parsed: {req.queryString}",
            selectedScopes=['FT'], termOperator='ALL'
        )
    )
    default_google_fields = models.GoogleLikeSearchFields(
        dateFrom="", dateTo="", dateType="publication", inventors=[], assignees=[],
        patentOffices=[], languages=[], status="", patentType="", litigation=""
    )
    default_uspto_settings = models.UsptoSpecificSettings(
        defaultOperator="AND", plurals=False, britishEquivalents=True,
        selectedDatabases=['US-PGPUB', 'USPAT', 'USOCR'],
        highlights="SINGLE_COLOR", showErrors=True
    )
    return models.ParseResponse(
        searchConditions=[default_text_condition],
        googleLikeFields=default_google_fields,
        usptoSpecificSettings=default_uspto_settings
    )

def convert_query_service(req: models.ConvertRequest) -> models.ConvertResponse:
    """
    Placeholder: Returns a simple string indicating the conversion requested.
    """
    converted_text = (
        f"Placeholder conversion of '{req.query_string}' "
        f"from '{req.source_format}' to '{req.target_format}'"
    )
    return models.ConvertResponse(converted_text=converted_text, settings={})