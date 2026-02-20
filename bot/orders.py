"""
Order placement logic — orchestrates validation, client call, and result formatting.
"""

from typing import Any, Dict, Optional

from .client import BinanceClient, BinanceAPIError
from .validators import OrderParams, validate_order_params, ValidationError
from .logging_config import get_logger

logger = get_logger(__name__)


class OrderResult:
    """Holds the parsed result of a placed order."""

    def __init__(self, raw: Dict[str, Any]) -> None:
        self.raw = raw
        self.order_id: int = raw.get("orderId", -1)
        self.status: str = raw.get("status", "UNKNOWN")
        self.symbol: str = raw.get("symbol", "")
        self.side: str = raw.get("side", "")
        self.order_type: str = raw.get("type", "")
        self.orig_qty: str = raw.get("origQty", "0")
        self.executed_qty: str = raw.get("executedQty", "0")
        self.avg_price: str = raw.get("avgPrice", raw.get("price", "N/A"))
        self.client_order_id: str = raw.get("clientOrderId", "")
        self.time_in_force: str = raw.get("timeInForce", "")

    def __str__(self) -> str:
        lines = [
            "─" * 50,
            "  ORDER RESPONSE",
            "─" * 50,
            f"  Order ID       : {self.order_id}",
            f"  Status         : {self.status}",
            f"  Symbol         : {self.symbol}",
            f"  Side           : {self.side}",
            f"  Type           : {self.order_type}",
            f"  Orig Qty       : {self.orig_qty}",
            f"  Executed Qty   : {self.executed_qty}",
            f"  Avg Price      : {self.avg_price}",
        ]
        if self.time_in_force:
            lines.append(f"  Time In Force  : {self.time_in_force}")
        lines.append("─" * 50)
        return "\n".join(lines)


def place_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None,
) -> OrderResult:
    """
    Validate inputs and place an order via the Binance client.

    Returns:
        OrderResult on success.

    Raises:
        ValidationError: on invalid input parameters.
        BinanceAPIError: on Binance-side rejection.
        requests.RequestException: on network failures.
    """
    params: OrderParams = validate_order_params(
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
    )

    logger.info(
        "Submitting order | %s %s %s qty=%s price=%s",
        params.side,
        params.order_type,
        params.symbol,
        params.quantity,
        params.price,
    )

    raw = client.place_order(
        symbol=params.symbol,
        side=params.side,
        order_type=params.order_type,
        quantity=params.quantity,
        price=params.price,
    )

    return OrderResult(raw)