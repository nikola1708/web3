"""
Bunny Backend - Test Suite
Comprehensive tests for all backend functionality.
Run with: pytest tests/ -v
"""

import os
import sys
import uuid
import hashlib
import tempfile

# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from fastapi.testclient import TestClient

# Add backend dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force mock model for tests
os.environ["USE_MOCK_MODEL"] = "true"
os.environ["SOLANA_PRIVATE_KEY"] = ""

from main import app
from app import database as db
from app.services import file_parser, ai_engine, temporal_engine, humanity_score

client = TestClient(app)


# ─── Fixtures ────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def setup_db(tmp_path):
    """Use a temporary database for each test."""
    test_db = str(tmp_path / "test_bunny.db")
    db.DB_PATH = test_db
    db.init_db()
    yield
    if os.path.exists(test_db):
        os.remove(test_db)


@pytest.fixture
def sample_text():
    return (
        "It was a dark and stormy night. The wind howled through the ancient oaks, "
        "bending their gnarled branches like the arthritic fingers of old witches. "
        "Sarah pulled her coat tighter and pressed forward into the rain. "
        "She had been walking for hours, maybe days. Time had lost all meaning "
        "since the letter arrived. That terrible, beautiful letter that changed everything.\n\n"
        "The house appeared suddenly, as if the fog had simply decided to reveal it. "
        "A Victorian monstrosity perched on the cliff's edge, its windows glowing "
        "with a sickly amber light. Sarah stopped. Her heart hammered against her ribs. "
        "This was the place. This was where it all began, and where it would all end."
    )


@pytest.fixture
def ai_generated_text():
    return (
        "In the realm of artificial intelligence, machine learning algorithms have "
        "demonstrated remarkable capabilities in natural language processing tasks. "
        "These systems utilize deep neural networks to generate coherent and contextually "
        "appropriate text. The transformer architecture has revolutionized the field, "
        "enabling models to capture long-range dependencies in text sequences. "
        "Furthermore, attention mechanisms allow these models to focus on relevant "
        "portions of the input when generating each token of the output sequence. "
        "The implications of these advancements are far-reaching and profound."
    )


@pytest.fixture
def author_id():
    aid = str(uuid.uuid4())
    db.create_author(aid, "Test Author")
    return aid


@pytest.fixture
def document_id(author_id):
    did = str(uuid.uuid4())
    db.create_document(did, author_id, "Test Novel")
    return did


# ─── File Parser Tests ───────────────────────────────────────────────

class TestFileParser:
    def test_extract_text_from_txt(self):
        content = b"Hello, this is a test manuscript."
        result = file_parser.extract_text(content, "test.txt")
        assert result == "Hello, this is a test manuscript."

    def test_extract_text_from_markdown(self):
        content = b"# Chapter 1\n\nIt was a dark and stormy night."
        result = file_parser.extract_text(content, "novel.md")
        assert "Chapter 1" in result
        assert "dark and stormy" in result

    def test_unsupported_format(self):
        with pytest.raises(ValueError, match="Unsupported"):
            file_parser.extract_text(b"data", "file.xyz")

    def test_empty_content(self):
        with pytest.raises(ValueError, match="No text"):
            file_parser.extract_text(b"", "empty.txt")

    def test_compute_hash(self):
        text = "Hello World"
        h = file_parser.compute_hash(text)
        expected = hashlib.sha256(text.encode()).hexdigest()
        assert h == expected
        assert len(h) == 64

    def test_hash_deterministic(self):
        text = "Same content produces same hash"
        h1 = file_parser.compute_hash(text)
        h2 = file_parser.compute_hash(text)
        assert h1 == h2

    def test_hash_different_content(self):
        h1 = file_parser.compute_hash("Version 1")
        h2 = file_parser.compute_hash("Version 2")
        assert h1 != h2

    def test_text_stats(self, sample_text):
        stats = file_parser.get_text_stats(sample_text)
        assert stats["word_count"] > 0
        assert stats["char_count"] > 0
        assert stats["sentence_count"] > 0
        assert stats["paragraph_count"] >= 2
        assert stats["avg_word_length"] > 0


# ─── AI Engine Tests ─────────────────────────────────────────────────

