# 🐰 Bunny — Digital Heartbeat for Writers

A decentralized attestation layer for novelists. Bunny proves human authorship 
by combining linguistic AI analysis with Proof of Process (timestamped edit history), 
anchored to the Solana blockchain.

## Architecture

```
Writer uploads .docx/.md/.pdf
        │
        ▼
┌─────────────────────────────┐
│     FastAPI Backend          │
│  ┌─────────────────────┐   │
│  │ 1. File Parser       │   │  → Extract text, compute SHA-256 hash
│  │ 2. AI Engine         │   │  → DeBERTa-v3 linguistic analysis
│  │ 3. Temporal Engine   │   │  → Compare against edit history
│  │ 4. Humanity Score    │   │  → Weighted final score (A+ to F)
│  │ 5. Solana Relayer    │   │  → Submit attestation on-chain
│  └─────────────────────┘   │
│          │                   │
│     SQLite DB               │
└──────────┬──────────────────┘
           │
           ▼
┌──────────────────────────────┐
│  Solana Devnet (Anchor)      │
│  • Attestation PDAs          │
│  • Author Profile PDAs       │
│  • Immutable audit trail     │
└──────────────────────────────┘
```

## Quick Start

### Prerequisites (Arch Linux)
```bash
# Python 3.10+
sudo pacman -S python python-pip

# Node.js 18+
sudo pacman -S nodejs npm

# Rust + Solana (for on-chain program)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
sh -c "$(curl -sSfL https://release.anza.xyz/stable/install)"
cargo install --git https://github.com/coral-xyz/anchor avm --force
avm install latest && avm use latest
```

### Installation

```bash
# Clone and setup
chmod +x setup.sh
./setup.sh
```

### Manual Setup

**Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install fastapi "uvicorn[standard]" python-multipart python-docx PyPDF2 \
    pydantic aiofiles httpx pytest pytest-asyncio aiosqlite python-dotenv
uvicorn main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Run Tests:**
```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload` | Upload manuscript for full analysis + commit |
| POST | `/api/analyze-text` | Analyze raw text without file upload |
| GET | `/api/verify/{hash}` | Verify a manuscript by SHA-256 hash |
| GET | `/api/documents/{id}` | Get document with commit history |
| GET | `/api/authors/{id}/commits` | Get all commits by an author |
| GET | `/api/health` | Health check |
| GET | `/docs` | Interactive API documentation |

## How It Works

### 1. Ingestion Layer
Upload `.docx`, `.md`, `.pdf`, or `.txt` → text extracted → SHA-256 hash generated.
**Your manuscript never touches the blockchain.** Only the cryptographic fingerprint is stored.

### 2. Verification Engine (Dual-Layer)

**Linguistic Check (AI Engine)**
- DeBERTa-v3-base model analyzes text patterns
- Measures: vocabulary richness, burstiness, sentence variance, hapax ratio, contraction usage
- Score 0-100 (higher = more likely AI)

**Temporal Check (Proof of Process)**
- Compares current hash to previous commits
- Rewards natural time-deltas between edits
- AI generates 50k words in seconds; humans over months
- Score 0-100 (higher = more natural evolution)

### 3. Humanity Score
Weighted combination of AI + Temporal scores → Grade A+ to F

### 4. Solana Anchor
Hash + score submitted to Solana Devnet → Immutable audit trail.
Writers never need a wallet (Relayer Architecture).

## Testing

The backend includes comprehensive tests:
```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

Tests cover:
- ✅ File parsing (txt, md, docx, pdf)
- ✅ SHA-256 hashing (deterministic, unique)
- ✅ AI detection engine (features, scoring)
- ✅ Temporal analysis (first commit, evolution, duplicates)
- ✅ Humanity score (bounds, grades)
- ✅ Database operations (CRUD)
- ✅ API endpoints (upload, verify, history)
- ✅ Full pipeline (upload → analyze → commit → verify)

## Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_MOCK_MODEL` | `true` | Use heuristic model (no GPU needed) |
| `SOLANA_RPC_URL` | devnet | Solana RPC endpoint |
| `SOLANA_PRIVATE_KEY` | empty | Relayer wallet (base58) |
| `PROGRAM_ID` | placeholder | Deployed Anchor program ID |

## Project Structure

```
web3/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── app/
│   │   ├── config.py        # Environment configuration
│   │   ├── database.py      # SQLite data layer
│   │   ├── models.py        # Pydantic schemas
│   │   ├── routes/
│   │   │   ├── upload.py    # Upload & analysis endpoints
│   │   │   └── documents.py # Document & verify endpoints
│   │   └── services/
│   │       ├── file_parser.py     # Text extraction + hashing
│   │       ├── ai_engine.py       # DeBERTa AI detection
│   │       ├── temporal_engine.py # Proof of Process
│   │       ├── humanity_score.py  # Final score calculator
│   │       └── solana_relayer.py  # On-chain attestation
│   └── tests/
│       └── test_backend.py  # Comprehensive test suite
├── frontend/                # Next.js UI
│   └── src/app/
│       ├── page.tsx         # Main page (upload/verify/history)
│       ├── layout.tsx       # Root layout
│       └── globals.css      # Styles
├── program/                 # Solana Anchor program
│   └── programs/bunny_attestation/
│       └── src/lib.rs       # Smart contract
├── setup.sh                 # One-command setup
└── README.md
```

## License

MIT
