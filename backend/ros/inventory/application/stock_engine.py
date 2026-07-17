"""Internal stock movement and projection services for Inventory."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from http import HTTPStatus
from uuid import uuid4

from sqlalchemy import delete

from ros.core.extensions import db
from ros.inventory.persistence.models import (
    InventoryNegativePolicyEnum,
    InventoryReferenceTypeEnum,
    StockAdjustmentModel,
    StockAdjustmentTypeEnum,
    InventoryTransactionModel,
    InventoryTransactionTypeEnum,
    StockLevelModel,
)
from ros.inventory.persistence.repositories import (
    InventoryItemRepository,
    InventoryLocationRepository,
    InventoryLotRepository,
    StockAdjustmentRepository,
    InventoryTransactionRepository,
    StockLevelRepository,
)
from ros.shared.exceptions import ROSException


_QUANTIZE_PRECISION = Decimal("0.0001")
_PROJECTION_UPDATE_TOKEN = object()


@dataclass(slots=True)
class StockMovementResult:
    """Return value for stock movement requests."""

    transaction: InventoryTransactionModel
    stock_level: StockLevelModel


class StockLevelService:
    """Owns stock projection lifecycle and consistency."""

    def __init__(
        self,
        stock_level_repository: StockLevelRepository | None = None,
        transaction_repository: InventoryTransactionRepository | None = None,
    ) -> None:
        self._stock_level_repository = stock_level_repository or StockLevelRepository()
        self._transaction_repository = transaction_repository or InventoryTransactionRepository()

    def get_or_create_projection(self, inventory_item_id: str, location_id: str) -> StockLevelModel:
        normalized_item_id = self._require_text(inventory_item_id, "Inventory item ID is required.")
        normalized_location_id = self._require_text(location_id, "Location ID is required.")
        existing = self._stock_level_repository.get_by_item_and_location(normalized_item_id, normalized_location_id)
        if existing is not None:
            return existing

        model = StockLevelModel(
            id=self._new_id(),
            inventory_item_id=normalized_item_id,
            location_id=normalized_location_id,
            quantity=Decimal("0.0000"),
            reserved_quantity=Decimal("0.0000"),
            available_quantity=Decimal("0.0000"),
            last_transaction_id=None,
        )
        return self._stock_level_repository.create_if_missing(model)

    def recalculate_projection(self, inventory_item_id: str, location_id: str) -> StockLevelModel:
        projection = self.get_or_create_projection(inventory_item_id, location_id)
        quantity = Decimal("0.0000")
        reserved_quantity = Decimal(str(projection.reserved_quantity or Decimal("0.0000"))).quantize(_QUANTIZE_PRECISION)

        transactions = self._transaction_repository.get_by_item(inventory_item_id)
        scoped_transactions = [
            transaction for transaction in transactions if transaction.location_id == location_id
        ]

        last_transaction: InventoryTransactionModel | None = None
        for transaction in sorted(scoped_transactions, key=lambda item: item.performed_at):
            quantity += self._signed_delta(transaction.transaction_type, transaction.quantity)
            last_transaction = transaction

        return self.update_projection(
            projection,
            quantity=quantity,
            reserved_quantity=reserved_quantity,
            last_transaction_id=last_transaction.id if last_transaction is not None else None,
            projection_update_token=_PROJECTION_UPDATE_TOKEN,
        )

    def update_projection(
        self,
        projection: StockLevelModel,
        *,
        quantity: Decimal,
        reserved_quantity: Decimal,
        last_transaction_id: str | None,
        projection_update_token: object,
    ) -> StockLevelModel:
        if projection_update_token is not _PROJECTION_UPDATE_TOKEN:
            raise ROSException("Stock projection updates are restricted to Inventory workflows.", HTTPStatus.FORBIDDEN)

        normalized_quantity = self._normalize_decimal(quantity, "Stock quantity must be a valid decimal.")
        normalized_reserved = self._normalize_decimal(
            reserved_quantity,
            "Reserved quantity must be a valid decimal.",
        )
        if normalized_reserved < 0:
            raise ROSException("Reserved quantity cannot be negative.", HTTPStatus.BAD_REQUEST)

        projection.quantity = normalized_quantity
        projection.reserved_quantity = normalized_reserved
        projection.available_quantity = (normalized_quantity - normalized_reserved).quantize(_QUANTIZE_PRECISION)
        projection.last_transaction_id = last_transaction_id
        self.validate_projection_consistency(projection)
        return self._stock_level_repository.update_projection(projection)

    def validate_projection_consistency(self, projection: StockLevelModel) -> None:
        quantity = Decimal(str(projection.quantity)).quantize(_QUANTIZE_PRECISION)
        reserved = Decimal(str(projection.reserved_quantity)).quantize(_QUANTIZE_PRECISION)
        available = Decimal(str(projection.available_quantity)).quantize(_QUANTIZE_PRECISION)
        if available != (quantity - reserved).quantize(_QUANTIZE_PRECISION):
            raise ROSException("Stock projection is inconsistent.", HTTPStatus.CONFLICT)

    def list_projections(self) -> list[StockLevelModel]:
        return self._stock_level_repository.get_all()

    def list_projections_by_item(self, inventory_item_id: str) -> list[StockLevelModel]:
        normalized_item_id = self._require_text(inventory_item_id, "Inventory item ID is required.")
        return self._stock_level_repository.get_by_item(normalized_item_id)

    def list_projections_by_location(self, location_id: str) -> list[StockLevelModel]:
        normalized_location_id = self._require_text(location_id, "Location ID is required.")
        return self._stock_level_repository.get_by_location(normalized_location_id)

    def get_projection(self, inventory_item_id: str, location_id: str) -> StockLevelModel:
        normalized_item_id = self._require_text(inventory_item_id, "Inventory item ID is required.")
        normalized_location_id = self._require_text(location_id, "Location ID is required.")
        projection = self._stock_level_repository.get_by_item_and_location(normalized_item_id, normalized_location_id)
        if projection is None:
            raise ROSException("Stock level not found.", HTTPStatus.NOT_FOUND)
        return projection

    @staticmethod
    def _new_id() -> str:
        return uuid4().hex

    @staticmethod
    def _require_text(value: str, message: str) -> str:
        normalized = value.strip() if isinstance(value, str) else ""
        normalized = " ".join(normalized.split())
        if not normalized:
            raise ROSException(message, HTTPStatus.BAD_REQUEST)
        return normalized

    @staticmethod
    def _normalize_decimal(value: Decimal | str | int | float, message: str) -> Decimal:
        try:
            decimal_value = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ROSException(message, HTTPStatus.BAD_REQUEST) from exc
        if not decimal_value.is_finite():
            raise ROSException(message, HTTPStatus.BAD_REQUEST)
        return decimal_value.quantize(_QUANTIZE_PRECISION)

    @staticmethod
    def _signed_delta(transaction_type: InventoryTransactionTypeEnum, quantity: Decimal | str | int | float) -> Decimal:
        normalized_quantity = StockLevelService._normalize_decimal(quantity, "Transaction quantity must be a valid decimal.")
        increase_types = {
            InventoryTransactionTypeEnum.RECEIVE,
            InventoryTransactionTypeEnum.TRANSFER_IN,
            InventoryTransactionTypeEnum.ADJUSTMENT_POSITIVE,
            InventoryTransactionTypeEnum.RETURN,
            InventoryTransactionTypeEnum.PRODUCTION_OUTPUT,
        }
        decrease_types = {
            InventoryTransactionTypeEnum.ISSUE,
            InventoryTransactionTypeEnum.CONSUMPTION,
            InventoryTransactionTypeEnum.TRANSFER_OUT,
            InventoryTransactionTypeEnum.ADJUSTMENT_NEGATIVE,
            InventoryTransactionTypeEnum.WASTE,
        }
        if transaction_type in increase_types:
            return normalized_quantity
        if transaction_type in decrease_types:
            return -normalized_quantity
        raise ROSException("Unsupported transaction type.", HTTPStatus.BAD_REQUEST)


class InventoryTransactionService:
    """Creates immutable inventory ledger records."""

    def __init__(
        self,
        transaction_repository: InventoryTransactionRepository | None = None,
        item_repository: InventoryItemRepository | None = None,
        location_repository: InventoryLocationRepository | None = None,
        lot_repository: InventoryLotRepository | None = None,
        stock_level_service: StockLevelService | None = None,
    ) -> None:
        self._transaction_repository = transaction_repository or InventoryTransactionRepository()
        self._item_repository = item_repository or InventoryItemRepository()
        self._location_repository = location_repository or InventoryLocationRepository()
        self._lot_repository = lot_repository or InventoryLotRepository()
        self._stock_level_service = stock_level_service or StockLevelService(
            stock_level_repository=StockLevelRepository(),
            transaction_repository=self._transaction_repository,
        )

    def create_transaction(
        self,
        *,
        transaction_id: str,
        inventory_item_id: str,
        location_id: str,
        transaction_type: InventoryTransactionTypeEnum | str,
        quantity: Decimal | str | int | float,
        reference_type: str,
        reference_id: str,
        reference_number: str | None,
        performed_by: str,
        notes: str | None = None,
        inventory_lot_id: str | None = None,
        metadata: dict | None = None,
    ) -> InventoryTransactionModel:
        normalized_transaction_id = self._require_text(transaction_id, "Transaction ID is required.")
        if self._transaction_repository.get_by_id(normalized_transaction_id) is not None:
            raise ROSException("Inventory transaction already exists.", HTTPStatus.CONFLICT)
        item = self._get_item(inventory_item_id)
        location = self._get_location(location_id)
        lot = self._get_optional_lot(item.id, inventory_lot_id)
        normalized_transaction_type = self._normalize_transaction_type(transaction_type)
        normalized_quantity = self._normalize_positive_decimal(quantity, "Transaction quantity must be greater than zero.")
        normalized_reference_type = self._normalize_reference_type(reference_type)
        normalized_reference_id = self._require_text(reference_id, "Reference ID is required.")
        normalized_reference_number = self._normalize_optional_text(reference_number)
        normalized_performed_by = self._require_text(performed_by, "Performed by is required.")
        normalized_notes = self._normalize_optional_text(notes)

        transaction = InventoryTransactionModel(
            id=normalized_transaction_id,
            inventory_item_id=item.id,
            inventory_lot_id=lot.id if lot is not None else None,
            location_id=location.id,
            transaction_type=normalized_transaction_type,
            quantity=normalized_quantity,
            reference_type=normalized_reference_type.value,
            reference_id=normalized_reference_id,
            reference_number=normalized_reference_number,
            performed_by=normalized_performed_by,
            performed_at=datetime.now(tz=UTC),
            notes=normalized_notes,
            transaction_metadata=metadata,
        )
        return self._transaction_repository.create(transaction)

    def get_transaction(self, transaction_id: str) -> InventoryTransactionModel:
        normalized_id = self._require_text(transaction_id, "Transaction ID is required.")
        model = self._transaction_repository.get_by_id(normalized_id)
        if model is None:
            raise ROSException("Inventory transaction not found.", HTTPStatus.NOT_FOUND)
        return model

    def list_transactions(self) -> list[InventoryTransactionModel]:
        return self._transaction_repository.get_all()

    def list_transactions_by_item(self, inventory_item_id: str) -> list[InventoryTransactionModel]:
        item = self._get_item(inventory_item_id)
        return self._transaction_repository.get_by_item(item.id)

    def list_transactions_by_reference(self, reference_type: str, reference_id: str) -> list[InventoryTransactionModel]:
        normalized_reference_type = self._normalize_reference_type(reference_type)
        normalized_reference_id = self._require_text(reference_id, "Reference ID is required.")
        return self._transaction_repository.get_by_reference(normalized_reference_type, normalized_reference_id)

    def list_transactions_by_date_range(
        self,
        *,
        start_at: datetime | None,
        end_at: datetime | None,
    ) -> list[InventoryTransactionModel]:
        normalized_start, normalized_end = self._normalize_date_range(start_at, end_at)
        return self._transaction_repository.get_by_date_range(normalized_start, normalized_end)

    def request_projection_update(self, inventory_item_id: str, location_id: str) -> StockLevelModel:
        item = self._get_item(inventory_item_id)
        location = self._get_location(location_id)
        return self._stock_level_service.recalculate_projection(item.id, location.id)

    def _get_item(self, item_id: str):
        normalized_id = self._require_text(item_id, "Inventory item ID is required.")
        model = self._item_repository.get_by_id(normalized_id)
        if model is None:
            raise ROSException("Inventory item not found.", HTTPStatus.NOT_FOUND)
        if not model.is_active:
            raise ROSException("Inventory item is inactive.", HTTPStatus.CONFLICT)
        return model

    def _get_location(self, location_id: str):
        normalized_id = self._require_text(location_id, "Location ID is required.")
        model = self._location_repository.get_by_id(normalized_id)
        if model is None:
            raise ROSException("Inventory location not found.", HTTPStatus.NOT_FOUND)
        if not model.is_active:
            raise ROSException("Inventory location is inactive.", HTTPStatus.CONFLICT)
        return model

    def _get_optional_lot(self, item_id: str, lot_id: str | None):
        if lot_id is None:
            return None
        normalized_lot_id = self._require_text(lot_id, "Inventory lot ID is required.")
        lot = self._lot_repository.get_by_id(normalized_lot_id)
        if lot is None:
            raise ROSException("Inventory lot not found.", HTTPStatus.NOT_FOUND)
        if lot.inventory_item_id != item_id:
            raise ROSException("Inventory lot does not belong to the specified item.", HTTPStatus.CONFLICT)
        return lot

    @staticmethod
    def _normalize_transaction_type(value: InventoryTransactionTypeEnum | str) -> InventoryTransactionTypeEnum:
        if isinstance(value, InventoryTransactionTypeEnum):
            return value
        try:
            return InventoryTransactionTypeEnum(str(value))
        except ValueError as exc:
            raise ROSException("Invalid transaction type.", HTTPStatus.BAD_REQUEST) from exc

    @staticmethod
    def _normalize_reference_type(value: InventoryReferenceTypeEnum | str) -> InventoryReferenceTypeEnum:
        if isinstance(value, InventoryReferenceTypeEnum):
            return value
        try:
            return InventoryReferenceTypeEnum(str(value))
        except ValueError as exc:
            raise ROSException("Invalid reference type.", HTTPStatus.BAD_REQUEST) from exc

    @staticmethod
    def _normalize_date_range(
        start_at: datetime | None,
        end_at: datetime | None,
    ) -> tuple[datetime | None, datetime | None]:
        normalized_start = start_at
        normalized_end = end_at
        if normalized_start is not None and normalized_start.tzinfo is None:
            normalized_start = normalized_start.replace(tzinfo=UTC)
        if normalized_end is not None and normalized_end.tzinfo is None:
            normalized_end = normalized_end.replace(tzinfo=UTC)
        if normalized_start is not None and normalized_end is not None and normalized_start > normalized_end:
            raise ROSException("Start datetime cannot be after end datetime.", HTTPStatus.BAD_REQUEST)
        return normalized_start, normalized_end

    @staticmethod
    def _normalize_positive_decimal(value: Decimal | str | int | float, message: str) -> Decimal:
        try:
            decimal_value = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ROSException(message, HTTPStatus.BAD_REQUEST) from exc
        if not decimal_value.is_finite() or decimal_value <= 0:
            raise ROSException(message, HTTPStatus.BAD_REQUEST)
        return decimal_value.quantize(_QUANTIZE_PRECISION)

    @staticmethod
    def _require_text(value: str, message: str) -> str:
        normalized = value.strip() if isinstance(value, str) else ""
        normalized = " ".join(normalized.split())
        if not normalized:
            raise ROSException(message, HTTPStatus.BAD_REQUEST)
        return normalized

    @classmethod
    def _normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return cls._require_text(value, "Optional text field cannot be empty.")


class StockMovementEngine:
    """The only workflow allowed to mutate stock projections."""

    def __init__(
        self,
        transaction_service: InventoryTransactionService | None = None,
        stock_level_service: StockLevelService | None = None,
        item_repository: InventoryItemRepository | None = None,
        location_repository: InventoryLocationRepository | None = None,
        lot_repository: InventoryLotRepository | None = None,
    ) -> None:
        self._stock_level_service = stock_level_service or StockLevelService()
        self._transaction_service = transaction_service or InventoryTransactionService(
            transaction_repository=InventoryTransactionRepository(),
            item_repository=item_repository or InventoryItemRepository(),
            location_repository=location_repository or InventoryLocationRepository(),
            lot_repository=lot_repository or InventoryLotRepository(),
            stock_level_service=self._stock_level_service,
        )
        self._item_repository = item_repository or InventoryItemRepository()
        self._location_repository = location_repository or InventoryLocationRepository()
        self._lot_repository = lot_repository or InventoryLotRepository()

    def move_stock(
        self,
        *,
        movement_type: InventoryTransactionTypeEnum | str,
        inventory_item_id: str,
        location_id: str,
        quantity: Decimal | str | int | float,
        lot_id: str | None,
        reference_type: InventoryReferenceTypeEnum | str,
        reference_id: str,
        reference_number: str | None,
        performed_by: str,
        reason: str | None,
        transaction_id: str | None = None,
        negative_policy: InventoryNegativePolicyEnum | str = InventoryNegativePolicyEnum.STRICT,
        approving_manager: str | None = None,
        approval_reason: str | None = None,
        approval_timestamp: datetime | None = None,
    ) -> StockMovementResult:
        normalized_type = InventoryTransactionService._normalize_transaction_type(movement_type)
        normalized_reference_type = InventoryTransactionService._normalize_reference_type(reference_type)
        normalized_policy = self._normalize_negative_policy(negative_policy)
        normalized_quantity = InventoryTransactionService._normalize_positive_decimal(
            quantity,
            "Movement quantity must be greater than zero.",
        )

        item = self._get_item(inventory_item_id)
        location = self._get_location(location_id)
        self._get_optional_lot(item.id, lot_id)

        projection = self._stock_level_service.get_or_create_projection(item.id, location.id)
        current_quantity = Decimal(str(projection.quantity)).quantize(_QUANTIZE_PRECISION)
        reserved_quantity = Decimal(str(projection.reserved_quantity)).quantize(_QUANTIZE_PRECISION)
        delta = StockLevelService._signed_delta(normalized_type, normalized_quantity)
        next_quantity = (current_quantity + delta).quantize(_QUANTIZE_PRECISION)
        next_available = (next_quantity - reserved_quantity).quantize(_QUANTIZE_PRECISION)

        transaction_metadata = self._build_transaction_metadata(
            negative_policy=normalized_policy,
            next_available=next_available,
            approving_manager=approving_manager,
            approval_reason=approval_reason,
            approval_timestamp=approval_timestamp,
        )

        transaction = self._transaction_service.create_transaction(
            transaction_id=transaction_id or uuid4().hex,
            inventory_item_id=item.id,
            inventory_lot_id=lot_id,
            location_id=location.id,
            transaction_type=normalized_type,
            quantity=normalized_quantity,
            reference_type=normalized_reference_type.value,
            reference_id=reference_id,
            reference_number=reference_number,
            performed_by=performed_by,
            notes=reason,
            metadata=transaction_metadata,
        )

        updated_projection = self._transaction_service.request_projection_update(item.id, location.id)
        return StockMovementResult(transaction=transaction, stock_level=updated_projection)

    def _build_transaction_metadata(
        self,
        *,
        negative_policy: InventoryNegativePolicyEnum,
        next_available: Decimal,
        approving_manager: str | None,
        approval_reason: str | None,
        approval_timestamp: datetime | None,
    ) -> dict | None:
        if next_available >= 0:
            return None

        if negative_policy == InventoryNegativePolicyEnum.STRICT:
            raise ROSException("Negative inventory is not allowed under STRICT policy.", HTTPStatus.CONFLICT)

        if negative_policy == InventoryNegativePolicyEnum.ALLOW:
            return {
                "negative_policy": InventoryNegativePolicyEnum.ALLOW.value,
                "allow_negative": True,
            }

        normalized_manager = InventoryTransactionService._require_text(
            approving_manager,
            "Approving manager is required for MANAGER_OVERRIDE policy.",
        )
        normalized_reason = InventoryTransactionService._require_text(
            approval_reason,
            "Approval reason is required for MANAGER_OVERRIDE policy.",
        )
        normalized_timestamp = approval_timestamp or datetime.now(tz=UTC)
        if normalized_timestamp.tzinfo is None:
            normalized_timestamp = normalized_timestamp.replace(tzinfo=UTC)

        return {
            "negative_policy": InventoryNegativePolicyEnum.MANAGER_OVERRIDE.value,
            "approving_manager": normalized_manager,
            "approval_reason": normalized_reason,
            "approval_timestamp": normalized_timestamp.isoformat(),
        }

    def _get_item(self, item_id: str):
        model = self._item_repository.get_by_id(InventoryTransactionService._require_text(item_id, "Inventory item ID is required."))
        if model is None:
            raise ROSException("Inventory item not found.", HTTPStatus.NOT_FOUND)
        if not model.is_active:
            raise ROSException("Inventory item is inactive.", HTTPStatus.CONFLICT)
        return model

    def _get_location(self, location_id: str):
        model = self._location_repository.get_by_id(
            InventoryTransactionService._require_text(location_id, "Location ID is required.")
        )
        if model is None:
            raise ROSException("Inventory location not found.", HTTPStatus.NOT_FOUND)
        if not model.is_active:
            raise ROSException("Inventory location is inactive.", HTTPStatus.CONFLICT)
        return model

    def _get_optional_lot(self, item_id: str, lot_id: str | None):
        if lot_id is None:
            return None
        normalized_lot_id = InventoryTransactionService._require_text(lot_id, "Inventory lot ID is required.")
        lot = self._lot_repository.get_by_id(normalized_lot_id)
        if lot is None:
            raise ROSException("Inventory lot not found.", HTTPStatus.NOT_FOUND)
        if lot.inventory_item_id != item_id:
            raise ROSException("Inventory lot does not belong to the specified item.", HTTPStatus.CONFLICT)
        return lot

    @staticmethod
    def _normalize_negative_policy(value: InventoryNegativePolicyEnum | str) -> InventoryNegativePolicyEnum:
        if isinstance(value, InventoryNegativePolicyEnum):
            return value
        try:
            return InventoryNegativePolicyEnum(str(value))
        except ValueError as exc:
            raise ROSException("Invalid negative inventory policy.", HTTPStatus.BAD_REQUEST) from exc


class RebuildProjectionService:
    """Internal projection rebuild service that replays immutable ledger records."""

    def __init__(
        self,
        stock_level_service: StockLevelService | None = None,
        transaction_repository: InventoryTransactionRepository | None = None,
    ) -> None:
        self._stock_level_service = stock_level_service or StockLevelService()
        self._transaction_repository = transaction_repository or InventoryTransactionRepository()

    def rebuild(self) -> list[StockLevelModel]:
        db.session.execute(delete(StockLevelModel))

        projections: dict[tuple[str, str], StockLevelModel] = {}
        transactions = sorted(self._transaction_repository.get_all(), key=lambda model: model.performed_at)

        for transaction in transactions:
            key = (transaction.inventory_item_id, transaction.location_id)
            projection = projections.get(key)
            if projection is None:
                projection = self._stock_level_service.get_or_create_projection(*key)
                projections[key] = projection

            current_quantity = Decimal(str(projection.quantity)).quantize(_QUANTIZE_PRECISION)
            reserved_quantity = Decimal(str(projection.reserved_quantity)).quantize(_QUANTIZE_PRECISION)
            delta = StockLevelService._signed_delta(transaction.transaction_type, transaction.quantity)
            next_quantity = (current_quantity + delta).quantize(_QUANTIZE_PRECISION)

            projection = self._stock_level_service.update_projection(
                projection,
                quantity=next_quantity,
                reserved_quantity=reserved_quantity,
                last_transaction_id=transaction.id,
                projection_update_token=_PROJECTION_UPDATE_TOKEN,
            )
            projections[key] = projection

        return list(projections.values())


class StockAdjustmentService:
    """Workflow service for immutable stock adjustment records."""

    def __init__(
        self,
        adjustment_repository: StockAdjustmentRepository | None = None,
        stock_level_service: StockLevelService | None = None,
        stock_movement_engine: StockMovementEngine | None = None,
        item_repository: InventoryItemRepository | None = None,
    ) -> None:
        self._adjustment_repository = adjustment_repository or StockAdjustmentRepository()
        self._stock_level_service = stock_level_service or StockLevelService()
        self._stock_movement_engine = stock_movement_engine or StockMovementEngine(
            stock_level_service=self._stock_level_service,
        )
        self._item_repository = item_repository or InventoryItemRepository()

    def create_adjustment(
        self,
        *,
        adjustment_id: str,
        inventory_item_id: str,
        inventory_location_id: str,
        inventory_lot_id: str | None,
        actual_quantity: Decimal | str | int | float,
        reason: str,
        approved_by: str | None,
        performed_by: str,
        notes: str | None,
        adjustment_type: StockAdjustmentTypeEnum | str | None = None,
        negative_policy: InventoryNegativePolicyEnum | str = InventoryNegativePolicyEnum.STRICT,
        approving_manager: str | None = None,
        approval_reason: str | None = None,
        approval_timestamp: datetime | None = None,
    ) -> StockAdjustmentModel:
        normalized_adjustment_id = InventoryTransactionService._require_text(adjustment_id, "Adjustment ID is required.")
        normalized_item_id = InventoryTransactionService._require_text(inventory_item_id, "Inventory item ID is required.")
        normalized_location_id = InventoryTransactionService._require_text(
            inventory_location_id,
            "Inventory location ID is required.",
        )
        normalized_reason = InventoryTransactionService._require_text(reason, "Adjustment reason is required.")
        normalized_performed_by = InventoryTransactionService._require_text(performed_by, "Performed by is required.")
        normalized_notes = InventoryTransactionService._normalize_optional_text(notes)
        normalized_approved_by = (
            InventoryTransactionService._normalize_optional_text(approved_by) if approved_by is not None else None
        )
        normalized_actual = self._normalize_non_negative_decimal(
            actual_quantity,
            "Actual quantity must be zero or greater.",
        )

        item = self._item_repository.get_by_id(normalized_item_id)
        if item is None:
            raise ROSException("Inventory item not found.", HTTPStatus.NOT_FOUND)
        if not item.is_active:
            raise ROSException("Inventory item is inactive.", HTTPStatus.CONFLICT)

        projection = self._stock_level_service.get_or_create_projection(normalized_item_id, normalized_location_id)
        expected_quantity = Decimal(str(projection.quantity)).quantize(_QUANTIZE_PRECISION)
        variance = (normalized_actual - expected_quantity).quantize(_QUANTIZE_PRECISION)
        if variance == Decimal("0.0000"):
            raise ROSException("Adjustment variance is zero; no stock movement required.", HTTPStatus.BAD_REQUEST)

        calculated_type = (
            StockAdjustmentTypeEnum.POSITIVE if variance > Decimal("0.0000") else StockAdjustmentTypeEnum.NEGATIVE
        )
        if adjustment_type is not None:
            provided_type = self._normalize_adjustment_type(adjustment_type)
            if provided_type != calculated_type:
                raise ROSException("Adjustment type does not match calculated variance.", HTTPStatus.BAD_REQUEST)

        movement_type = (
            InventoryTransactionTypeEnum.ADJUSTMENT_POSITIVE
            if variance > Decimal("0.0000")
            else InventoryTransactionTypeEnum.ADJUSTMENT_NEGATIVE
        )

        movement_result = self._stock_movement_engine.move_stock(
            movement_type=movement_type,
            inventory_item_id=normalized_item_id,
            location_id=normalized_location_id,
            quantity=abs(variance),
            lot_id=inventory_lot_id,
            reference_type=InventoryReferenceTypeEnum.STOCK_ADJUSTMENT.value,
            reference_id=normalized_adjustment_id,
            reference_number=normalized_adjustment_id,
            performed_by=normalized_performed_by,
            reason=normalized_reason,
            negative_policy=negative_policy,
            approving_manager=approving_manager,
            approval_reason=approval_reason,
            approval_timestamp=approval_timestamp,
        )

        adjustment = StockAdjustmentModel(
            id=normalized_adjustment_id,
            inventory_item_id=normalized_item_id,
            inventory_location_id=normalized_location_id,
            inventory_lot_id=inventory_lot_id,
            inventory_transaction_id=movement_result.transaction.id,
            adjustment_type=calculated_type,
            expected_quantity=expected_quantity,
            actual_quantity=normalized_actual,
            variance=variance,
            reason=normalized_reason,
            approved_by=normalized_approved_by,
            performed_by=normalized_performed_by,
            performed_at=movement_result.transaction.performed_at,
            notes=normalized_notes,
        )
        return self._adjustment_repository.create(adjustment)

    def get_adjustment(self, adjustment_id: str) -> StockAdjustmentModel:
        normalized_id = InventoryTransactionService._require_text(adjustment_id, "Adjustment ID is required.")
        adjustment = self._adjustment_repository.get_by_id(normalized_id)
        if adjustment is None:
            raise ROSException("Stock adjustment not found.", HTTPStatus.NOT_FOUND)
        return adjustment

    def list_adjustments(self) -> list[StockAdjustmentModel]:
        return self._adjustment_repository.get_all()

    def list_adjustments_by_item(self, inventory_item_id: str) -> list[StockAdjustmentModel]:
        normalized_item_id = InventoryTransactionService._require_text(inventory_item_id, "Inventory item ID is required.")
        return self._adjustment_repository.get_by_item(normalized_item_id)

    def list_adjustments_by_date_range(
        self,
        *,
        start_at: datetime | None,
        end_at: datetime | None,
    ) -> list[StockAdjustmentModel]:
        normalized_start, normalized_end = InventoryTransactionService._normalize_date_range(start_at, end_at)
        return self._adjustment_repository.get_by_date_range(normalized_start, normalized_end)

    @staticmethod
    def _normalize_adjustment_type(value: StockAdjustmentTypeEnum | str) -> StockAdjustmentTypeEnum:
        if isinstance(value, StockAdjustmentTypeEnum):
            return value
        try:
            return StockAdjustmentTypeEnum(str(value))
        except ValueError as exc:
            raise ROSException("Invalid adjustment type.", HTTPStatus.BAD_REQUEST) from exc

    @staticmethod
    def _normalize_non_negative_decimal(value: Decimal | str | int | float, message: str) -> Decimal:
        try:
            decimal_value = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ROSException(message, HTTPStatus.BAD_REQUEST) from exc
        if not decimal_value.is_finite() or decimal_value < 0:
            raise ROSException(message, HTTPStatus.BAD_REQUEST)
        return decimal_value.quantize(_QUANTIZE_PRECISION)
