"""
API routes for the spec generation service.
POST /api/specs/generate
POST /api/specs/refine
GET  /api/specs/{trace_id}/history
"""

import logging
import time
import traceback

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from models import (
    GenerateRequest, GenerateResponse, RefineRequest, RefineResponse,
    HistoryResponse, SpecOutput
)
from llm_service import LLMService
from rate_limiter import rate_limiter
from storage import save_spec, get_spec, get_history

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/specs")

llm_service = LLMService()


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/generate")
async def generate_spec(body: GenerateRequest, request: Request):
    """Generate a full technical specification from requirements text."""
    ip = _get_client_ip(request)

    # Rate limit check
    allowed, retry_after = rate_limiter.check(ip)
    if not allowed:
        return JSONResponse(status_code=429, content={
            "error": "rate_limit_exceeded",
            "message": f"Maximum {rate_limiter.limit} requests per minute exceeded",
            "retry_after": retry_after
        })

    try:
        start = time.time()

        # Run the LLM pipeline
        spec_dict, total_retries = llm_service.generate_spec(body.requirements_text)

        # Validate through Pydantic (will throw if invalid)
        validated = SpecOutput(**{
            **spec_dict,
            "trace_id": "temp",
            "version": 1,
            "timestamp": "temp",
        })

        # Save to storage
        trace_id, version = save_spec(spec_dict)

        # Re-read saved spec (has trace_id and timestamp set)
        saved_spec = get_spec(trace_id, version)

        processing_ms = int((time.time() - start) * 1000)

        warnings = []
        if spec_dict.get("metadata", {}).get("llm_model") == "mock":
            warnings.append("Generated in mock mode — connect an LLM API key for real analysis")

        return {
            "trace_id": trace_id,
            "status": "success",
            "spec": saved_spec,
            "processing_time_ms": processing_ms,
            "warnings": warnings
        }

    except ValueError as e:
        logger.error(f"Generation error: {e}")
        # Extract the actual cause if it's a quota issue
        err_msg = str(e)
        if "quota" in err_msg.lower() or "429" in err_msg:
            return JSONResponse(status_code=429, content={
                "error": "quota_exceeded",
                "message": "AI service quota exceeded. Please try again later or switch your API key.",
                "details": err_msg
            })
        
        return JSONResponse(status_code=422, content={
            "error": "generation_failed",
            "message": "Unable to generate valid specification from provided requirements",
            "details": err_msg,
            "suggestions": [
                "Provide more specific requirements",
                "Include user roles and actions",
                "Describe at least 2-3 features or user flows"
            ]
        })
    except Exception as e:
        logger.error(f"Generation error: {traceback.format_exc()}")
        return JSONResponse(status_code=500, content={
            "error": "processing_error",
            "message": "Specification generation failed",
            "details": str(e)[:500]
        })


@router.post("/refine")
async def refine_spec(body: RefineRequest, request: Request):
    """Refine an existing specification with new instructions."""
    ip = _get_client_ip(request)

    allowed, retry_after = rate_limiter.check(ip)
    if not allowed:
        return JSONResponse(status_code=429, content={
            "error": "rate_limit_exceeded",
            "message": f"Maximum {rate_limiter.limit} requests per minute exceeded",
            "retry_after": retry_after
        })

    try:
        start = time.time()

        # Run refinement
        refined_dict = llm_service.refine_spec(body.existing_spec, body.refinement_instructions)

        # Save as new version
        parent_trace_id = body.trace_id
        trace_id, version = save_spec(
            refined_dict,
            parent_trace_id=parent_trace_id,
            refinement_instructions=body.refinement_instructions
        )

        saved_spec = get_spec(trace_id, version)
        processing_ms = int((time.time() - start) * 1000)

        # Calculate simple change summary
        old = body.existing_spec
        changes = {
            "added": {},
            "modified": {},
            "removed": {}
        }
        for key in ["modules", "user_stories", "api_endpoints", "db_schema", "open_questions"]:
            old_count = len(old.get(key, []))
            new_count = len(refined_dict.get(key, []))
            if new_count > old_count:
                changes["added"][key] = new_count - old_count
            elif new_count < old_count:
                changes["removed"][key] = old_count - new_count

        return {
            "trace_id": trace_id,
            "parent_trace_id": parent_trace_id,
            "version": version,
            "status": "success",
            "spec": saved_spec,
            "changes_summary": changes,
            "processing_time_ms": processing_ms
        }

    except Exception as e:
        logger.error(f"Refinement error: {traceback.format_exc()}")
        return JSONResponse(status_code=500, content={
            "error": "processing_error",
            "message": "Specification refinement failed",
            "details": str(e)[:500]
        })


@router.get("/{trace_id}/history")
async def spec_history(trace_id: str):
    """Get version history for a specification."""
    history = get_history(trace_id)
    if not history:
        return JSONResponse(status_code=404, content={
            "error": "not_found",
            "message": f"No specification found with trace_id: {trace_id}"
        })

    return {
        "trace_id": trace_id,
        "versions": history.get("versions", [])
    }
