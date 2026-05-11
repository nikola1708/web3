"""
Bunny - Document & Verification Routes
GET /api/health                       — health check
POST /api/authors                     — create author
GET  /api/authors/{id}               — get author
GET  /api/authors/{id}/documents     — list documents
GET  /api/authors/{id}/commits       — list all commits
GET  /api/documents/{id}             — document + commit history
GET  /api/documents/{id}/commits     — commits only
GET  /api/verify/{hash}              — verify by SHA-256 hash
"""

import uuid
from fastapi import APIRouter, HTTPException
from app import database as db
from app.services import solana_relayer, file_parser

router = APIRouter(prefix="/api", tags=["documents"])


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "bunny-backend", "version": "0.1.0"}


@router.post("/authors")
async def create_author(display_name: str):
    author_id = str(uuid.uuid4())
    return db.create_author(author_id, display_name)


@router.get("/authors/{author_id}")
async def get_author(author_id: str):
    author = db.get_author(author_id)
    if not author:
        raise HTTPException(404, "Author not found")
    return author


@router.get("/authors/{author_id}/documents")
async def get_author_documents(author_id: str):
    return db.get_documents_by_author(author_id)


@router.get("/authors/{author_id}/commits")
async def get_author_commits(author_id: str):
    return db.get_all_commits_by_author(author_id)


@router.get("/documents/{document_id}")
async def get_document(document_id: str):
    doc = db.get_document(document_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    return {**doc, "commits": db.get_commits_by_document(document_id)}


@router.get("/documents/{document_id}/commits")
async def get_document_commits(document_id: str):
    return db.get_commits_by_document(document_id)


@router.get("/verify/{manuscript_hash}")
async def verify_hash(manuscript_hash: str):
    commit = db.get_commit_by_hash(manuscript_hash)
    if not commit:
        return {"found": False, "manuscript_hash": manuscript_hash, "message": "No attestation found."}

    on_chain = None
    if commit.get("tx_signature"):
        on_chain = await solana_relayer.verify_attestation_onchain(
            manuscript_hash, "", commit["commit_number"]
        )

    return {"found": True, "manuscript_hash": manuscript_hash, "commit": commit, "on_chain": on_chain}
