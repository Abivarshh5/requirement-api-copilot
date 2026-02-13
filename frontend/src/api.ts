// API client for communicating with the FastAPI backend

import type { GenerateResponse, RefineResponse, HistoryResponse } from './types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class ApiError extends Error {
    status: number;
    details: Record<string, unknown>;

    constructor(status: number, message: string, details: Record<string, unknown> = {}) {
        super(message);
        this.status = status;
        this.details = details;
    }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE}${path}`;
    const res = await fetch(url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options.headers,
        },
    });

    const data = await res.json();

    if (!res.ok) {
        throw new ApiError(
            res.status,
            data.message || data.error || 'Request failed',
            data
        );
    }

    return data as T;
}

export async function generateSpec(
    requirementsText: string,
    options: { include_examples?: boolean; prioritization_mode?: string } = {}
): Promise<GenerateResponse> {
    return request<GenerateResponse>('/api/specs/generate', {
        method: 'POST',
        body: JSON.stringify({
            requirements_text: requirementsText,
            options: {
                include_examples: options.include_examples ?? true,
                prioritization_mode: options.prioritization_mode ?? 'balanced',
            },
        }),
    });
}

export async function refineSpec(
    traceId: string,
    existingSpec: Record<string, unknown>,
    refinementInstructions: string,
    options: { preserve_ids?: boolean; merge_strategy?: string } = {}
): Promise<RefineResponse> {
    return request<RefineResponse>('/api/specs/refine', {
        method: 'POST',
        body: JSON.stringify({
            trace_id: traceId,
            existing_spec: existingSpec,
            refinement_instructions: refinementInstructions,
            options: {
                preserve_ids: options.preserve_ids ?? true,
                merge_strategy: options.merge_strategy ?? 'merge',
            },
        }),
    });
}

export async function getHistory(traceId: string): Promise<HistoryResponse> {
    return request<HistoryResponse>(`/api/specs/${traceId}/history`);
}

export async function healthCheck(): Promise<Record<string, unknown>> {
    return request<Record<string, unknown>>('/health');
}

export { ApiError };
