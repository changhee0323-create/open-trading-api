# Quick Start Guide

## 1. Setup (5 minutes)

### Step 1: Navigate to the project folder

```bash
cd /workspaces/open-trading-api/samsung_auto_trader
```

### Step 2: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Create `.env` file with your credentials

```bash
cp .env.example .env
```

Edit `.env`:

```env
GH_ACCOUNT=your_kis_account_id
GH_APPKEY=your_kis_app_key
GH_APPSECRET=your_kis_app_secret
```

## 2. Verify Setup

Test that your credentials are loaded:

```bash
python config.py
```

Should output: `✓ All credentials loaded`

Test the logger:

```bash
python logger.py
```

Should output log messages with timestamps.

## 3. Run the Trader

```bash
python main.py
```

You should see:

```
2024-03-25 09:15:30 | INFO     | samsung_auto_trader | Starting Samsung Auto Trader...
2024-03-25 09:15:30 | INFO     | samsung_auto_trader | ✓ Credentials validated
2024-03-25 09:15:31 | INFO     | samsung_auto_trader | Initializing Samsung Auto Trader...
2024-03-25 09:15:31 | INFO     | samsung_auto_trader | ✓ Trader initialized successfully
2024-03-25 09:15:31 | INFO     | samsung_auto_trader | SAMSUNG AUTO TRADER STARTED
...
```

## 4. Key Files to Understand

| File | Purpose |
|------|---------|
| `main.py` | Start the system here |
| `config.py` | Adjust trading parameters (offsets, timing, API limits) |
| `trader.py` | See the main trading loop and decision logic |
| `auth.py` | Token management - explains how tokens are cached |
| `README.md` | Full documentation |

## 5. Troubleshooting

### Error: "Missing required environment variables"

→ Make sure `.env` file exists with credentials

### Error: "Token request failed"

→ Check that GH_APPKEY and GH_APPSECRET are correct

### Trader starts but doesn't place orders

→ Check if it's within trading window (09:10 AM - 03:30 PM)
→ Check API endpoint paths in `config.py` (these are placeholders)

## 6. What to Monitor

Check the logs while trader is running:

```bash
tail -f auto_trader.log
```

Look for:
- ✓ Token reuse messages (shows token caching works)
- ✓ Current price queries
- ✓ Account balance queries
- ✓ Order placement attempts
- ✗ Any API errors

## 7. Adjusting Parameters

Edit `config.py` to change:

- **Trading hours**: `TRADING_START_HOUR`, `TRADING_START_MINUTE`, etc.
- **Order offsets**: `BUY_OFFSET_KRW`, `SELL_OFFSET_KRW`
- **Order size**: `ORDER_QUANTITY`
- **Polling interval**: `POLLING_INTERVAL_SECONDS`
- **API limits**: `MAX_RETRIES`, `REQUEST_TIMEOUT_SECONDS`

## 8. Important Notes

⚠️ **API Endpoint Paths**: The endpoint paths in `config.py` are **placeholders**:
- `PRICE_ENDPOINT`
- `ACCOUNT_BALANCE_ENDPOINT`
- `ORDER_BUY_ENDPOINT`
- `ORDER_SELL_ENDPOINT`

These need to be verified against the actual KIS API documentation and adjusted if different.

⚠️ **Response Fields**: The field names extracted from API responses (e.g., `stck_prpr` for price) are also placeholders and should be verified against actual API responses.

See `API_ENDPOINTS_AND_FIELDS.md` for details.

## 9. Next Steps

- Review the full `README.md` for comprehensive documentation
- Check `API_ENDPOINTS_AND_FIELDS.md` for API integration notes
- Run tests to verify each module independently
- Monitor logs during first few trading cycles

---

**Now run:**

```bash
python main.py
```

Let me know if you hit any issues! 🚀
