from cryptography.fernet import Fernet
import os
import base64

# Generate once and store as env var: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY = os.getenv("TOKEN_ENCRYPTION_KEY", "").encode()

def get_fernet():
    if not ENCRYPTION_KEY:
        raise ValueError("TOKEN_ENCRYPTION_KEY not set in environment")
    return Fernet(ENCRYPTION_KEY)

def encrypt_token(token: str) -> str:
    """Encrypt before storing in database."""
    f = get_fernet()
    return f.encrypt(token.encode()).decode()

def decrypt_token(encrypted: str) -> str:
    """Decrypt when reading from database."""
    f = get_fernet()
    return f.decrypt(encrypted.encode()).decode()