class TestAIEngine:
    def test_analyze_text(self, sample_text):
        result = ai_engine.analyze_text(sample_text)
        assert "ai_score" in result
        assert 0 <= result["ai_score"] <= 100
        assert "linguistic_features" in result
        assert "model_used" in result

    def test_linguistic_features(self, sample_text):
        features = ai_engine._analyze_linguistic_features(sample_text)
        assert "vocabulary_richness" in features
        assert "burstiness" in features
        assert "hapax_ratio" in features
        assert "sentence_length_variance" in features
        assert features["word_count"] > 0

    def test_empty_text(self):
        features = ai_engine._analyze_linguistic_features("")
        assert "error" in features

    def test_heuristic_score_range(self, sample_text):
        features = ai_engine._analyze_linguistic_features(sample_text)
        score = ai_engine._heuristic_ai_score(features)
        assert 0 <= score <= 100

    def test_mock_mode(self, sample_text):
        result = ai_engine.analyze_text(sample_text)
        assert result["model_used"] in ("mock_heuristic", "heuristic_fallback")


# ─── Temporal Engine Tests ───────────────────────────────────────────

class TestTemporalEngine:
    def test_first_commit_baseline(self, document_id):
        result = temporal_engine.calculate_temporal_score(
            document_id, "abc123", 5000
        )
        assert result["temporal_score"] == 50.0
        assert result["total_commits"] == 0

    def test_second_commit(self, document_id, author_id):
        db.create_commit(
            str(uuid.uuid4()), document_id, author_id, 1,
            "hash1", 80.0, 20.0, 50.0, {}, "First draft",
            5000, 25000,
        )
        result = temporal_engine.calculate_temporal_score(
            document_id, "hash2", 5500
        )
        assert result["total_commits"] == 1
        assert result["temporal_score"] > 0

    def test_duplicate_hash(self, document_id, author_id):
        db.create_commit(
            str(uuid.uuid4()), document_id, author_id, 1,
            "samehash", 80.0, 20.0, 50.0, {}, "Draft",
            5000, 25000,
        )
        result = temporal_engine.calculate_temporal_score(
            document_id, "samehash", 5000
        )
        assert "Identical content" in result["analysis"]


# ─── Humanity Score Tests ────────────────────────────────────────────

class TestHumanityScore:
    def test_high_humanity(self):
        result = humanity_score.calculate_humanity_score(
            ai_score=10, temporal_score=90, ai_confidence=0.8
        )
        assert result["humanity_score"] > 70
        assert result["grade"] in ("A+", "A", "B")

    def test_low_humanity(self):
        result = humanity_score.calculate_humanity_score(
            ai_score=90, temporal_score=10, ai_confidence=0.8
        )
        assert result["humanity_score"] < 30
        assert result["grade"] in ("E", "F")

    def test_neutral(self):
        result = humanity_score.calculate_humanity_score(
            ai_score=50, temporal_score=50, ai_confidence=0.5
        )
        assert 40 <= result["humanity_score"] <= 60

    def test_score_bounds(self):
        r1 = humanity_score.calculate_humanity_score(0, 100, 1.0)
        assert r1["humanity_score"] <= 100
        r2 = humanity_score.calculate_humanity_score(100, 0, 1.0)
        assert r2["humanity_score"] >= 0


# ─── Database Tests ──────────────────────────────────────────────────

class TestDatabase:
    def test_create_author(self):
        author = db.create_author("test-1", "Alice")
        assert author["id"] == "test-1"
        assert author["display_name"] == "Alice"

    def test_create_document(self):
        db.create_author("a1", "Bob")
        doc = db.create_document("d1", "a1", "My Novel")
        assert doc["title"] == "My Novel"

    def test_create_commit(self):
        db.create_author("a2", "Carol")
        db.create_document("d2", "a2", "Story")
        commit = db.create_commit(
            "c1", "d2", "a2", 1, "hash123",
            85.5, 14.5, 90.0, {"test": True},
            "Initial commit", 1000, 5000,
        )
        assert commit["manuscript_hash"] == "hash123"
        assert commit["humanity_score"] == 85.5

    def test_get_commits_by_document(self):
        db.create_author("a3", "Dave")
        db.create_document("d3", "a3", "Novel")
        db.create_commit("c2", "d3", "a3", 1, "h1", 80, 20, 50, {}, "v1", 100, 500)
        db.create_commit("c3", "d3", "a3", 2, "h2", 85, 15, 60, {}, "v2", 200, 1000)
        commits = db.get_commits_by_document("d3")
        assert len(commits) == 2
        assert commits[0]["commit_number"] == 1

    def test_verify_by_hash(self):
        db.create_author("a4", "Eve")
        db.create_document("d4", "a4", "Book")
        db.create_commit(
            "c4", "d4", "a4", 1, "unique_hash",
            90, 10, 95, {}, "done", 5000, 25000
        )
        found = db.get_commit_by_hash("unique_hash")
        assert found is not None
        assert found["humanity_score"] == 90


# ─── API Endpoint Tests ─────────────────────────────────────────────

