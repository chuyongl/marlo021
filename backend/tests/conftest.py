import os
import sys
from pathlib import Path

os.environ.setdefault("BB_FAKE_LLM", "1")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
