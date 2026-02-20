"""
Binance Futures Testnet API client.

Uses direct REST calls (requests) to avoid library version conflicts.
Base URL: https://testnet.binancefuture.com
"""

import hashlib
import hmac
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests

from .logging_config import get_logger

logger = get_logger(__name__)

BASE_URL = "https://testnet.binancefuture.com"
RECV_WINDOW = 5000  # milliseconds


class BinanceAPIError(Exception):
    """Raised when the Binance API returns an error response."""

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"Binance API error {code}: {message}")


class BinanceClient:
    """Thin wrapper around the Binance Futures Testnet REST API."""

    def __init__(self, api_key: str, api_secret: str) -> None:
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = requests.Session()
        self.session.headers.update(
            {
                "X-MBX-APIKEY": self.api_key,
                "Content-Type": "application/json",
            }
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _sign(self, params: Dict[str, Any]) -> str:
        """Return HMAC-SHA256 signature for the given parameter dict."""
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return signature

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Signed GET request."""
        params = params or {}
        params["timestamp"] = int(time.time() * 1000)
        params["recvWindow"] = RECV_WINDOW
        params["signature"] = self._sign(params)

        url = f"{BASE_URL}{path}"
        logger.debug("GET %s | params=%s", url, {k: v for k, v in params.items() if k != "signature"})

        try:
            response = self.session.get(url, params=params, timeout=10)
        except requests.RequestException as exc:
            logger.error("Network error on GET %s: %s", url, exc)
            raise

        return self._handle_response(response)

    def _post(self, path: str, params: Dict[str, Any]) -> Any:
        """Signed POST request (params sent as query string per Binance spec)."""
        params["timestamp"] = int(time.time() * 1000)
        params["recvWindow"] = RECV_WINDOW
        params["signature"] = self._sign(params)

        url = f"{BASE_URL}{path}"
        logger.debug(
            "POST %s | params=%s",
            url,
            {k: v for k, v in params.items() if k != "signature"},
        )

        try:
            response = self.session.post(url, params=params, timeout=10)
        except requests.RequestException as exc:
            logger.error("Network error on POST %s: %s", url, exc)
            raise

        return self._handle_response(response)

    def _handle_response(self, response: requests.Response) -> Any:
        """Parse JSON and raise BinanceAPIError on non-2xx or error body."""
        logger.debug("HTTP %s | body=%s", response.status_code, response.text[:500])
        try:
            data = response.json()
        except ValueError:
            response.raise_for_status()
            return response.text

        if isinstance(data, dict) and "code" in data and data["code"] != 200:
            code = data.get("code", -1)
            msg = data.get("msg", "Unknown error")
            logger.error("Binance API error %s: %s", code, msg)
            raise BinanceAPIError(code, msg)

        response.raise_for_status()
        logger.debug("Response OK: %s", str(data)[:300])
        return data

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    def get_account_info(self) -> Dict[str, Any]:
        """Fetch futures account information (connectivity / auth check)."""
        return self._get("/fapi/v2/account")

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        time_in_force: str = "GTC",
        reduce_only: bool = False,
    ) -> Dict[str, Any]:
        """
        Place a new order on Binance Futures Testnet.

        Args:
            symbol:        Trading pair, e.g. 'BTCUSDT'.
            side:          'BUY' or 'SELL'.
            order_type:    'MARKET' or 'LIMIT'.
            quantity:      Order quantity.
            price:         Required for LIMIT orders.
            time_in_force: e.g. 'GTC' (Good Till Cancelled). Used for LIMIT orders.
            reduce_only:   Whether the order should only reduce an existing position.

        Returns:
            Parsed JSON response from Binance.
        """
        params: Dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
        }

        if order_type == "LIMIT":
            params["price"] = price
            params["timeInForce"] = time_in_force

        if reduce_only:
            params["reduceOnly"] = "true"

        logger.info(
            "Placing %s %s order | symbol=%s qty=%s price=%s",
            side,
            order_type,
            symbol,
            quantity,
            price,
        )
        result = self._post("/fapi/v1/order", params)
        logger.info("Order placed successfully | orderId=%s status=%s", result.get("orderId"), result.get("status"))
        return result