class TestAPI:
    def test_root(self):
        r = client.get("/")
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "Bunny"

    def test_health(self):
        r = client.get("/api/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"

    def test_upload_txt(self, sample_text):
        author = db.create_author(str(uuid.uuid4()), "TestWriter")
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(sample_text.encode())
            f.flush()
            fname = f.name
        try:
            with open(fname, "rb") as f:
                r = client.post(
                    "/api/upload",
                    files={"file": ("novel.txt", f, "text/plain")},
                    data={
                        "author_id": author["id"],
                        "title": "Test Novel",
                        "commit_message": "First draft",
                    },
                )
            assert r.status_code == 200
            data = r.json()
            assert "manuscript_hash" in data
            assert "ai_analysis" in data
            assert "humanity" in data
            assert data["humanity"]["grade"] in (
                "A+", "A", "B", "C", "D", "E", "F"
            )
            assert "commit" in data
        finally:
            os.remove(fname)

    def test_upload_md(self, sample_text):
        author = db.create_author(str(uuid.uuid4()), "MDWriter")
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            f.write(f"# Chapter 1\n\n{sample_text}".encode())
            f.flush()
            fname = f.name
        try:
            with open(fname, "rb") as f:
                r = client.post(
                    "/api/upload",
                    files={"file": ("novel.md", f, "text/markdown")},
                    data={"author_id": author["id"]},
                )
            assert r.status_code == 200
        finally:
            os.remove(fname)

    def test_upload_unsupported(self):
        r = client.post(
            "/api/upload",
            files={
                "file": ("data.xyz", b"content", "application/octet-stream")
            },
            data={"author_id": "test"},
        )
        assert r.status_code == 400

    def test_analyze_text(self, sample_text):
        r = client.post(
            "/api/analyze-text",
            data={"text": sample_text},
        )
        assert r.status_code == 200
        data = r.json()
        assert "manuscript_hash" in data
        assert "ai_analysis" in data
        assert "humanity" in data

    def test_verify_unknown_hash(self):
        fake = "0" * 64
        r = client.get(f"/api/verify/{fake}")
        assert r.status_code == 200
        data = r.json()
        assert data["found"] is False

    def test_verify_known_hash(self, sample_text):
        author = db.create_author(str(uuid.uuid4()), "Verifier")
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(sample_text.encode())
            f.flush()
            fname = f.name
        try:
            with open(fname, "rb") as f:
                upload_r = client.post(
                    "/api/upload",
                    files={"file": ("novel.txt", f, "text/plain")},
                    data={"author_id": author["id"]},
                )
            h = upload_r.json()["manuscript_hash"]
            r = client.get(f"/api/verify/{h}")
            assert r.status_code == 200
            assert r.json()["found"] is True
        finally:
            os.remove(fname)

    def test_create_author_endpoint(self):
        r = client.post("/api/authors?display_name=NewAuthor")
        assert r.status_code == 200
        assert r.json()["display_name"] == "NewAuthor"

    def test_full_pipeline(self, sample_text):
        """End-to-end: upload -> analyze -> commit -> verify."""
        author = db.create_author(str(uuid.uuid4()), "Pipeline Author")

        # Upload first version
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(sample_text.encode())
            f.flush()
            fname = f.name
        try:
            with open(fname, "rb") as f:
                r1 = client.post(
                    "/api/upload",
                    files={"file": ("novel.txt", f, "text/plain")},
                    data={
                        "author_id": author["id"],
                        "title": "Pipeline Novel",
                        "commit_message": "Initial draft",
                    },
                )
            assert r1.status_code == 200
            d1 = r1.json()
            doc_id = d1["document_id"]
            hash1 = d1["manuscript_hash"]
        finally:
            os.remove(fname)

        # Upload second version (evolved)
        evolved = sample_text + "\n\nChapter 2: The door creaked open."
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(evolved.encode())
            f.flush()
            fname = f.name
        try:
            with open(fname, "rb") as f:
                r2 = client.post(
                    "/api/upload",
                    files={"file": ("novel.txt", f, "text/plain")},
                    data={
                        "author_id": author["id"],
                        "document_id": doc_id,
                        "commit_message": "Added Chapter 2",
                    },
                )
            assert r2.status_code == 200
            hash2 = r2.json()["manuscript_hash"]
            assert hash1 != hash2
        finally:
            os.remove(fname)

        # Verify first hash
        v = client.get(f"/api/verify/{hash1}")
        assert v.status_code == 200
        assert v.json()["found"] is True

        # Check document has 2 commits
        doc = client.get(f"/api/documents/{doc_id}")
        assert doc.status_code == 200
        assert len(doc.json()["commits"]) == 2
