# Samsung Auto Trader

An automated trading system for Samsung Electronics (005930) using the **Korea Investment & Securities (KIS) Open API** in mock trading mode.

## Overview

This is a **polling-based**, **REST API-only** trading system that:
- Monitors Samsung Electronics price in real-time
- Places buy orders at current price - 1,000 KRW
- Places sell orders at current price + 1,000 KRW
- Verifies execution by checking account balance changes
- Operates **only** during the Korean market trading window (09:10 AM - 03:30 PM)
- **Does NOT use WebSocket** - purely polling-based HTTP calls

## ⚠️ Important Notes

- **Mock Trading Only**: This system uses KIS mock trading environment
- **Token Caching**: The authentication token is cached and reused for the same trading day
- **Rate Limiting**: Conservative polling intervals to minimize API calls in the mock environment
- **No Live Trading**: This is explicitly designed for mock/paper trading only

## Prerequisites

- Python 3.8+
- Korea Investment Open API credentials (app key and secret)
- Trading account ID for mock trading
- Internet connection

## Installation

### 1. Clone or navigate to the project

```bash
cd samsung_auto_trader
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up environment variables

Create a `.env` file in the project root (copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` and fill in your credentials:

```env
GH_ACCOUNT=your_account_id
GH_APPKEY=your_app_key
GH_APPSECRET=your_app_secret
```

Alternatively, set these as system environment variables:

```bash
export GH_ACCOUNT=your_account_id
export GH_APPKEY=your_app_key
export GH_APPSECRET=your_app_secret
```

## Usage

### Running the trader

```bash
python main.py
```

### Running in the background (Linux/macOS)

```bash
nohup python main.py > trader.log 2>&1 &
```

### Stopping the trader

Press `Ctrl+C` to stop gracefully.

## Project Structure

```
samsung_auto_trader/
├── main.py                 # Entry point - start here
├── config.py              # Configuration & environment variables
├── logger.py              # Logging setup
├── auth.py                # Token management & caching
├── api_client.py          # Base HTTP client with retry logic
├── market_data.py         # Market price queries (Samsung)
├── account.py             # Account balance & holdings queries
├── orders.py              # Order placement logic
├── trader.py              # Main trading loop orchestration
├── utils.py               # Utility functions (time checks, etc.)
├── requirements.txt       # Python dependencies
├── .env.example           # Example environment variables (→ copy to .env)
├── README.md              # This file
└── token_cache.json       # (Auto-created) Cached authentication token
```

## Module Responsibilities

| Module | Responsibility |
|--------|---|
| `main.py` | Entry point, initializes logger and starts trader |
| `config.py` | Loads config from env vars, defines constants |
| `logger.py` | Sets up logging to console and file |
| `auth.py` | Authenticates with KIS API, caches token for same-day reuse |
| `api_client.py` | Base HTTP client with error handling & retries |
| `market_data.py` | Fetches current price for Samsung (005930) |
| `account.py` | Queries account balance and stock holdings |
| `orders.py` | Places buy/sell orders |
| `trader.py` | Main trading loop: price→balance→orders→verify |
| `utils.py` | Time window checks, sleep helpers, formatters |

## Trading Logic

The system continuously:

1. **Checks trading window** - Only trades between 09:10 AM and 03:30 PM on weekdays
2. **Gets current price** - Queries Samsung (005930) current market price
3. **Checks account before** - Queries holdings and available cash
4. **Places buy order** - Limit order at (current_price - 1,000 KRW) for 1 share
5. **Places sell order** - Limit order at (current_price + 1,000 KRW) for 1 share
6. **Checks account after** - Verifies if orders were executed by checking balance change
7. **Logs results** - Records all actions, prices, and execution status
8. **Waits** - Sleeps for configurable interval (default: 5 seconds) before next cycle

### Trading Window

- **Start**: 09:10 AM (Korean time)
- **End**: 03:30 PM (Korean time)
- **Outside this window**: Trader sleeps and checks periodically
- **Automatic stop**: After 03:30 PM, no orders are placed

## Configuration

Key settings in `config.py`:

```python
# Trading target
SAMSUNG_CODE = "005930"

# Trading window
TRADING_START_HOUR = 9
TRADING_START_MINUTE = 10
TRADING_END_HOUR = 15
TRADING_END_MINUTE = 30

# Order parameters
BUY_OFFSET_KRW = 1000    # Buy at price - 1000 KRW
SELL_OFFSET_KRW = 1000   # Sell at price + 1000 KRW
ORDER_QUANTITY = 1       # 1 share per order

# API rate limiting
POLLING_INTERVAL_SECONDS = 5  # Wait between cycles
MAX_RETRIES = 2               # Retry failed API calls
REQUEST_TIMEOUT_SECONDS = 10  # HTTP timeout

# Token caching
TOKEN_CACHE_FILE = "token_cache.json"  # Same-day reuse
```

