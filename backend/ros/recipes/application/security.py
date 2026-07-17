"""Security abstractions for secret formulation encryption workflows."""

from __future__ import annotations

from typing import Protocol


class EncryptionProvider(Protocol):
    """Abstraction for encryption providers (KMS/HSM/Vault integrations)."""

    def encrypt(self, plaintext: str, *, context: dict[str, str] | None = None) -> str:
        """Encrypt plaintext and return ciphertext."""


class DecryptionProvider(Protocol):
    """Abstraction for decryption providers (KMS/HSM/Vault integrations)."""

    def decrypt(self, ciphertext: str, *, context: dict[str, str] | None = None) -> str:
        """Decrypt ciphertext and return plaintext."""


class KeyProvider(Protocol):
    """Abstraction for selecting encryption keys outside the application database."""

    def get_key_id(self, *, purpose: str, context: dict[str, str] | None = None) -> str:
        """Resolve an external key identifier for a given security purpose."""


class AuditLogger(Protocol):
    """Abstraction for immutable security audit logging."""

    def log_secret_formulation_decryption(
        self,
        *,
        formulation_id: str,
        encryption_version: int,
        requested_by: str,
        reason: str,
        client_ip: str,
        organization_id: str,
        branch_id: str,
        recipe_id: str,
        recipe_version_id: str,
        request_timestamp,
        outcome: str,
    ) -> None:
        """Persist one immutable decryption audit event."""
