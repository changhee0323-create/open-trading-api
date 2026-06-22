# API Endpoints and Fields Reference

This document lists all API endpoint paths and response field names used in the code. These are **placeholders** and may need adjustment based on the actual KIS Open API documentation.

## Overview

The current implementation uses placeholder values for:
1. **Endpoint paths** (e.g., `/uapi/domestic-stock/v1/quotations/inquire-price`)
2. **Response field names** (e.g., `stck_prpr` for price)

You must verify these against the official KIS API documentation before running in production.

---

## 1. Authentication Endpoint

**File**: `auth.py`

### Token Request
```python
Config.TOKEN_ENDPOINT = "/oauth2/tokenP"  # Mock trading endpoint
```

**Placeholder**: The `/oauth2/tokenP` path is for mock trading. Verify this in KIS docs.

---

## 2. Market Data Endpoints

**File**: `market_data.py`, `config.py`

### Get Current Stock Price
```python
Config.PRICE_ENDPOINT = "/uapi/domestic-stock/v1/quotations/inquire-price"
```

**Request Parameters**:
```python
params = {
    "fid_cond_mrkt_div_code": "J",  # Domestic market code
    "fid_input_iscd": "005930"       # Samsung stock code
}
```

**Response Field Extraction** (Line in `market_data.py`):
```python
price = data.get("output", {}).get("stck_prpr")  # ← PLACEHOLDER!
```

**Status**: 
- ✓ Endpoint path: Likely correct for KIS API
- ⚠️ Field name `stck_prpr`: Verify in actual API response
  - Alternative names to check: `stck_oprc`, `stck_clpr`, `prdy_clpr`

---

## 3. Account Endpoints

**File**: `account.py`, `config.py`

### Get Account Balance and Holdings
```python
Config.ACCOUNT_BALANCE_ENDPOINT = "/uapi/domestic-stock/v1/trading/inquire-psbl-order"
```

**Request Parameters**:
```python
params = {
    "CANO": "12345678",        # Account number part
    "ACNT_PRDT_CD": "01"       # Account product code (01 = general stock)
}
```

**Response Field Extraction** (in `account.py`):
```python
# Total balance
account_info.total_balance = int(output.get("tot_evlu_amt", 0))  # ← PLACEHOLDER

# Available cash
account_info.available_cash = int(output.get("nxdy_excc_amt", 0))  # ← PLACEHOLDER

# Holdings (from output2 array)
for position in output2:
    stock_code = position.get("pdno")      # ← PLACEHOLDER
    quantity = int(position.get("qty", 0)) # ← PLACEHOLDER
```

**Status**:
- ⚠️ Endpoint path: Verify this is the correct endpoint for balance+holdings
- ⚠️ Field names: All are placeholders - check actual response
  - `tot_evlu_amt`: Total evaluation amount (or similar)
  - `nxdy_excc_amt`: Next day executable amount (or similar)
  - `pdno`: Product number/code (or `stck_code`, etc.)
  - `qty`: Quantity (or `hldg_qty`, `sln_qty`, etc.)

---

## 4. Order Endpoints

**File**: `orders.py`, `config.py`

### Place Buy Order
```python
Config.ORDER_BUY_ENDPOINT = "/uapi/domestic-stock/v1/trading/order-cash"
```

**Request Payload**:
```python
payload = {
    "CANO": "12345678",         # Account number
    "ACNT_PRDT_CD": "01",       # Account product code
    "PDNO": "005930",           # Stock code
    "ORD_DVSN": "00",           # Order division (00=limit order) ← PLACEHOLDER
    "ORD_QTY": 1,               # Order quantity
    "ORD_UNPR": 70000,          # Order unit price
    "SLL_TYPE": "01"            # Buy=01, Sell=02 ← CONFIRM
}
```

**Response Field Extraction**:
```python
order_id = data.get("output", {}).get("odno")  # ← PLACEHOLDER
```

**Status**:
- ⚠️ Endpoint path: Verify this is used for both BUY and SELL orders
- ⚠️ Payload field names: Check exact parameter names in API
  - `ORD_DVSN`: Order division code (00=limit? Check alternatives)
  - `SLL_TYPE`: Buy/Sell type (01/02? Or other values?)
- ⚠️ Response field: `odno` may not be correct field name

---

## 5. How to Verify and Fix

### Step 1: Get KIS API Documentation

