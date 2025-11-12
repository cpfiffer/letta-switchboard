import hashlib
import json
from cryptography.fernet import Fernet
import logging
import os

logger = logging.getLogger(__name__)


def get_api_key_hash(api_key: str) -> str:
    """Generate a hash of the API key for directory naming."""
    return hashlib.sha256(api_key.encode()).hexdigest()[:16]


def is_dev_mode() -> bool:
    """Check if we're in dev mode (no encryption)."""
    return os.getenv("LETTA_SWITCHBOARD_DEV_MODE", "").lower() in ("true", "1", "yes")


def get_encryption_key() -> bytes:
    """Get or generate encryption key for JSON encryption."""
    key = os.getenv("LETTA_SWITCHBOARD_ENCRYPTION_KEY")
    
    if is_dev_mode():
        logger.warning("🔓 DEV MODE: Encryption disabled - files stored in plaintext")
        return b"dev-mode-no-encryption"
    
    if not key:
        logger.warning("LETTA_SWITCHBOARD_ENCRYPTION_KEY not set, generating temporary key")
        key = Fernet.generate_key().decode()
    
    return key.encode()


def encrypt_json(data: dict, encryption_key: bytes) -> bytes:
    """Encrypt a JSON object (or return plaintext in dev mode)."""
    json_bytes = json.dumps(data, default=str, indent=2).encode()
    
    if is_dev_mode():
        return json_bytes
    
    fernet = Fernet(encryption_key)
    return fernet.encrypt(json_bytes)


def decrypt_json(encrypted_data: bytes, encryption_key: bytes) -> dict:
    """Decrypt an encrypted JSON object (or parse plaintext in dev mode)."""
    if is_dev_mode():
        return json.loads(encrypted_data)
    
    fernet = Fernet(encryption_key)
    json_bytes = fernet.decrypt(encrypted_data)
    return json.loads(json_bytes)
