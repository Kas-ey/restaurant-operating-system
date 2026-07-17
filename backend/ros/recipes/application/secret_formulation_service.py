"""Application service for secret formulation workflows."""

from __future__ import annotations

from datetime import datetime
from http import HTTPStatus
from uuid import uuid4

from ros.shared.exceptions import ROSException

from ..persistence.models import (
    RecipeSecurityClassificationEnum,
    SecretFormulationAccessAuditModel,
    SecretFormulationModel,
)
from ..persistence.repositories import SecretFormulationAccessAuditRepository, SecretFormulationRepository
from .security import AuditLogger, DecryptionProvider, EncryptionProvider, KeyProvider


class RepositoryAuditLogger:
    """Default audit logger implementation backed by recipes persistence."""

    def __init__(self, repository: SecretFormulationAccessAuditRepository | None = None) -> None:
        self._repository = repository or SecretFormulationAccessAuditRepository()

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
        request_timestamp: datetime,
        outcome: str,
    ) -> None:
        audit = SecretFormulationAccessAuditModel(
            id=str(uuid4()),
            secret_formulation_id=formulation_id,
            organization_id=organization_id,
            branch_id=branch_id,
            recipe_id=recipe_id,
            recipe_version_id=recipe_version_id,
            encryption_version=encryption_version,
            requested_by=requested_by,
            reason=reason,
            client_ip=client_ip,
            request_timestamp=request_timestamp,
            outcome=outcome,
        )
        self._repository.create(audit)


