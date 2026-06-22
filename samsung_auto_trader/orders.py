"""
Orders module for the Samsung Auto Trader.
Handles order placement and order status tracking.
"""

import logging
from typing import Optional, Dict, Any
from enum import Enum

from api_client import APIClient
from config import Config
from utils import format_price


logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Order type enumeration."""
    BUY = Config.BUY
    SELL = Config.SELL


class OrderResult:
    """Container for order placement result."""
    
    def __init__(self, success: bool, order_id: Optional[str] = None, message: str = ""):
        self.success = success
        self.order_id = order_id
        self.message = message
    
    def __str__(self) -> str:
        status = "✓ Success" if self.success else "✗ Failed"
        order_info = f" (Order ID: {self.order_id})" if self.order_id else ""
        return f"{status}{order_info}: {self.message}"


class Orders:
    """Manages order placement and tracking."""
    
    def __init__(self, client: APIClient, authenticator, account_id: str):
        """
        Initialize orders module.
        
        Args:
            client: APIClient instance
            authenticator: KISAuthenticator instance
            account_id: Account ID for trading
        """
        self.client = client
        self.authenticator = authenticator
        self.account_id = account_id
    
    def place_order(
        self,
        stock_code: str,
        order_type: OrderType,
        price: int,
        quantity: int = Config.ORDER_QUANTITY
    ) -> OrderResult:
        """
        Place a buy or sell order.
        
        Args:
            stock_code: Stock code (e.g., "005930")
            order_type: OrderType.BUY or OrderType.SELL
            price: Order price in KRW
            quantity: Number of shares
        
        Returns:
            OrderResult with success status and order ID
        """
        order_name = "BUY" if order_type == OrderType.BUY else "SELL"
        logger.info(
            f"Placing {order_name} order: {quantity} shares of {stock_code} @ {format_price(price)}"
        )
        
        headers = self.authenticator.get_headers()
        
        # Prepare order payload
        # Note: Field names and structure are placeholders
        # Adjust based on actual KIS API documentation
        payload = {
            "CANO": self.account_id.split("-")[0],
            "ACNT_PRDT_CD": self.account_id.split("-")[1] if "-" in self.account_id else "01",
            "PDNO": stock_code,
            "ORD_DVSN": "00",  # Order division (00=limit order)
            "ORD_QTY": quantity,
            "ORD_UNPR": price,
            "SLL_TYPE": order_type.value,  # BUY=01, SELL=02
        }
        
        try:
            response = self.client.post(
                Config.ORDER_BUY_ENDPOINT,  # Or ORDER_SELL_ENDPOINT depending on order_type
                headers=headers,
                json=payload
            )
            
            data = response.json()
            
            # Check for API errors
            error = self.client.check_api_error(response)
            if error:
                logger.error(f"Order placement failed: {error}")
                return OrderResult(False, message=str(error))
            
            # Extract order ID from response
            # Note: Field name may vary; adjust if needed
            order_id = data.get("output", {}).get("odno")
            
            if order_id:
                logger.info(f"{order_name} order placed successfully. Order ID: {order_id}")
                return OrderResult(True, order_id=order_id, message=f"{order_name} order placed")
            else:
                logger.warning(f"Order placed but no order ID in response: {data}")
                return OrderResult(
                    True,  # Optimistic: assume order succeeded
                    message=f"{order_name} order submitted (no order ID received)"
                )
        
        except Exception as e:
            logger.error(f"Exception while placing {order_name} order: {e}")
            return OrderResult(False, message=f"Exception: {str(e)}")
    
    def place_buy_order(self, stock_code: str, price: int, quantity: int = Config.ORDER_QUANTITY) -> OrderResult:
        """
        Place a buy order.
        
        Args:
            stock_code: Stock code
            price: Buy price in KRW
            quantity: Number of shares
        
        Returns:
            OrderResult
        """
        return self.place_order(stock_code, OrderType.BUY, price, quantity)
    
    def place_sell_order(self, stock_code: str, price: int, quantity: int = Config.ORDER_QUANTITY) -> OrderResult:
        """
        Place a sell order.
        
        Args:
            stock_code: Stock code
            price: Sell price in KRW
            quantity: Number of shares
        
        Returns:
            OrderResult
        """
        return self.place_order(stock_code, OrderType.SELL, price, quantity)


# ── 모듈 레벨 함수 (trader.py 호환) ──────────────────────────────────────────
import config as _cfg
import auth as _auth
import requests as _requests


def buy(stock_code: str, price: int, qty: int) -> None:
    """매수 주문 — trader.py에서 직접 호출하는 모듈 레벨 함수."""
    _place_order(stock_code, price, qty, _cfg.TR_BUY, "매수")


def sell(stock_code: str, price: int, qty: int) -> None:
    """매도 주문 — trader.py에서 직접 호출하는 모듈 레벨 함수."""
    _place_order(stock_code, price, qty, _cfg.TR_SELL, "매도")


def _place_order(stock_code: str, price: int, qty: int, tr_id: str, label: str) -> None:
    url = f"{_cfg.BASE_URL}{_cfg.ORDER_ENDPOINT}"
    headers = _auth.make_headers(tr_id)
    ord_unpr = "0" if _cfg.ORDER_DIVISION == "01" else str(price)  # 시장가 단가 = "0"
    payload = {
        "CANO":         _cfg.ACCOUNT_NO,
        "ACNT_PRDT_CD": _cfg.ACNT_PRDT_CD,
        "PDNO":         stock_code,
        "ORD_DVSN":     _cfg.ORDER_DIVISION,
        "ORD_QTY":      str(qty),
        "ORD_UNPR":     ord_unpr,
    }
    try:
        resp = _requests.post(url, headers=headers, json=payload,
                              timeout=_cfg.REQUEST_TIMEOUT_SECONDS)
        data = resp.json()
        if data.get("rt_cd") != "0":
            logger.error(f"{label} 주문 오류: {data.get('msg1', data)}")
            return
        order_no = (data.get("output") or {}).get("odno", "?")
        logger.info(f"{label} 주문: [{stock_code}] {qty}주 @ {price:,} KRW")
        logger.info(f"{label} 주문 완료 (주문번호: {order_no})")
    except Exception as exc:
        logger.error(f"{label} 주문 예외: {exc}")


if __name__ == "__main__":
    # orders.py 단독 실행 시 실제 주문이 발생합니다.
    # 반드시 모의투자(KIS_ENV=demo) 환경에서만 테스트하세요.
    from logger import setup_logger
    import config as _c
    setup_logger(__name__, level="DEBUG")
    print(f"현재 환경: {'모의투자' if _c.ENV_DV == 'demo' else '실전투자'}")
    print("orders.py 직접 실행은 주문을 발생시킵니다.")
    print("테스트하려면 main.py를 사용하거나 거래 시간 외에 실행하세요.")
