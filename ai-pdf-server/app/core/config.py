"""Application configuration settings."""

import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv

load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
INDEX_DIR = DATA_DIR / "indices"
METADATA_DIR = DATA_DIR / "metadata"

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
INDEX_DIR.mkdir(parents=True, exist_ok=True)
METADATA_DIR.mkdir(parents=True, exist_ok=True)


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self):
        # Server settings
        self.PORT: int = int(os.getenv("PORT", "8000"))
        self.HOST: str = os.getenv("HOST", "0.0.0.0")
        self.DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
        self.CORS_ORIGINS: List[str] = self._parse_cors_origins()

        # OpenAI settings
        self.OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
        self.EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        self.LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o")
        self.EMBEDDING_DIMENSIONS: int = 1536

        # RAG settings
        self.CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "500"))
        self.CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "50"))
        self.TOP_K_RESULTS: int = int(os.getenv("TOP_K_RESULTS", "5"))
        self.CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.7"))

        # Voice call session settings
        self.VOICE_SESSION_TIMEOUT_MINUTES: int = int(os.getenv("VOICE_SESSION_TIMEOUT_MINUTES", "5"))
        self.VOICE_SESSION_MAX_DURATION_MINUTES: int = int(os.getenv("VOICE_SESSION_MAX_DURATION_MINUTES", "60"))
        self.VOICE_MAX_CONCURRENT_CALLS_PER_USER: int = int(os.getenv("VOICE_MAX_CONCURRENT_CALLS_PER_USER", "1"))
        self.VOICE_MAX_AUDIO_BYTES_PER_SECOND: int = int(os.getenv("VOICE_MAX_AUDIO_BYTES_PER_SECOND", "48000"))

        # Voice RAG enforcement settings
        self.RAG_HARD_REJECT_ENABLED: bool = os.getenv("RAG_HARD_REJECT_ENABLED", "true").lower() == "true"
        self.RAG_MIN_CONFIDENCE_FOR_VOICE: float = float(os.getenv("RAG_MIN_CONFIDENCE_FOR_VOICE", "0.3"))
        self.RAG_REFUSAL_MESSAGE: str = os.getenv(
            "RAG_REFUSAL_MESSAGE",
            "I cannot find information about that in the uploaded document. Please ask something related to the document content."
        )

        # Exhaustive extraction settings
        self.ENABLE_EXHAUSTIVE_EXTRACTION: bool = os.getenv("ENABLE_EXHAUSTIVE_EXTRACTION", "true").lower() == "true"
        self.MAX_EXTRACTION_TOKENS: int = int(os.getenv("MAX_EXTRACTION_TOKENS", "8000"))
        self.EXTRACTION_MAX_CHUNKS: int = int(os.getenv("EXTRACTION_MAX_CHUNKS", "200"))
        self.EXTRACTION_BATCH_SIZE: int = int(os.getenv("EXTRACTION_BATCH_SIZE", "10"))

        # Highlight synchronization settings
        self.ENABLE_HIGHLIGHT_SYNC: bool = os.getenv("ENABLE_HIGHLIGHT_SYNC", "true").lower() == "true"
        self.HIGHLIGHT_MERGE_THRESHOLD: float = float(os.getenv("HIGHLIGHT_MERGE_THRESHOLD", "0.9"))

        # Blockchain integration settings
        self.ENABLE_BLOCKCHAIN: bool = os.getenv("ENABLE_BLOCKCHAIN", "false").lower() == "true"
        self.BLOCKCHAIN_RPC_URL: str = os.getenv("BLOCKCHAIN_RPC_URL", "")
        self.BLOCKCHAIN_CONTRACT_ADDRESS: str = os.getenv("BLOCKCHAIN_CONTRACT_ADDRESS", "")
        self.BLOCKCHAIN_PRIVATE_KEY: str = os.getenv("BLOCKCHAIN_PRIVATE_KEY", "")
        self.BLOCKCHAIN_CHAIN_ID: int = int(os.getenv("BLOCKCHAIN_CHAIN_ID", "137"))  # Polygon mainnet
        self.BLOCKCHAIN_GAS_LIMIT: int = int(os.getenv("BLOCKCHAIN_GAS_LIMIT", "100000"))
        self.ENABLE_MERKLE_BATCHING: bool = os.getenv("ENABLE_MERKLE_BATCHING", "true").lower() == "true"
        self.MERKLE_BATCH_SIZE: int = int(os.getenv("MERKLE_BATCH_SIZE", "10"))

        # Storage paths
        self.UPLOAD_DIR: Path = UPLOAD_DIR
        self.INDEX_DIR: Path = INDEX_DIR
        self.METADATA_DIR: Path = METADATA_DIR

        # Logging
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")

    def _parse_cors_origins(self) -> List[str]:
        """Parse CORS origins from environment variable."""
        origins = os.getenv("CORS_ORIGINS", "*")
        if origins == "*":
            return ["*"]
        return [origin.strip() for origin in origins.split(",") if origin.strip()]


settings = Settings()

