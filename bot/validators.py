"""
Input validation logic for the Binance Futures trading bot.
"""

from dataclasses import dataclass
from typing import Optional


VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT"}


class ValidationError(ValueError):
    """Raised when user-supplied input fails validation."""


@dataclass
class OrderParams:
    symbol: str
    side: str
    order_type: str
    quantity: float
    price: Optional[float] = None


def validate_order_params(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float],
) -> OrderParams:
    """
    Validate all order parameters and return a typed OrderParams object.

    Raises:
        ValidationError: on any invalid input.
    """
    # Symbol
    symbol = symbol.strip().upper()
    if not symbol:
        raise ValidationError("Symbol must not be empty.")

    # Side
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValidationError(
            f"Invalid side '{side}'. Must be one of: {', '.join(sorted(VALID_SIDES))}."
        )

    # Order type
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Invalid order type '{order_type}'. "
            f"Must be one of: {', '.join(sorted(VALID_ORDER_TYPES))}."
        )

    # Quantity
    if quantity is None:
        raise ValidationError("Quantity must be provided.")
    if quantity <= 0:
        raise ValidationError(f"Quantity must be a positive number, got {quantity}.")

    # Price (required for LIMIT orders)
    if order_type == "LIMIT":
        if price is None:
            raise ValidationError("Price is required for LIMIT orders.")
        if price <= 0:
            raise ValidationError(f"Price must be a positive number, got {price}.")

    return OrderParams(
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price if order_type == "LIMIT" else None,
    )