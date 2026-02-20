# Binance Futures Testnet Trading Bot 🤖

A clean, modular Python CLI application for placing **MARKET** and **LIMIT** orders on the [Binance Futures Testnet (USDT-M)](https://testnet.binancefuture.com).

> ⚠️ **Disclaimer:** This project is for educational purposes only. It connects to the Binance **Testnet** environment and does not involve real funds. This is not financial advice.

---

## Features

- ✅ Place **MARKET** and **LIMIT** orders
- ✅ Support for **BUY** and **SELL** sides
- ✅ Input validation with clear error messages
- ✅ Structured CLI with `argparse`
- ✅ Credentials loaded from `.env` file
- ✅ Rotating log file (`logs/trading_bot.log`)
- ✅ Clean separation of concerns (client / orders / validators / CLI)
- ✅ Full exception handling for API errors, network failures, and bad input

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py          # Package exports
│   ├── client.py            # Binance REST API client (signing, requests)
│   ├── logging_config.py    # Rotating file + console logging setup
│   ├── orders.py            # Order placement logic & result formatting
│   └── validators.py        # Input validation
├── cli.py                   # CLI entry point (argparse)
├── .env                     # Your API credentials (never commit this)
├── .env.example             # Template for credentials
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/trading_bot.git
cd trading_bot
```

### 2. Create a Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Get Binance Testnet API Credentials

1. Go to [testnet.binancefuture.com](https://testnet.binancefuture.com)
2. Log in with your GitHub account
3. Click your profile (top right) → **API Key** → **Create**
4. Copy both the **API Key** and **Secret Key** — the secret is only shown once

### 5. Configure Credentials

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Then edit `.env` with your credentials:

```
BINANCE_API_KEY=your_testnet_api_key_here
BINANCE_API_SECRET=your_testnet_api_secret_here
```

> 🔒 The `.env` file is listed in `.gitignore` and will never be committed to Git.

---

## Usage

### Command Syntax

```
python cli.py --symbol SYMBOL --side SIDE --type TYPE --qty QUANTITY [--price PRICE]
```

### Arguments

| Argument | Alias | Required | Description |
|---|---|---|---|
| `--symbol` | `-s` | ✅ | Trading pair, e.g. `BTCUSDT`, `ETHUSDT` |
| `--side` | | ✅ | `BUY` or `SELL` |
| `--type` | `-t` | ✅ | `MARKET` or `LIMIT` |
| `--qty` | `-q` | ✅ | Order quantity (must be a positive number) |
| `--price` | `-p` | LIMIT only | Limit price (required for LIMIT orders) |
| `--api-key` | | ❌ | Overrides `BINANCE_API_KEY` env var |
| `--api-secret` | | ❌ | Overrides `BINANCE_API_SECRET` env var |

---

## Examples

### Market Orders

```bash
# Market BUY 0.002 BTC
python cli.py --symbol BTCUSDT --side BUY --type MARKET --qty 0.002

# Market SELL 0.04 ETH
python cli.py --symbol ETHUSDT --side SELL --type MARKET --qty 0.04
```

### Limit Orders

```bash
# Limit BUY 0.002 BTC at $65,000 (below market — sits open)
python cli.py --symbol BTCUSDT --side BUY --type LIMIT --qty 0.002 --price 65000

# Limit SELL 0.04 ETH at $3,500
python cli.py --symbol ETHUSDT --side SELL --type LIMIT --qty 0.04 --price 3500
```

### Short Aliases

```bash
python cli.py -s BTCUSDT --side BUY -t MARKET -q 0.002
```

---

## Sample Output

```
──────────────────────────────────────────────────
  ORDER REQUEST SUMMARY
──────────────────────────────────────────────────
  Symbol     : BTCUSDT
  Side       : BUY
  Type       : MARKET
  Quantity   : 0.002
──────────────────────────────────────────────────
──────────────────────────────────────────────────
  ORDER RESPONSE
──────────────────────────────────────────────────
  Order ID       : 12417434823
  Status         : NEW
  Symbol         : BTCUSDT
  Side           : BUY
  Type           : MARKET
  Orig Qty       : 0.002
  Executed Qty   : 0.000
  Avg Price      : 0.00
  Time In Force  : GTC
──────────────────────────────────────────────────
✅  Order placed successfully!
```

---

## Validation & Error Handling

The bot validates all inputs before sending anything to Binance:

| Scenario | Example | Exit Code |
|---|---|---|
| Missing required argument | No `--symbol` | `2` |
| Invalid side | `--side LONG` | `2` |
| Invalid order type | `--type STOP` | `2` |
| Negative quantity | `--qty -1` | `2` |
| Missing price for LIMIT | `--type LIMIT` without `--price` | `2` |
| Binance API rejection | Order too small, price out of range | `3` |
| Network failure | No internet connection | `4` |
| Missing credentials | No `.env` / env vars set | `1` |

### Common Binance Errors

| Error Code | Meaning | Fix |
|---|---|---|
| `-4164` | Order notional < $100 | Increase quantity so `qty × price ≥ $100` |
| `-4016` | Limit price out of allowed range | Stay within ~5–10% of current market price |
| `-1121` | Invalid symbol | Check spelling, e.g. `BTCUSDT` not `BTC-USDT` |

---

## Logging

All activity is written to `logs/trading_bot.log` (created automatically on first run):

```
2026-02-20 19:18:51 | INFO     | bot.orders  | Submitting order | BUY MARKET BTCUSDT qty=0.002 price=None
2026-02-20 19:18:51 | DEBUG    | bot.client  | POST https://testnet.binancefuture.com/fapi/v1/order
2026-02-20 19:18:52 | INFO     | bot.client  | Order placed successfully | orderId=12417434823 status=NEW
```

- Log files rotate at **10 MB**, keeping the last **5 files**
- `DEBUG` and above → log file
- `WARNING` and above → console

---

## Requirements

```
requests>=2.31.0
python-dotenv>=1.0.0
```

Python **3.9+** required.

---

## Assumptions

- **Testnet only** — base URL is hard-coded to `https://testnet.binancefuture.com`
- **USDT-M perpetual futures** — uses the `/fapi/v1/order` endpoint
- **`timeInForce` defaults to `GTC`** (Good Till Cancelled) for LIMIT orders
- **Minimum order notional is $100** on Binance Futures Testnet
- Credentials are never logged or printed to the console

---

## License

MIT License — free to use, modify, and distribute.