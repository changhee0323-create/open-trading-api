"""
Account module for the Samsung Auto Trader.
Handles account balance and holdings queries.
"""

import logging
from typing import Optional, Dict, Any, List

from api_client import APIClient
from config import Config
from utils import format_price


logger = logging.getLogger(__name__)


class AccountInfo:
    """Container for account information."""
    
    def __init__(self, account_id: str):
        self.account_id = account_id
        self.total_balance: Optional[int] = None
        self.available_cash: Optional[int] = None
        self.holdings: Dict[str, int] = {}  # stock_code -> quantity
    
    def get_samsung_quantity(self) -> int:
        """Get quantity of Samsung shares held."""
        return self.holdings.get(Config.SAMSUNG_CODE, 0)
    
    def __str__(self) -> str:
        samsung_qty = self.get_samsung_quantity()
        balances = f"Total: {format_price(self.total_balance)}" if self.total_balance else "N/A"
        cash = f"Cash: {format_price(self.available_cash)}" if self.available_cash else "N/A"
        
        return (
            f"Account {self.account_id} | {balances} | {cash} | "
            f"Samsung holdings: {samsung_qty} shares"
        )


class Account:
    """Manages account information and balance checks."""
    
    def __init__(self, client: APIClient, authenticator, account_id: str):
        """
        Initialize account module.
        
        Args:
            client: APIClient instance
            authenticator: KISAuthenticator instance
            account_id: Account ID for trading
        """
        self.client = client
        self.authenticator = authenticator
        self.account_id = account_id
    
    def get_account_info(self) -> Optional[AccountInfo]:
        """
        Fetch current account information including balance and holdings.
        
        Returns:
            AccountInfo object, or None if fetch fails
        """
        logger.info(f"Fetching account info for {self.account_id}...")
        
        headers = self.authenticator.get_headers()
        
        # Note: This endpoint path and parameters may need adjustment
        # based on the actual KIS API documentation
        params = {
            "CANO": self.account_id.split("-")[0],  # Account number
            "ACNT_PRDT_CD": self.account_id.split("-")[1] if "-" in self.account_id else "01"  # Product code
        }
        
        try:
            response = self.client.get(
                Config.ACCOUNT_BALANCE_ENDPOINT,
                headers=headers,
                params=params
            )
            
            data = response.json()
            
            # Check for API errors
            error = self.client.check_api_error(response)
            if error:
                logger.error(f"Failed to fetch account info: {error}")
                return None
            
            account_info = AccountInfo(self.account_id)
            
            # Extract balance information
            # Note: Field names are placeholders; adjust based on actual API response
            output = data.get("output", {})
            if isinstance(output, dict):
                account_info.total_balance = int(output.get("tot_evlu_amt", 0))
                account_info.available_cash = int(output.get("nxdy_excc_amt", 0))
            
            # Extract holdings from output2 (array of positions)
            output2 = data.get("output2", [])
            if isinstance(output2, list):
                for position in output2:
                    stock_code = position.get("pdno")  # Product code
                    quantity = int(position.get("qty", 0))
                    if stock_code and quantity > 0:
                        account_info.holdings[stock_code] = quantity
            
            logger.info(f"Account info retrieved: {account_info}")
            return account_info
        
        except Exception as e:
            logger.error(f"Exception while fetching account info: {e}")
            return None
    
    def get_samsung_holdings(self) -> int:
        """
        Get quantity of Samsung shares currently held.
        
        Returns:
            Quantity of Samsung shares, or 0 if unable to fetch
        """
        account_info = self.get_account_info()
        if account_info:
            return account_info.get_samsung_quantity()
        return 0
    
    def get_available_cash(self) -> Optional[int]:
        """
        Get available cash for trading.
        
        Returns:
            Available cash in KRW, or None if unable to fetch
        """
        account_info = self.get_account_info()
        if account_info:
            return account_info.available_cash
        return None


# ── 모듈 레벨 함수 (trader.py 호환) ──────────────────────────────────────────
import config as _cfg
import auth as _auth
import requests as _requests
from typing import Tuple


def get_balance() -> Tuple[Optional[int], dict]:
    """예수금·보유종목 조회 — trader.py에서 직접 호출하는 모듈 레벨 함수.

    Returns:
        (예수금 int, 보유종목 dict[종목코드 → 수량])
        조회 실패 시 (None, {})
    """
    url = f"{_cfg.BASE_URL}{_cfg.BALANCE_ENDPOINT}"
    headers = _auth.make_headers(_cfg.TR_BALANCE)
    params = {
        "CANO":                _cfg.ACCOUNT_NO,
        "ACNT_PRDT_CD":        _cfg.ACNT_PRDT_CD,
        "AFHR_FLPR_YN":        "N",
        "OFL_YN":              "",
        "INQR_DVSN":           "02",
        "UNPR_DVSN":           "01",
        "FUND_STTL_ICLD_YN":   "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN":           "01",
        "CTX_AREA_FK100":      "",
        "CTX_AREA_NK100":      "",
    }
    try:
        resp = _requests.get(url, headers=headers, params=params,
                             timeout=_cfg.REQUEST_TIMEOUT_SECONDS)
        data = resp.json()
        if data.get("rt_cd") != "0":
            logger.error(f"계좌 조회 오류: {data.get('msg1', data)}")
            return None, {}

        # prvs_rcdl_excc_amt(가수도정산금액): 당일 체결분이 즉시 반영된 실제 주문 가능 금액.
        # dnca_tot_amt(예수금총액)는 T+2 정산 전 금액이라 당일 매수/매도가 반영되지 않음.
        cash_raw = (data.get("output2") or [{}])[0].get("prvs_rcdl_excc_amt", "0")
        cash = int(cash_raw)

        holdings: dict = {}
        for item in data.get("output1") or []:
            code = item.get("pdno")
            qty  = int(item.get("hldg_qty", 0))
            if code and qty > 0:
                holdings[code] = qty

        logger.info(f"예수금: {cash:,} KRW | 보유종목: {holdings}")
        return cash, holdings
    except Exception as exc:
        logger.error(f"계좌 조회 예외: {exc}")
        return None, {}


if __name__ == "__main__":
    from logger import setup_logger
    setup_logger(__name__, level="DEBUG")
    cash, holdings = get_balance()
    if cash is not None:
        print(f"✓ 예수금: {cash:,} KRW | 보유종목: {holdings}")
    else:
        print("✗ Failed to fetch account info")
