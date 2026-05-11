"""
Bunny - Upload & Analysis Routes
POST /api/upload       — full pipeline: extract → hash → AI → temporal → score → commit
POST /api/analyze-text — same but raw text, no file
"""

import uuid
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services import file_parser, ai_engine, temporal_engine, humanity_score
from app.services import solana_relayer
from app import database as db
from app.config import settings

router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/upload")
async def upload_and_analyze(
    file: UploadFile = File(...),
    author_id: str = Form(...),
    document_id: str = Form(default=""),
    title: str = Form(default=""),
    commit_message: str = Form(default=""),
    auto_commit: bool = Form(default=True),
):
    # Validate extension
    ext = "." + (file.filename or "x.txt").rsplit(".", 1)[-1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported format: {ext}. Allowed: {settings.ALLOWED_EXTENSIONS}")

    file_bytes = await file.read()
    if len(file_bytes) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(400, f"File too large. Max {settings.MAX_FILE_SIZE_MB}MB")

    # Extract text
    try:
        text = file_parser.extract_text(file_bytes, file.filename or "upload.txt")
    except ValueError as e:
        raise HTTPException(400, str(e))

    manuscript_hash = file_parser.compute_hash(text)
    text_stats = file_parser.get_text_stats(text)

    # Ensure author exists
    if not db.get_author(author_id):
        db.create_author(author_id, f"Author-{author_id[:8]}")

    # Ensure document exists
    if not document_id:
        document_id = str(uuid.uuid4())
        db.create_document(document_id, author_id, title or (file.filename or "Untitled").rsplit(".", 1)[0])
    elif not db.get_document(document_id):
        db.create_document(document_id, author_id, title or "Untitled")

    # Run analysis pipeline
    ai_result = ai_engine.analyze_text(text)
    temporal_result = temporal_engine.calculate_temporal_score(
        document_id, manuscript_hash, text_stats["word_count"]
    )
    h_result = humanity_score.calculate_humanity_score(
        ai_score=ai_result["ai_score"],
        temporal_score=temporal_result["temporal_score"],
        ai_confidence=ai_result["confidence"],
    )

    response = {
        "manuscript_hash": manuscript_hash,
        "document_id": document_id,
        "text_stats": text_stats,
        "ai_analysis": ai_result,
        "temporal_analysis": temporal_result,
        "humanity": h_result,
    }

    if auto_commit:
        commit_num = db.get_commit_count(document_id) + 1
        commit_id = str(uuid.uuid4())
        db.create_commit(
            commit_id, document_id, author_id, commit_num, manuscript_hash,
            h_result["humanity_score"], ai_result["ai_score"], temporal_result["temporal_score"],
            ai_result["linguistic_features"], commit_message or f"Commit #{commit_num}",
            text_stats["word_count"], text_stats["char_count"],
        )
        db.increment_author_commits(author_id)
        db.update_document_timestamp(document_id)

        chain = await solana_relayer.submit_attestation_onchain(
            manuscript_hash, int(h_result["humanity_score"]), int(ai_result["ai_score"]),
            int(temporal_result["temporal_score"]), title or "Untitled", commit_message, author_id,
        )
        if chain.get("tx_signature"):
            db.update_commit_tx(commit_id, chain["tx_signature"])

        response["commit"] = {
            "commit_id": commit_id,
            "commit_number": commit_num,
            "on_chain_status": chain.get("status", "pending"),
            "tx_signature": chain.get("tx_signature"),
            "chain_details": chain,
        }

    return response


@router.post("/analyze-text")
async def analyze_text_directly(
    text: str = Form(...),
    author_id: str = Form(default="anonymous"),
    document_id: str = Form(default=""),
):
    if not text.strip():
        raise HTTPException(400, "Text cannot be empty")

    manuscript_hash = file_parser.compute_hash(text)
    text_stats = file_parser.get_text_stats(text)
    ai_result = ai_engine.analyze_text(text)

    temporal_result: dict = {"temporal_score": 50.0, "analysis": "No document history for raw text."}
    if document_id:
        temporal_result = temporal_engine.calculate_temporal_score(
            document_id, manuscript_hash, text_stats["word_count"]
        )

    h_result = humanity_score.calculate_humanity_score(
        ai_score=ai_result["ai_score"],
        temporal_score=temporal_result["temporal_score"],
        ai_confidence=ai_result["confidence"],
    )

    return {
        "manuscript_hash": manuscript_hash,
        "text_stats": text_stats,
        "ai_analysis": ai_result,
        "temporal_analysis": temporal_result,
        "humanity": h_result,
    }
