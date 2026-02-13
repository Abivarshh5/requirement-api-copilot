// TypeScript interfaces matching the backend Pydantic models

export type Priority = 'high' | 'medium' | 'low';
export type Complexity = 'simple' | 'moderate' | 'complex';
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
export type AuthRequirement = 'required' | 'optional' | 'none';
export type RelationshipType = 'one-to-many' | 'many-to-one' | 'many-to-many';
export type QuestionCategory = 'authentication' | 'business_logic' | 'data_model' | 'integration' | 'other';

export interface Module {
    module_id: string;
    name: string;
    description: string;
    priority: Priority;
}

export interface Feature {
    feature_id: string;
    name: string;
    description: string;
    priority: Priority;
    complexity: Complexity;
}

export interface UserStory {
    story_id: string;
    module_id: string;
    feature_id: string;
    as_a: string;
    i_want: string;
    so_that: string;
    acceptance_criteria: string[];
    priority: Priority;
}

export interface ErrorResponse {
    status_code: number;
    description: string;
    body?: Record<string, unknown>;
}

export interface SuccessResponse {
    status_code: number;
    body?: Record<string, unknown>;
}

export interface EndpointRequest {
    headers?: Record<string, string>;
    query_params?: Record<string, string>;
    body?: Record<string, unknown>;
}

export interface EndpointResponseSchema {
    success: SuccessResponse;
    errors: ErrorResponse[];
}

export interface ApiEndpoint {
    endpoint_id: string;
    method: HttpMethod;
    path: string;
    description: string;
    authentication: AuthRequirement;
    authorization?: string | null;
    request?: EndpointRequest | null;
    response: EndpointResponseSchema;
    related_stories: string[];
}

export interface Column {
    name: string;
    type: string;
    nullable: boolean;
    primary_key: boolean;
    foreign_key?: string | null;
    default?: unknown;
    constraints: string[];
}

export interface Index {
    name: string;
    columns: string[];
    unique: boolean;
}

export interface Relationship {
    type: RelationshipType;
    target_table: string;
    description: string;
}

export interface DbTable {
    table_name: string;
    description: string;
    columns: Column[];
    indexes: Index[];
    relationships: Relationship[];
}

export interface OpenQuestion {
    question_id: string;
    category: QuestionCategory;
    question: string;
    context: string;
    priority: Priority;
}

export interface Contradiction {
    description: string;
    conflicting_items: string[];
    suggested_resolution?: string | null;
}

export interface SpecMetadata {
    original_requirements_length: number;
    processing_time_ms: number;
    llm_model: string;
    total_retries: number;
}

export interface SpecOutput {
    trace_id: string;
    version: number;
    timestamp: string;
    modules: Module[];
    features_by_module: Record<string, Feature[]>;
    user_stories: UserStory[];
    api_endpoints: ApiEndpoint[];
    db_schema: DbTable[];
    open_questions: OpenQuestion[];
    contradictions: Contradiction[];
    metadata: SpecMetadata;
}

export interface GenerateResponse {
    trace_id: string;
    status: string;
    spec: SpecOutput;
    processing_time_ms: number;
    warnings: string[];
}

export interface RefineResponse {
    trace_id: string;
    parent_trace_id: string;
    version: number;
    status: string;
    spec: SpecOutput;
    changes_summary: Record<string, Record<string, number>>;
    processing_time_ms: number;
}

export interface VersionSummary {
    version: number;
    timestamp: string;
    refinement_instructions?: string | null;
    spec_summary: Record<string, number>;
}

export interface HistoryResponse {
    trace_id: string;
    versions: VersionSummary[];
}

export type TabId = 'modules' | 'stories' | 'endpoints' | 'database' | 'issues';
