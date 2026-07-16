"""Password hashing and verification helpers for authentication."""

from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(password: str) -> str:
    """Hash a plaintext password using a secure one-way algorithm."""
    return generate_password_hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against its stored hash."""
    return check_password_hash(password_hash, password)
