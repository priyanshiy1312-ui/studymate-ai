import os
from pathlib import Path
from dotenv import load_dotenv

BASE = Path(__file__).resolve().parent
load_dotenv(BASE / ".env")

DATA_DIR = Path(os.getenv("DATA_DIR", BASE / "data"))
UPLOAD_DIR = DATA_DIR / "uploads"
CHROMA_DIR = DATA_DIR / "chroma"
DB_PATH = DATA_DIR / "studymate.db"
SAMPLE_DIR = Path(os.getenv("SAMPLE_DIR", BASE.parent / "sample_data"))
for d in (DATA_DIR, UPLOAD_DIR, CHROMA_DIR):
    d.mkdir(parents=True, exist_ok=True)

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto").lower()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
EMBEDDING_BACKEND = os.getenv("EMBEDDING_BACKEND", "auto").lower()
RERANKER = os.getenv("RERANKER", "none")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
VISION = os.getenv("VISION", "1") == "1"
MAX_VISION_PAGES = int(os.getenv("MAX_VISION_PAGES", "25"))
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.25"))
SR_UNIT = float(os.getenv("SR_UNIT_SECONDS", "86400"))
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")]
