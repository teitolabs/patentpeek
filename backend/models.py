# /backend/models.py
from pydantic import BaseModel, Field
from typing import List, Union, Optional, Dict, Any, Literal
import uuid

# --- Models for Structured Search Conditions (from frontend) ---

# Simplified to only include 'text' as other fields were unused.
class TextSearchData(BaseModel):
    type: Literal["TEXT"]
    text: str

# The SearchCondition model is now greatly simplified.
class SearchCondition(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: Literal["TEXT"]
    data: TextSearchData

# --- Models for Form Fields ---

class DynamicEntry(BaseModel):
    id: str
    value: str

class GoogleLikeSearchFields(BaseModel):
    dateFrom: str
    dateTo: str
    dateType: str
    inventors: List[DynamicEntry]
    assignees: List[DynamicEntry]
    patentOffices: List[str]
    languages: List[str]
    status: str
    patentType: str
    litigation: str
    
class UsptoSpecificSettings(BaseModel):
    defaultOperator: str
    plurals: bool
    britishEquivalents: bool
    selectedDatabases: List[str]
    highlights: str
    showErrors: bool

# --- Request/Response Models for API Endpoints ---

class GenerateRequest(BaseModel):
    format: Literal["google", "uspto"]
    searchConditions: List[SearchCondition]
    googleLikeFields: Optional[GoogleLikeSearchFields] = None
    usptoSpecificSettings: Optional[UsptoSpecificSettings] = None

class GenerateResponse(BaseModel):
    queryStringDisplay: str
    url: str
    ast: Optional[Dict[str, Any]] = None # <-- ADDED

class ParseRequest(BaseModel):
    format: Literal["google", "uspto"]
    queryString: str

class ParseResponse(BaseModel):
    searchConditions: List[SearchCondition]
    googleLikeFields: GoogleLikeSearchFields
    usptoSpecificSettings: UsptoSpecificSettings

class ConvertRequest(BaseModel):
    query_string: str
    source_format: Literal["google", "uspto"]
    target_format: Literal["google", "uspto"]

class ConvertResponse(BaseModel):
    converted_text: Optional[str] = None
    error: Optional[str] = None
    settings: Dict[str, Any]