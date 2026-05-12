"""
Bunny Backend - Main Application
A decentralized attestation layer for novelists.

Run with: uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.routes import upload, documents

# Initialize the database on startup
init_db()

app = FastAPI(
    title="Bunny - Digital Heartbeat for Writers",
    description=(
        "Decentralized attestation layer for novelists. "
        "Proves human authorship via AI analysis + temporal evolution, "
        "anchored to the Solana blockchain."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(upload.router)
app.include_router(documents.router)


@app.get("/")
async def root():
    return {
        "name": "Bunny",
        "tagline": "The Digital Heartbeat for Writers",
        "version": "0.1.0",
        "docs": "/docs",
        "endpoints": {
            "upload": "POST /api/upload",
            "analyze_text": "POST /api/analyze-text",
            "verify": "GET /api/verify/{hash}",
            "documents": "GET /api/documents/{id}",
            "health": "GET /api/health",
        },
    }

