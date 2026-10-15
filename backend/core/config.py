"""
Settings read from the environment, with defaults that work on Railway as-is.

Brown Bag is the public name. "Marlo" never appears in anything a reader or
vendor sees.
"""

import hashlib
import os

FRONTEND_URL = os.getenv("FRONTEND_URL", "https://marlo021.ai").rstrip("/")
API_URL = os.getenv("APP_BASE_URL", "https://api.marlo021.ai").rstrip("/")
PUBLICATION_NAME = os.getenv("PUBLICATION_NAME", "Brown Bag")

FROM_EMAIL = os.getenv("BB_FROM_EMAIL") or os.getenv("FROM_EMAIL") or "hello@marlo021.ai"
FROM_NAME = os.getenv("BB_FROM_NAME", PUBLICATION_NAME)

# One secret signs editor sessions and click links. Uses an explicit secret
# when Railway has one; otherwise derives a stable one from the database URL
# so the app works without new configuration.
_raw_secret = (
    os.getenv("BB_SECRET")
    or os.getenv("VENDOR_TOKEN_SECRET")
    or os.getenv("JWT_SECRET_KEY")
    or os.getenv("SECRET_KEY")
    or ("derived:" + os.getenv("DATABASE_URL", "local-dev"))
)
SECRET = hashlib.sha256(_raw_secret.encode()).digest()

# First-editor setup. Only the hash lives in code; the code itself was given
# to Anna directly. Works only while no editor account exists.
SETUP_CODE_SHA256 = os.getenv(
    "BB_SETUP_CODE_SHA256",
    "351570ee1b0a54a4580e1b0ba45727fe8764ceeea16a5f263c1bb0c73c6372d6",
)

FAKE_LLM = os.getenv("BB_FAKE_LLM") == "1"   # local tests only

CORS_ORIGINS = sorted({
    FRONTEND_URL,
    "https://marlo021.ai",
    "https://www.marlo021.ai",
    "http://localhost:3000",
})
