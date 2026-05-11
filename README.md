# Bunny — Decentralized Manuscript Attestation

Proves human authorship by combining AI linguistic analysis with Proof of Process, anchored to Solana.

---

## Prerequisites

- Python 3.10+
- Node.js 18+
- (Optional) Rust + Solana CLI + Anchor — only needed if you want to rebuild/redeploy the on-chain program

---

## Setup

```bash
chmod +x setup.sh
./setup.sh
```

The script will:
1. Create a Python venv and install backend dependencies
2. Optionally install AI model deps (`torch` + `transformers`, ~2 GB, GPU recommended) — skip to use the built-in heuristic mock
3. Optionally install Solana SDK (`anchorpy`, `solders`, `solana`)
4. Run backend tests
5. Install frontend dependencies (`npm install`)

---

## Environment Variables

Create `backend/.env` (copy from `backend/.env.example`):

| Variable | Default | Notes |
|---|---|---|
| `USE_MOCK_MODEL` | `true` | Set to `false` only if you installed `torch` + `transformers` |
| `SOLANA_RPC_URL` | devnet | Leave as-is for local testing |
| `SOLANA_PRIVATE_KEY` | _(empty)_ | Relayer wallet (base58) — optional for local testing |
| `PROGRAM_ID` | _(placeholder)_ | Only needed if you deploy your own Anchor program |

> Without a `SOLANA_PRIVATE_KEY`, on-chain attestation is skipped but all analysis and scoring still works.

---

## Running Locally

Open two terminals:

**Terminal 1 — Backend** (port 8000)
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

**Terminal 2 — Frontend** (port 3000)
```bash
cd frontend
npm run dev
```

Then open **http://localhost:3000**

API docs (Swagger): **http://localhost:8000/docs**

---

## Tests

```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```
