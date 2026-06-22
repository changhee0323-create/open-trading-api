"""
Market data module for the Samsung Auto Trader.
Handles fetching current prices and market information.
"""

import logging
from typing import Optional, Dict, Any

from api_client import APIClient
from config import Config
from utils import format_price


logger = logging.getLogger(__name__)


class MarketData:
    """Fetches and manages market data for trading."""
    
    def __init__(self, client: APIClient, authenticator):
        """
        Initialize market data module.
        
        Args:
            client: APIClient instance
            authenticator: KISAuthenticator instance
        """
        self.client = client
        self.authenticator = authenticator
    
    def get_current_price(self, stock_code: str) -> Optional[int]:
        """
        Fetch current price for a given stock code.
        
        Args:
            stock_code: Stock code (e.g., "005930" for Samsung)
        
        Returns:
            Current price in KRW, or None if fetch fails
        """
        logger.info(f"Fetching current price for {stock_code}...")
        
        headers = self.authenticator.get_headers()
        
        params = {
            "fid_cond_mrkt_div_code": Config.MARKET_CODE,
            "fid_input_iscd": stock_code
        }
        
        try:
            response = self.client.get(
                Config.PRICE_ENDPOINT,
                headers=headers,
                params=params
            )
            
            data = response.json()
            
            # Check for API errors
            error = self.client.check_api_error(response)
            if error:
                logger.error(f"Failed to fetch price: {error}")
                return None
            
            # Extract price from response
            # Note: The exact field name depends on KIS API response format
            # This is a common field, but may need adjustment
            price = data.get("output", {}).get("stck_prpr")
            
            if price is None:
                logger.warning(f"Price not found in response: {data}")
                return None
            
            # Convert to integer
            price = int(price)
            logger.info(f"Current price for {stock_code}: {format_price(price)}")
            
            return price
        
        except Exception as e:
            logger.error(f"Exception while fetching price: {e}")
            return None
    
    def get_samsung_price(self) -> Optional[int]:
        """
        Fetch current price for Samsung Electronics (005930).
        
        Returns:
            Current price in KRW, or None if fetch fails
        """
        return self.get_current_price(Config.SAMSUNG_CODE)


# ── 모듈 레벨 함수 (trader.py 호환) ──────────────────────────────────────────
import config as _cfg
import auth as _auth
import requests as _requests


def get_current_price(stock_code: str) -> Optional[int]:
    """현재가 조회 — trader.py에서 직접 호출하는 모듈 레벨 함수."""
    url = f"{_cfg.BASE_URL}{_cfg.PRICE_ENDPOINT}"
    headers = _auth.make_headers(_cfg.TR_PRICE)
    params = {
        "fid_cond_mrkt_div_code": _cfg.MARKET_CODE,
        "fid_input_iscd": stock_code,
    }
    try:
        resp = _requests.get(url, headers=headers, params=params,
                             timeout=_cfg.REQUEST_TIMEOUT_SECONDS)
        data = resp.json()
        if data.get("rt_cd") != "0":
            logger.error(f"시세 조회 오류: {data.get('msg1', data)}")
            return None
        price = int(data["output"]["stck_prpr"])
        logger.info(f"[{stock_code}] 현재가: {price:,} KRW")
        return price
    except Exception as exc:
        logger.error(f"시세 조회 예외: {exc}")
        return None


if __name__ == "__main__":
    from logger import setup_logger
    setup_logger(__name__, level="DEBUG")
    import config as _c
    price = get_current_price(_c.TARGET_STOCK)
    if price:
        print(f"✓ Samsung price: {price:,} KRW")
    else:
        print("✗ Failed to fetch price")
