"""Domain exceptions for Recipe entities."""


class RecipeDomainError(ValueError):
    """Raised when Recipe invariants are violated."""


class RecipeVersionDomainError(ValueError):
    """Raised when RecipeVersion invariants are violated."""
