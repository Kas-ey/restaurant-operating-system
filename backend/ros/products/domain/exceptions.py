"""Domain exceptions for Products entities."""


class ProductCategoryDomainError(ValueError):
    """Raised when ProductCategory invariants are violated."""


class ProductDomainError(ValueError):
    """Raised when Product invariants are violated."""


class ProductVariantDomainError(ValueError):
    """Raised when ProductVariant invariants are violated."""


class ModifierGroupDomainError(ValueError):
    """Raised when ModifierGroup invariants are violated."""


class ModifierOptionDomainError(ValueError):
    """Raised when ModifierOption invariants are violated."""


class ProductPriceDomainError(ValueError):
    """Raised when ProductPrice invariants are violated."""


class VariantPriceDomainError(ValueError):
    """Raised when VariantPrice invariants are violated."""
