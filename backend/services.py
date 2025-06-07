# /backend/services.py
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from pyparsing import ParseException
import uuid
import pprint

import models
from ast_nodes import (
    ASTNode, QueryRootNode, TermNode, BooleanOpNode, ProximityOpNode,
    FieldedSearchNode, DateSearchNode, ClassificationNode
)
from google_parser import GoogleQueryParser
from google_generator import ASTToGoogleQueryGenerator
from uspto_parser import USPTOQueryParser
from uspto_generator import ASTToUSPTOQueryGenerator

# --- Helper to Build AST from Structured JSON ---
def _build_ast_from_structure(req: models.GenerateRequest) -> QueryRootNode:
    query_nodes: List[ASTNode] = []

    if req.searchConditions:
        for condition in req.searchConditions:
            # --- Handle TEXT conditions ---
            if condition.type == "TEXT":
                text_data = condition.data
                text_input = text_data.text.strip()
                if not text_input:
                    continue

                # --- START: CORRECTED PHRASE-HANDLING LOGIC ---
                text_node: Optional[ASTNode] = None

                # Check if the input is an exact phrase (wrapped in quotes)
                if text_input.startswith('"') and text_input.endswith('"'):
                    # Remove the quotes from the value and set the flag
                    phrase_content = text_input[1:-1]
                    if phrase_content: # Ensure it's not just empty quotes ""
                        text_node = TermNode(phrase_content, is_phrase=True)
                else:
                    # If not a phrase, treat as one or more words
                    # A more advanced implementation would parse operators here,
                    # but for now, we'll treat it as a single term.
                    text_node = TermNode(text_input, is_phrase=False)

                if text_node:
                    query_nodes.append(text_node)
                # --- END: CORRECTED PHRASE-HANDLING LOGIC ---

            # --- Handle CLASSIFICATION conditions ---
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

    # 2. Process the Google-like specific fields
    if req.googleLikeFields:
        fields = req.googleLikeFields
        
        if fields.inventors:
            inv_nodes = [
                FieldedSearchNode("inventor_name", TermNode(inv.value, is_phrase=True)) 
                for inv in fields.inventors if inv.value.strip()
            ]
            if len(inv_nodes) == 1:
                query_nodes.append(inv_nodes[0])
            elif len(inv_nodes) > 1:
                query_nodes.append(BooleanOpNode("OR", inv_nodes))

        if fields.assignees:
            asg_nodes = [
                FieldedSearchNode("assignee_name", TermNode(asg.value, is_phrase=True))
                for asg in fields.assignees if asg.value.strip()
            ]
            if len(asg_nodes) == 1:
                query_nodes.append(asg_nodes[0])
            elif len(asg_nodes) > 1:
                query_nodes.append(BooleanOpNode("OR", asg_nodes))

        date_map = {"publication": "publication_date", "filing": "application_date", "priority": "priority_date"}
        canonical_date_field = date_map.get(fields.dateType)
        if canonical_date_field:
            if fields.dateFrom:
                date_val = fields.dateFrom.replace("-", "")
                query_nodes.append(DateSearchNode(canonical_date_field, ">=", date_val)) # type: ignore
            if fields.dateTo:
                date_val = fields.dateTo.replace("-", "")
                query_nodes.append(DateSearchNode(canonical_date_field, "<=", date_val)) # type: ignore

        if fields.patentOffices:
            office_nodes = [
                FieldedSearchNode("country_code", TermNode(office)) 
                for office in fields.patentOffices
            ]
            if len(office_nodes) == 1:
                query_nodes.append(office_nodes[0])
            elif len(office_nodes) > 1:
                query_nodes.append(BooleanOpNode("OR", office_nodes))

        if fields.languages:
            lang_nodes = [
                FieldedSearchNode("language", TermNode(lang.lower()))
                for lang in fields.languages
            ]
            if len(lang_nodes) == 1:
                query_nodes.append(lang_nodes[0])
            elif len(lang_nodes) > 1:
                query_nodes.append(BooleanOpNode("OR", lang_nodes))

        if fields.status:
            query_nodes.append(FieldedSearchNode("status", TermNode(fields.status.lower())))

        if fields.patentType:
            query_nodes.append(FieldedSearchNode("patent_type", TermNode(fields.patentType.lower())))

        if fields.litigation == "YES":
            query_nodes.append(TermNode("is:litigated"))
        
    # 3. Combine all collected nodes into a single root
    if not query_nodes:
        return QueryRootNode(query=TermNode("__EMPTY__"))
    if len(query_nodes) == 1:
        return QueryRootNode(query=query_nodes[0])
    
    return QueryRootNode(query=BooleanOpNode(operator="AND", operands=query_nodes))


# --- Public Service Functions (Unchanged) ---

def generate_query(req: models.GenerateRequest) -> models.GenerateResponse:
    ast_root = _build_ast_from_structure(req)

    print("\n--- GENERATED AST ---")
    pprint.pprint(ast_root.to_dict())
    print("---------------------\n")

    if req.format == "google":
        generator = ASTToGoogleQueryGenerator()
        query_string = generator.generate(ast_root)
        url = "#"
    elif req.format == "uspto":
        generator = ASTToUSPTOQueryGenerator()
        query_string = generator.generate(ast_root)
        url = "#"
    else:
        raise HTTPException(status_code=400, detail=f"Invalid format for generation: {req.format}")
    
    return models.GenerateResponse(queryStringDisplay=query_string, url=url)

def parse_query(req: models.ParseRequest) -> models.ParseResponse:
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
    converted_text = (
        f"Placeholder conversion of '{req.query_string}' "
        f"from '{req.source_format}' to '{req.target_format}'"
    )
    return models.ConvertResponse(converted_text=converted_text, settings={})