#!/bin/bash
# Bunny - Setup Script
# Run this to set up the entire project on Arch Linux

set -e

echo "🐰 Bunny Setup Script"
echo "====================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# ─── Backend Setup ──────────────────────────────────────────────────
echo -e "\n${GREEN}[1/4] Setting up Backend...${NC}"

cd backend

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate and install
source venv/bin/activate
pip install --upgrade pip
pip install fastapi "uvicorn[standard]" python-multipart python-docx PyPDF2 \
    pydantic aiofiles httpx pytest pytest-asyncio aiosqlite python-dotenv

# Optional: Install AI model deps (requires ~2GB disk + GPU recommended)
echo -e "${YELLOW}Install AI model dependencies? (torch + transformers) [y/N]${NC}"
read -r install_ai
if [[ "$install_ai" =~ ^[Yy]$ ]]; then
    pip install torch transformers
    echo -e "${GREEN}AI dependencies installed. Set USE_MOCK_MODEL=false in .env${NC}"
else
    echo -e "${YELLOW}Skipping AI deps. Mock model will be used (USE_MOCK_MODEL=true)${NC}"
fi

# Optional: Solana SDK
echo -e "${YELLOW}Install Solana SDK? (anchorpy, solders, solana) [y/N]${NC}"
read -r install_solana
if [[ "$install_solana" =~ ^[Yy]$ ]]; then
    pip install anchorpy solders solana
fi

cd ..

# ─── Run Backend Tests ──────────────────────────────────────────────
echo -e "\n${GREEN}[2/4] Running Backend Tests...${NC}"
cd backend
source venv/bin/activate
python -m pytest tests/ -v --tb=short || echo -e "${RED}Some tests failed. Check output above.${NC}"
cd ..

# ─── Frontend Setup ────────────────────────────────────────────────
echo -e "\n${GREEN}[3/4] Setting up Frontend...${NC}"
cd frontend
npm install
cd ..

# ─── Solana Program ─────────────────────────────────────────────────
echo -e "\n${GREEN}[4/4] Solana Program...${NC}"
if command -v anchor &> /dev/null; then
    cd program
    anchor build || echo -e "${YELLOW}Anchor build failed. Make sure Solana CLI is configured.${NC}"
    cd ..
else
    echo -e "${YELLOW}Anchor not found. Install with: cargo install --git https://github.com/coral-xyz/anchor avm${NC}"
    echo -e "${YELLOW}Then: avm install latest && avm use latest${NC}"
fi

echo -e "\n${GREEN}✅ Setup complete!${NC}"
echo ""
echo "To start development:"
echo "  Backend:  cd backend && source venv/bin/activate && uvicorn main:app --reload"
echo "  Frontend: cd frontend && npm run dev"
echo "  Tests:    cd backend && source venv/bin/activate && pytest tests/ -v"
echo ""
echo "API docs:   http://localhost:8000/docs"
echo "Frontend:   http://localhost:3000"
