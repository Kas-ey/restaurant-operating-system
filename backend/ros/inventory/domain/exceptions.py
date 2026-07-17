"""Domain exceptions for Inventory entities."""


class InventoryCategoryDomainError(ValueError):
    """Raised when InventoryCategory invariants are violated."""


class UnitOfMeasureDomainError(ValueError):
    """Raised when UnitOfMeasure invariants are violated."""


class InventoryItemDomainError(ValueError):
    """Raised when InventoryItem invariants are violated."""


class InventoryLotDomainError(ValueError):
    """Raised when InventoryLot invariants are violated."""


class InventoryLocationDomainError(ValueError):
    """Raised when InventoryLocation invariants are violated."""
