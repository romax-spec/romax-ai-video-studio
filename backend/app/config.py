import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
DATA_DIR = Path(os.getenv("DATA_DIR", "./data")).resolve()
UPLOAD_DIR = DATA_DIR / "uploads"
OUTPUT_DIR = DATA_DIR / "outputs"
for p in (DATA_DIR, UPLOAD_DIR, OUTPUT_DIR): p.mkdir(parents=True, exist_ok=True)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./romax.db")
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "2048"))
ENABLE_WHISPER = os.getenv("ENABLE_WHISPER", "false").lower() == "true"
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