To modify these, edit `config.py` before running.

## Logging

The trader logs all important actions to both **console** and **file**:

```
2024-03-25 09:15:30 | INFO     | samsung_auto_trader | SAMSUNG AUTO TRADER STARTED
2024-03-25 09:15:35 | INFO     | api.market_data | Current price for 005930: 70,500 KRW
2024-03-25 09:15:36 | INFO     | api.account | Account info retrieved: Account ...
2024-03-25 09:15:37 | INFO     | api.orders | BUY order placed successfully. Order ID: ...
...
```

Log file location: `auto_trader.log` (auto-rotated after 5 MB)

### What gets logged

- ✓ Token reuse / refresh
- ✓ Current price
- ✓ Holdings before/after orders
- ✓ Buy/sell order requests and results
- ✓ Account balance changes
- ✓ Execution detection
- ✓ API errors and retries
- ✓ Trading window start/end

## Troubleshooting

### "Missing required environment variables"

**Solution**: Set `GH_ACCOUNT`, `GH_APPKEY`, `GH_APPSECRET` in `.env` or as export.

### "Token request failed"

**Possible causes**:
- Invalid app key or secret
- Network connectivity issue
- KIS API is temporarily down

**Solution**: Check credentials, verify network, check KIS API status.

### "Failed to fetch current price"

**Possible causes**:
- Market is closed (outside 09:10-15:30 window)
- Invalid stock code
- Network issue

**Solution**: Check trading window, verify it's a trading day, check network.

### "No execution detected"

This is normal - limit orders may not execute immediately. The system will keep trying on subsequent cycles.

### "HTTP 429 (Too Many Requests)"

The mock trading environment has strict rate limits. If you see this:
- Increase `POLLING_INTERVAL_SECONDS` in `config.py`
- Reduce `MAX_RETRIES` or increase `API_RETRY_DELAY_SECONDS`

### Other API errors

Check `auto_trader.log` for detailed error messages and adjust API endpoint paths in `config.py` if needed.

## Development Notes

### Key Design Principles

1. **Modular**: Each concern (auth, market data, orders, etc.) is isolated
2. **Polling-based**: No WebSocket; purely HTTP REST calls
3. **Conservative**: Low API usage to respect mock trading limits
4. **Readable**: Clear logging and type hints throughout
5. **Safe**: No hardcoded credentials, proper error handling

### Token Caching

Tokens are cached in `token_cache.json` and reused for the same trading day. This reduces API calls significantly. A new token is obtained on the next trading day.

### Retry Logic

Failed API calls are retried up to `MAX_RETRIES` times with `API_RETRY_DELAY_SECONDS` between attempts.

### Rate Limiting

Between each trading cycle, the system waits `POLLING_INTERVAL_SECONDS` (default: 5s). Adjust this based on your API limits.

## Known Limitations

- **REST API only**: At the moment, the system does NOT use WebSocket; all data is polled
- **Mock trading only**: Not suitable for live trading without extensive modifications
- **Single stock**: Currently hardcoded for Samsung (005930); extend `market_data.py` for multiple stocks
- **Simple orders**: Only limit orders for 1 share; extend `orders.py` for complex order types
- **No order tracking**: System doesn't track existing pending orders; assumes orders execute quickly or are cancelled

## Future Improvements

- [ ] Support multiple stocks
- [ ] Configurable order quantities and price offsets per cycle
- [ ] Order tracking and cancellation
- [ ] WebSocket support for faster price updates (if needed)
- [ ] Database to track trades and performance
- [ ] Web dashboard for monitoring
- [ ] Backtesting framework
- [ ] Advanced trading strategies beyond simple spread trading

## Support

For issues with:
- **KIS API**: Check [KIS Open API documentation](https://www.kis.com/openapi)
- **Code**: Review logs in `auto_trader.log`
- **Credentials**: Verify setup in `.env` file

## License

This project is provided as-is for educational and mock trading purposes only.

## Disclaimer

⚠️ **This system is for mock trading only.** Do NOT use for real trading without:
1. Extensive testing and validation
2. Risk management and position sizing
3. Proper error handling for live markets
4. Full understanding of the API and trading mechanics

---

**Ready to start?**

```bash
python main.py
```

Happy trading! 📈
