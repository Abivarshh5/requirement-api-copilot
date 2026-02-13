"""
FastAPI application entry point.
Configures CORS, logging, routes, and health check.
"""

import os
import logging
from datetime import datetime, timezone

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import router as specs_router

# ── Logging ───────────────────────────────────────────────────────────

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# ── App Setup ─────────────────────────────────────────────────────────

app = FastAPI(
    title="Requirement → API Copilot",
    description="Transform product requirements into structured technical specifications",
    version="1.0.0"
)

# CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(specs_router)

# ── Health Check ──────────────────────────────────────────────────────

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./outputs")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "llm_provider": "google-gemini",
        "llm_model": os.getenv("LLM_MODEL", "gemini-1.5-flash"),
        "mock_mode": os.getenv("MOCK_MODE", "false").lower() == "true",
        "output_dir_writable": os.access(OUTPUT_DIR, os.W_OK) if os.path.exists(OUTPUT_DIR) else True,
    }


@app.get("/")
async def root():
    return {
        "name": "Requirement → API Copilot",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