class SecretFormulationService:
    """Encapsulates encrypted secret formulation workflows."""

    def __init__(
        self,
        *,
        repository: SecretFormulationRepository | None = None,
        encryption_provider: EncryptionProvider | None = None,
        decryption_provider: DecryptionProvider | None = None,
        key_provider: KeyProvider | None = None,
        audit_logger: AuditLogger | None = None,
    ) -> None:
        self._repository = repository or SecretFormulationRepository()
        self._encryption_provider = encryption_provider
        self._decryption_provider = decryption_provider
        self._key_provider = key_provider
        self._audit_logger = audit_logger or RepositoryAuditLogger()

    def configure_providers(
        self,
        *,
        encryption_provider: EncryptionProvider | None,
        decryption_provider: DecryptionProvider | None,
        key_provider: KeyProvider | None,
        audit_logger: AuditLogger | None = None,
    ) -> None:
        self._encryption_provider = encryption_provider
        self._decryption_provider = decryption_provider
        self._key_provider = key_provider
        if audit_logger is not None:
            self._audit_logger = audit_logger

    def create_formulation(
        self,
        *,
        formulation_id: str,
        code: str,
        name: str,
        description: str,
        security_classification: str,
        plaintext_payload: str,
        created_by: str,
        allow_manage: bool,
    ) -> SecretFormulationModel:
        self._require_manage_permission(allow_manage)
        provider = self._require_encryption_provider()
        key_id = self._require_key_provider().get_key_id(
            purpose="secret_formulation.encrypt",
            context={"code": code.strip().upper()},
        )
        normalized_code = code.strip().upper()
        if self._repository.exists_by_code(normalized_code):
            raise ROSException("Secret formulation code already exists.", HTTPStatus.CONFLICT)

        clean_payload = self._require_non_empty(plaintext_payload, "payload")
        encrypted_payload = provider.encrypt(
            clean_payload,
            context={"secret_formulation_code": normalized_code, "created_by": created_by.strip(), "key_id": key_id},
        )

        model = SecretFormulationModel(
            id=self._require_non_empty(formulation_id, "id"),
            code=normalized_code,
            name=self._require_non_empty(name, "name"),
            description=self._require_non_empty(description, "description"),
            security_classification=self._parse_security_classification(security_classification),
            encrypted_payload=encrypted_payload,
            encryption_version=1,
            created_by=self._require_non_empty(created_by, "created_by"),
        )
        return self._repository.create(model)

    def list_formulations(self) -> list[SecretFormulationModel]:
        return self._repository.get_all()

    def get_formulation(self, formulation_id: str) -> SecretFormulationModel:
        formulation = self._repository.get_by_id(formulation_id)
        if formulation is None:
            raise ROSException("Secret formulation not found.", HTTPStatus.NOT_FOUND)
        return formulation

    def create_new_version(
        self,
        formulation_id: str,
        *,
        name: str | None,
        description: str | None,
        security_classification: str | None,
        plaintext_payload: str,
        allow_manage: bool,
    ) -> SecretFormulationModel:
        self._require_manage_permission(allow_manage)
        provider = self._require_encryption_provider()
        key_id = self._require_key_provider().get_key_id(
            purpose="secret_formulation.encrypt",
            context={"formulation_id": formulation_id},
        )
        formulation = self.get_formulation(formulation_id)
        if not formulation.is_active:
            raise ROSException("Archived secret formulations cannot be edited.", HTTPStatus.CONFLICT)

        clean_payload = self._require_non_empty(plaintext_payload, "payload")
        encrypted_payload = provider.encrypt(
            clean_payload,
            context={
                "secret_formulation_code": formulation.code,
                "encryption_version": str(formulation.encryption_version + 1),
                "key_id": key_id,
            },
        )

        if name is not None:
            formulation.name = self._require_non_empty(name, "name")
        if description is not None:
            formulation.description = self._require_non_empty(description, "description")
        if security_classification is not None:
            formulation.security_classification = self._parse_security_classification(security_classification)

        formulation.encrypted_payload = encrypted_payload
        formulation.encryption_version += 1
        return self._repository.update(formulation)

    def archive(self, formulation_id: str, *, allow_manage: bool) -> SecretFormulationModel:
        self._require_manage_permission(allow_manage)
        formulation = self.get_formulation(formulation_id)
        formulation.is_active = False
        return self._repository.update(formulation)

    def decrypt_formulation(
        self,
        formulation_id: str,
        *,
        requested_by: str,
        reason: str,
        client_ip: str,
        organization_id: str,
        branch_id: str,
        recipe_id: str,
        recipe_version_id: str,
        request_timestamp: datetime,
        allow_view: bool,
    ) -> str:
        formulation = self.get_formulation(formulation_id)
        if not formulation.is_active:
            raise ROSException("Archived secret formulations cannot be decrypted.", HTTPStatus.CONFLICT)

        requested_by_value = self._require_non_empty(requested_by, "requested_by")
        reason_value = self._require_non_empty(reason, "reason")
        client_ip_value = self._require_non_empty(client_ip, "client_ip")
        organization_id_value = self._require_non_empty(organization_id, "organization_id")
        branch_id_value = self._require_non_empty(branch_id, "branch_id")
        recipe_id_value = self._require_non_empty(recipe_id, "recipe_id")
        recipe_version_id_value = self._require_non_empty(recipe_version_id, "recipe_version_id")

        if not allow_view:
            self._audit_logger.log_secret_formulation_decryption(
                formulation_id=formulation.id,
                encryption_version=formulation.encryption_version,
                requested_by=requested_by_value,
                reason=reason_value,
                client_ip=client_ip_value,
                organization_id=organization_id_value,
                branch_id=branch_id_value,
                recipe_id=recipe_id_value,
                recipe_version_id=recipe_version_id_value,
                request_timestamp=request_timestamp,
                outcome="FORBIDDEN",
            )
            raise ROSException("Forbidden.", HTTPStatus.FORBIDDEN)

        provider = self._require_decryption_provider()
        key_id = self._require_key_provider().get_key_id(
            purpose="secret_formulation.decrypt",
            context={"formulation_id": formulation.id},
        )
        try:
            plaintext = provider.decrypt(
                formulation.encrypted_payload,
                context={
                    "secret_formulation_code": formulation.code,
                    "encryption_version": str(formulation.encryption_version),
                    "key_id": key_id,
                },
            )
        except Exception as exc:
            self._audit_logger.log_secret_formulation_decryption(
                formulation_id=formulation.id,
                encryption_version=formulation.encryption_version,
                requested_by=requested_by_value,
                reason=reason_value,
                client_ip=client_ip_value,
                organization_id=organization_id_value,
                branch_id=branch_id_value,
                recipe_id=recipe_id_value,
                recipe_version_id=recipe_version_id_value,
                request_timestamp=request_timestamp,
                outcome="FAILED",
            )
            raise ROSException("Unable to decrypt secret formulation.", HTTPStatus.INTERNAL_SERVER_ERROR) from exc

        self._audit_logger.log_secret_formulation_decryption(
            formulation_id=formulation.id,
            encryption_version=formulation.encryption_version,
            requested_by=requested_by_value,
            reason=reason_value,
            client_ip=client_ip_value,
            organization_id=organization_id_value,
            branch_id=branch_id_value,
            recipe_id=recipe_id_value,
            recipe_version_id=recipe_version_id_value,
            request_timestamp=request_timestamp,
            outcome="SUCCESS",
        )
        return plaintext

    def protect_deletion(self, formulation_id: str) -> None:
        formulation = self.get_formulation(formulation_id)
        if self._repository.has_ingredients_reference(formulation.id):
            raise ROSException("Deletion is prohibited for referenced secret formulations.", HTTPStatus.CONFLICT)
        raise ROSException("Secret formulations cannot be deleted.", HTTPStatus.METHOD_NOT_ALLOWED)

    @staticmethod
    def _require_manage_permission(allow_manage: bool) -> None:
        if not allow_manage:
            raise ROSException("Forbidden.", HTTPStatus.FORBIDDEN)

    def _require_encryption_provider(self) -> EncryptionProvider:
        if self._encryption_provider is None:
            raise ROSException("Encryption provider is not configured.", HTTPStatus.INTERNAL_SERVER_ERROR)
        return self._encryption_provider

    def _require_decryption_provider(self) -> DecryptionProvider:
        if self._decryption_provider is None:
            raise ROSException("Decryption provider is not configured.", HTTPStatus.INTERNAL_SERVER_ERROR)
        return self._decryption_provider

    def _require_key_provider(self) -> KeyProvider:
        if self._key_provider is None:
            raise ROSException("Key provider is not configured.", HTTPStatus.INTERNAL_SERVER_ERROR)
        return self._key_provider

    @staticmethod
    def _parse_security_classification(value: str) -> RecipeSecurityClassificationEnum:
        try:
            return RecipeSecurityClassificationEnum(value.strip().upper())
        except ValueError as exc:
            raise ROSException("Invalid security classification.", HTTPStatus.BAD_REQUEST) from exc

    @staticmethod
    def _require_non_empty(value: str, field_name: str) -> str:
        normalized = value.strip() if isinstance(value, str) else ""
        if not normalized:
            raise ROSException(f"Field '{field_name}' is required.", HTTPStatus.BAD_REQUEST)
        return normalized
