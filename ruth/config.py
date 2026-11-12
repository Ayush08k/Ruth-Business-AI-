"""
Ruth Configuration Manager — Local-Only Version
No external AI APIs. Everything runs on your PC.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

class Config:
    # ── Local AI (Ollama) ──────────────────────────────────────────────────
    # NO Gemini, NO OpenAI — 100% local
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    # Model options for 4GB RAM:
    #   phi3:mini    (~2.3GB) ← best quality for the size
    #   gemma2:2b    (~1.6GB) ← Google's tiny model
    #   llama3.2:1b  (~1.3GB) ← fastest, least RAM
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "phi3:mini")

    # ── Gmail (for email reading + sending reports) ────────────────────────
    GMAIL_CREDENTIALS_FILE: str = os.getenv("GMAIL_CREDENTIALS_FILE", "credentials.json")
    GMAIL_TOKEN_FILE: str = os.getenv("GMAIL_TOKEN_FILE", "ruth_data/token.json")
    REPORT_EMAIL: str = os.getenv("REPORT_EMAIL", "")

    # ── Website Monitoring ─────────────────────────────────────────────────
    WEBSITE_URL: str = os.getenv("WEBSITE_URL", "")
    WEBSITE_CHECK_INTERVAL: int = int(os.getenv("WEBSITE_CHECK_INTERVAL", "300"))

    # ── Voice Settings ─────────────────────────────────────────────────────
    VOICE_LANGUAGE_DEFAULT: str = os.getenv("VOICE_LANGUAGE_DEFAULT", "en")
    WAKE_WORD: str = os.getenv("WAKE_WORD", "hey ruth")
    VOICE_EN: str = os.getenv("VOICE_EN", "en-US-JennyNeural")
    VOICE_HI: str = os.getenv("VOICE_HI", "hi-IN-SwaraNeural")

    # ── Picovoice (Wake Word) ──────────────────────────────────────────────
    PICOVOICE_ACCESS_KEY: str = os.getenv("PICOVOICE_ACCESS_KEY", "")

    # ── Paths (all local) ──────────────────────────────────────────────────
    RUTH_DATA_DIR: Path = Path(os.getenv("RUTH_DATA_DIR", "ruth_data"))
    MEMORY_DIR: Path = Path(os.getenv("MEMORY_DIR", "ruth_data/memory"))
    DB_PATH: Path = Path(os.getenv("DB_PATH", "ruth_data/ruth.db"))
    LOG_DIR: Path = Path(os.getenv("LOG_DIR", "logs"))

    # ── Report Schedule ────────────────────────────────────────────────────
    MORNING_BRIEFING_TIME: str = os.getenv("MORNING_BRIEFING_TIME", "07:00")
    EMAIL_CHECK_INTERVAL_HOURS: int = int(os.getenv("EMAIL_CHECK_INTERVAL_HOURS", "2"))

    @classmethod
    def ensure_dirs(cls):
        for d in [cls.RUTH_DATA_DIR, cls.MEMORY_DIR, cls.LOG_DIR]:
            Path(d).mkdir(parents=True, exist_ok=True)

    @classmethod
    def validate(cls) -> list[str]:
        """Check what's missing — Ollama must be running, that's all"""
        missing = []
        import requests
        try:
            requests.get(cls.OLLAMA_URL + "/api/tags", timeout=2)
        except Exception:
            missing.append("OLLAMA_NOT_RUNNING")
        return missing

config = Config()
config.ensure_dirs()