1. Visit [KIS Open API](https://www.kis.com/openapi)
2. Download/access the API documentation
3. Look for endpoints for:
   - Authentication (OAuth2)
   - Stock price quotes
   - Account inquiry
   - Order placement

### Step 2: Check Response Format

Test each endpoint and log the actual response:

```python
# Example: Add this to market_data.py to see full response
logger.info(f"Full API response: {response.json()}")
```

Then check `auto_trader.log` to see the actual response structure.

### Step 3: Update Placeholder Values

Once you know the correct values, update:

1. **Endpoint paths** in `config.py`
2. **Field names** in each module:
   - `market_data.py` - price field name
   - `account.py` - balance and holdings field names
   - `orders.py` - order ID field name

### Step 4: Test Each Module

```bash
# Test authentication
python auth.py

# Test market data
python market_data.py

# Test account
python account.py

# Test orders
python orders.py
```

If a module fails, check the log output and adjust the field names.

---

## 6. Field Name Mapping Guide

### Price Response
Look for fields containing:
- Current price: `stck_prpr`, `current_price`, `last_price`, `clos_price`
- Open price: `stck_oprc`, `open_price`
- Previous close: `prdy_clpr`, `prev_close`

### Account Response
Look for fields containing:
- Total balance: `tot_evlu_amt`, `total_balance`, `tot_balance`
- Available cash: `nxdy_excc_amt`, `cashable_amt`, `available_amount`
- Holdings (array): `output2`, `position_list`, `holdings`
- Stock code: `pdno`, `stck_code`, `stock_code`, `symbol`
- Quantity: `qty`, `hldg_qty`, `sln_qty`, `quantity`

### Order Response
Look for fields containing:
- Order ID: `odno`, `order_id`, `order_number`
- Status: `order_status`, `ord_status`
- Message: `msg`, `message`

---

## 7. Common API Response Format

KIS API typically returns:

```json
{
  "rt_cd": "0",           // Result code (0=success)
  "msg_cd": "...",        // Message code
  "msg1": "SUCCESS",      // Message
  "output": {             // Main data
    "field1": "value1",
    "field2": "value2"
  },
  "output2": [            // Optional array (for holdings, etc.)
    {"item1": "val1"},
    {"item2": "val2"}
  ]
}
```

Error response:
```json
{
  "rt_cd": "-1",
  "msg1": "error message"
}
```

---

## 8. Testing Checklist

Before running `main.py`:

- [ ] Test `python auth.py` - token retrieved and cached
- [ ] Test `python config.py` - credentials loaded
- [ ] Test `python market_data.py` - current price retrieved
- [ ] Test `python account.py` - account info retrieved
- [ ] Test `python logger.py` - logging works
- [ ] Verify `auto_trader.log` shows detailed output
- [ ] Check endpoint paths against KIS docs
- [ ] Verify all field names in API responses match code

---

## 9. Debugging Tips

### See Full API Response:

Add to any module:
```python
logger.info(f"Raw response: {response.text}")
```

### Check Status Code:

```python
logger.info(f"Status: {response.status_code}")
if response.status_code != 200:
    logger.error(f"HTTP Error: {response.status_code}")
```

### Validate JSON:

```python
try:
    data = response.json()
except json.JSONDecodeError as e:
    logger.error(f"Invalid JSON: {e}")
```

---

## 10. Known Placeholders Summary

| Item | Current Value | Status | Notes |
|------|---|---|---|
| Token endpoint | `/oauth2/tokenP` | Placeholder | Mock trading path - verify |
| Price endpoint | `/uapi/domestic-stock/v1/quotations/inquire-price` | Likely OK | Field names need verification |
| Account endpoint | `/uapi/domestic-stock/v1/trading/inquire-psbl-order` | Placeholder | May not be correct path |
| Price field | `stck_prpr` | Placeholder | Verify in API response |
| Balance field | `tot_evlu_amt` | Placeholder | Verify in API response |
| Cash field | `nxdy_excc_amt` | Placeholder | Verify in API response |
| Stock code in holdings | `pdno` | Placeholder | Verify in API response |
| Quantity field | `qty` | Placeholder | Verify in API response |
| Order ID field | `odno` | Placeholder | Verify in API response |
| Order division code | `00` | Placeholder | Verify correct value |
| Buy/Sell code | Buy=`01`, Sell=`02` | Placeholder | Verify correct values |

---

## Next Steps

1. Get the official KIS API documentation
2. Test each endpoint manually with curl or Postman
3. Update `config.py` with actual endpoint paths
4. Update field names in each module
5. Run test scripts again to verify
6. Start with `python main.py`

**Good luck!** 🚀
