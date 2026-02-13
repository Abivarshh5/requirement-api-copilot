"""
Pydantic models for the API Copilot output specification schema.
Every field is strictly typed for validation of LLM-generated JSON.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum


# ── Enums ──────────────────────────────────────────────────────────────

class Priority(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"

class Complexity(str, Enum):
    simple = "simple"
    moderate = "moderate"
    complex = "complex"

class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"

class AuthRequirement(str, Enum):
    required = "required"
    optional = "optional"
    none = "none"

class RelationshipType(str, Enum):
    one_to_many = "one-to-many"
    many_to_one = "many-to-one"
    many_to_many = "many-to-many"

class QuestionCategory(str, Enum):
    authentication = "authentication"
    business_logic = "business_logic"
    data_model = "data_model"
    integration = "integration"
    other = "other"

class MergeStrategy(str, Enum):
    replace = "replace"
    merge = "merge"
    append = "append"

class PrioritizationMode(str, Enum):
    strict = "strict"
    balanced = "balanced"
    lenient = "lenient"


# ── Module & Feature Models ───────────────────────────────────────────

class Module(BaseModel):
    module_id: str
    name: str
    description: str
    priority: Priority


class Feature(BaseModel):
    feature_id: str
    name: str
    description: str
    priority: Priority
    complexity: Complexity


# ── User Story Model ─────────────────────────────────────────────────

class UserStory(BaseModel):
    story_id: str
    module_id: str
    feature_id: str
    as_a: str
    i_want: str
    so_that: str
    acceptance_criteria: List[str]
    priority: Priority


# ── API Endpoint Models ──────────────────────────────────────────────

class ErrorResponse(BaseModel):
    status_code: int
    description: str
    body: Optional[Dict[str, Any]] = None


class SuccessResponse(BaseModel):
    status_code: int
    body: Optional[Dict[str, Any]] = None


class EndpointResponse(BaseModel):
    success: SuccessResponse
    errors: List[ErrorResponse] = []


class EndpointRequest(BaseModel):
    headers: Optional[Dict[str, str]] = None
    query_params: Optional[Dict[str, str]] = None
    body: Optional[Dict[str, Any]] = None


class ApiEndpoint(BaseModel):
    endpoint_id: str
    method: HttpMethod
    path: str
    description: str
    authentication: AuthRequirement
    authorization: Optional[str] = None
    request: Optional[EndpointRequest] = None
    response: EndpointResponse
    related_stories: List[str] = []


# ── Database Schema Models ───────────────────────────────────────────

class Column(BaseModel):
    name: str
    type: str
    nullable: bool = False
    primary_key: bool = False
    foreign_key: Optional[str] = None
    default: Optional[Any] = None
    constraints: List[str] = []


class Index(BaseModel):
    name: str
    columns: List[str]
    unique: bool = False


class Relationship(BaseModel):
    type: RelationshipType
    target_table: str
    description: str


class DbTable(BaseModel):
    table_name: str
    description: str
    columns: List[Column]
    indexes: List[Index] = []
    relationships: List[Relationship] = []


# ── Open Questions & Contradictions ──────────────────────────────────

class OpenQuestion(BaseModel):
    question_id: str
    category: QuestionCategory
    question: str
    context: str
    priority: Priority


class Contradiction(BaseModel):
    description: str
    conflicting_items: List[str]
    suggested_resolution: Optional[str] = None


# ── Metadata ─────────────────────────────────────────────────────────

class Metadata(BaseModel):
    original_requirements_length: int = 0
    processing_time_ms: int = 0
    llm_model: str = ""
    total_retries: int = 0


# ── Top-Level Spec Output ────────────────────────────────────────────

class SpecOutput(BaseModel):
    trace_id: str
    version: int = 1
    timestamp: str
    modules: List[Module] = []
    features_by_module: Dict[str, List[Feature]] = {}
    user_stories: List[UserStory] = []
    api_endpoints: List[ApiEndpoint] = []
    db_schema: List[DbTable] = []
    open_questions: List[OpenQuestion] = []
    contradictions: List[Contradiction] = []
    metadata: Metadata = Metadata()


# ── Request / Response Models for the API itself ─────────────────────

class GenerateOptions(BaseModel):
    include_examples: bool = True
    prioritization_mode: PrioritizationMode = PrioritizationMode.balanced

class GenerateRequest(BaseModel):
    requirements_text: str = Field(..., min_length=50, max_length=10000)
    user_id: Optional[str] = None
    options: GenerateOptions = GenerateOptions()

class GenerateResponse(BaseModel):
    trace_id: str
    status: str = "success"
    spec: SpecOutput
    processing_time_ms: int
    warnings: List[str] = []

class RefineOptions(BaseModel):
    preserve_ids: bool = True
    merge_strategy: MergeStrategy = MergeStrategy.merge

class RefineRequest(BaseModel):
    trace_id: str
    existing_spec: dict
    refinement_instructions: str = Field(..., min_length=5, max_length=5000)
    options: RefineOptions = RefineOptions()

class RefineResponse(BaseModel):
    trace_id: str
    parent_trace_id: str
    version: int
    status: str = "success"
    spec: SpecOutput
    changes_summary: Dict[str, Any] = {}

class VersionSummary(BaseModel):
    version: int
    timestamp: str
    refinement_instructions: Optional[str] = None
    spec_summary: Dict[str, Any] = {}

class HistoryResponse(BaseModel):
    trace_id: str
    versions: List[VersionSummary] = []

class ErrorDetail(BaseModel):
    error: str
    message: str
    details: Optional[Any] = None
    trace_id: Optional[str] = None
    retry_after: Optional[int] = None
    suggestions: Optional[List[str]] = None
