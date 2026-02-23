"""Configuration management for AstraDB Quality Check Tool."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for managing application settings."""

    def __init__(self):
        """Initialize configuration from environment variables."""
        # AstraDB Configuration
        self.astra_db_endpoint = os.getenv("ASTRA_DB_ENDPOINT")
        self.astra_db_token = os.getenv("ASTRA_DB_TOKEN")
        self.astra_db_keyspace = os.getenv("ASTRA_DB_KEYSPACE", "default_keyspace")
        self.astra_db_collection = os.getenv("ASTRA_DB_COLLECTION", "qa_collection")

        # Search Configuration
        self.similarity_threshold = float(os.getenv("SIMILARITY_THRESHOLD", "0.85"))
        self.max_search_results = int(os.getenv("MAX_SEARCH_RESULTS", "20"))

        # Audit Configuration
        self.audit_log_path = Path(os.getenv("AUDIT_LOG_PATH", "./audit_logs"))
        self.enable_audit_log = os.getenv("ENABLE_AUDIT_LOG", "true").lower() == "true"

        # Quality Check Configuration
        self.min_question_length = int(os.getenv("MIN_QUESTION_LENGTH", "10"))
        self.min_answer_length = int(os.getenv("MIN_ANSWER_LENGTH", "20"))
        self.quality_score_threshold = int(os.getenv("QUALITY_SCORE_THRESHOLD", "70"))

        # Validate required configuration
        self._validate()

    def _validate(self):
        """Validate that required configuration is present."""
        if not self.astra_db_endpoint:
            raise ValueError(
                "ASTRA_DB_ENDPOINT is required. Please set it in your .env file."
            )
        if not self.astra_db_token:
            raise ValueError(
                "ASTRA_DB_TOKEN is required. Please set it in your .env file."
            )

    def ensure_audit_log_dir(self):
        """Ensure audit log directory exists."""
        if self.enable_audit_log:
            self.audit_log_path.mkdir(parents=True, exist_ok=True)

    @property
    def is_configured(self) -> bool:
        """Check if the configuration is valid."""
        return bool(self.astra_db_endpoint and self.astra_db_token)

    def __repr__(self) -> str:
        """Return string representation of config (without sensitive data)."""
        return (
            f"Config("
            f"endpoint={'***' if self.astra_db_endpoint else None}, "
            f"keyspace={self.astra_db_keyspace}, "
            f"collection={self.astra_db_collection}, "
            f"similarity_threshold={self.similarity_threshold})"
        )


# Global configuration instance
config = Config()
