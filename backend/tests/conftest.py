import os
import sys
from pathlib import Path

os.environ.setdefault("BB_FAKE_LLM", "1")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/test")   # engine is lazy; nothing connects in unit tests
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
