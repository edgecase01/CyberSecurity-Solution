import hashlib


def hash_attachment(content: bytes) -> str:
    """Return the SHA-256 hex digest of attachment bytes."""
    return hashlib.sha256(content).hexdigest()
