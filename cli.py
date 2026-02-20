#!/usr/bin/env python3
"""
CLI entry point for the Binance Futures Testnet trading bot.

Usage examples:
    # Market BUY
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --qty 0.001

    # Limit SELL
    python cli.py --symbol ETHUSDT --side SELL --type LIMIT --qty 0.01 --price 3500

    # Using environment variables for credentials (recommended)
    export BINANCE_API_KEY="your_testnet_api_key"
    export BINANCE_API_SECRET="your_testnet_api_secret"
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --qty 0.001
"""

import argparse
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

from bot.logging_config import setup_logging, get_logger
from bot.client import BinanceClient, BinanceAPIError
from bot.orders import place_order
from bot.validators import ValidationError

# Initialise logging before anything else
setup_logging()
logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _print_separator(char: str = "─", width: int = 50) -> None:
    print(char * width)


def _print_order_summary(symbol: str, side: str, order_type: str, qty: float, price) -> None:
    _print_separator()
    print("  ORDER REQUEST SUMMARY")
    _print_separator()
    print(f"  Symbol     : {symbol.upper()}")
    print(f"  Side       : {side.upper()}")
    print(f"  Type       : {order_type.upper()}")
    print(f"  Quantity   : {qty}")
    if price is not None:
        print(f"  Price      : {price}")
    _print_separator()


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Place MARKET / LIMIT orders on Binance Futures Testnet (USDT-M).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Place a MARKET BUY order for 0.001 BTC
  python cli.py --symbol BTCUSDT --side BUY --type MARKET --qty 0.001

  # Place a LIMIT SELL order for 0.01 ETH at $3,500
  python cli.py --symbol ETHUSDT --side SELL --type LIMIT --qty 0.01 --price 3500

Credentials are read from environment variables:
  BINANCE_API_KEY     Your Binance Futures Testnet API key
  BINANCE_API_SECRET  Your Binance Futures Testnet API secret

Alternatively pass them via --api-key / --api-secret flags (less secure).
        """,
    )

    # Order parameters
    parser.add_argument(
        "--symbol", "-s",
        required=True,
        metavar="SYMBOL",
        help="Trading pair symbol, e.g. BTCUSDT",
    )
    parser.add_argument(
        "--side",
        required=True,
        choices=["BUY", "SELL"],
        metavar="SIDE",
        help="Order side: BUY or SELL",
    )
    parser.add_argument(
        "--type", "-t",
        dest="order_type",
        required=True,
        choices=["MARKET", "LIMIT"],
        metavar="TYPE",
        help="Order type: MARKET or LIMIT",
    )
    parser.add_argument(
        "--qty", "-q",
        dest="quantity",
        required=True,
        type=float,
        metavar="QUANTITY",
        help="Order quantity (must be positive)",
    )
    parser.add_argument(
        "--price", "-p",
        type=float,
        default=None,
        metavar="PRICE",
        help="Limit price (required for LIMIT orders)",
    )

    # Credentials (env vars preferred)
    parser.add_argument(
        "--api-key",
        default=None,
        metavar="KEY",
        help="Binance API key (overrides BINANCE_API_KEY env var)",
    )
    parser.add_argument(
        "--api-secret",
        default=None,
        metavar="SECRET",
        help="Binance API secret (overrides BINANCE_API_SECRET env var)",
    )

    return parser


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    """Entry point. Returns exit code (0 = success, non-zero = failure)."""
    parser = build_parser()
    args = parser.parse_args()

    # Resolve credentials
    api_key = args.api_key or os.environ.get("BINANCE_API_KEY", "")
    api_secret = args.api_secret or os.environ.get("BINANCE_API_SECRET", "")

    if not api_key or not api_secret:
        print(
            "ERROR: Binance API credentials are required.\n"
            "Set BINANCE_API_KEY and BINANCE_API_SECRET environment variables,\n"
            "or pass --api-key / --api-secret flags.",
            file=sys.stderr,
        )
        logger.error("Missing API credentials.")
        return 1

    # Print request summary
    _print_order_summary(
        symbol=args.symbol,
        side=args.side,
        order_type=args.order_type,
        qty=args.quantity,
        price=args.price,
    )

    # Build client
    client = BinanceClient(api_key=api_key, api_secret=api_secret)

    try:
        result = place_order(
            client=client,
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
        )
    except ValidationError as exc:
        print(f"\n❌  Validation error: {exc}", file=sys.stderr)
        logger.error("Validation error: %s", exc)
        return 2
    except BinanceAPIError as exc:
        print(f"\n❌  Binance API error [{exc.code}]: {exc.message}", file=sys.stderr)
        logger.error("Binance API error: code=%s msg=%s", exc.code, exc.message)
        return 3
    except requests.ConnectionError as exc:
        print(f"\n❌  Network error — could not connect to Binance: {exc}", file=sys.stderr)
        logger.error("Network connection error: %s", exc)
        return 4
    except requests.Timeout:
        print("\n❌  Network error — request timed out.", file=sys.stderr)
        logger.error("Request timed out.")
        return 4
    except requests.RequestException as exc:
        print(f"\n❌  Network error: {exc}", file=sys.stderr)
        logger.error("Request exception: %s", exc)
        return 4
    except Exception as exc:  # noqa: BLE001
        print(f"\n❌  Unexpected error: {exc}", file=sys.stderr)
        logger.exception("Unexpected error: %s", exc)
        return 5

    # Print result
    print(result)
    print("✅  Order placed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())