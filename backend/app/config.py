"""Bunny Backend Configuration."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")


class Settings:
    SOLANA_RPC_URL: str = os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com")
    SOLANA_PRIVATE_KEY: str = os.getenv("SOLANA_PRIVATE_KEY", "")
    PROGRAM_ID: str = os.getenv("PROGRAM_ID", "BuNNy1111111111111111111111111111111111111")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "microsoft/deberta-v3-base")
    USE_MOCK_MODEL: bool = os.getenv("USE_MOCK_MODEL", "true").lower() == "true"
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", str(Path(__file__).parent.parent / "bunny.db"))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    ALLOWED_EXTENSIONS: set = {".docx", ".doc", ".md", ".pdf", ".txt"}


settings = Settings()
