"""
[설정 모듈] Samsung Auto Trader
────────────────────────────────────────────────────
역할: kis_devlp.yaml 로드, 환경변수 적용, API 상수 정의.
      모든 모듈이 이 파일의 모듈 레벨 변수를 직접 참조합니다.
"""

import os
from pathlib import Path

import yaml


# ── YAML 로드 ──────────────────────────────────────────────────────────────
def _load_yaml() -> dict:
    candidates = [
        Path(__file__).parent.parent / "kis_devlp.yaml",
        Path(__file__).parent / "kis_devlp.yaml",
    ]
    for path in candidates:
        if path.exists():
            with open(path, encoding="utf-8") as f:
                return yaml.safe_load(f)
    raise FileNotFoundError(
        "kis_devlp.yaml을 찾을 수 없습니다.\n"
        "프로젝트 루트(open-trading-api/)의 kis_devlp.yaml에 자격증명을 입력하세요.\n"
        "MANUAL.md 4장을 참고하세요."
    )


_yaml = _load_yaml()


# ── 거래 환경 ───────────────────────────────────────────────────────────────
ENV_DV = os.getenv("KIS_ENV", "demo")   # "demo" = 모의투자  /  "real" = 실전투자


# ── 자격증명 (모의/실전 분기) ────────────────────────────────────────────────
if ENV_DV == "real":
    APP_KEY    = _yaml["my_app"]
    APP_SECRET = _yaml["my_sec"]
    ACCOUNT_NO = str(_yaml["my_acct_stock"])
    BASE_URL   = _yaml["prod"]
else:
    APP_KEY    = _yaml["paper_app"]
    APP_SECRET = _yaml["paper_sec"]
    ACCOUNT_NO = str(_yaml["my_paper_stock"])
    BASE_URL   = _yaml["vps"]

ACNT_PRDT_CD = _yaml.get("my_prod", "01")


# ── 매매 파라미터 (환경변수로 재정의 가능) ─────────────────────────────────────
TARGET_STOCK             = os.getenv("TARGET_STOCK", "005930")
ORDER_DIVISION           = os.getenv("ORDER_TYPE",    "00")       # "00"=지정가 / "01"=시장가
BUY_OFFSET_KRW           = int(os.getenv("BUY_OFFSET",    "1000"))
SELL_OFFSET_KRW          = int(os.getenv("SELL_OFFSET",   "1000"))
ORDER_QUANTITY           = int(os.getenv("ORDER_QTY",     "1"))
POLLING_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL", "30"))

# 기본값(false): 매매 사이클을 1회만 실행하고 종료 (1회성 주문)
# "true"/"1"/"yes" 지정 시: POLLING_INTERVAL_SECONDS 간격으로 계속 반복하는 폴링 모드로 전환
POLLING_MODE = os.getenv("POLLING_MODE", "false").strip().lower() in ("1", "true", "yes")


# ── 거래 시간 ───────────────────────────────────────────────────────────────
TRADING_START_HOUR   = 9
TRADING_START_MINUTE = 10
TRADING_END_HOUR     = 15
TRADING_END_MINUTE   = 30


# ── 로그 ────────────────────────────────────────────────────────────────────
LOG_FILE  = Path(__file__).parent / "auto_trader.log"
LOG_LEVEL = "INFO"


# ── API 엔드포인트 ───────────────────────────────────────────────────────────
TOKEN_ENDPOINT   = "/oauth2/tokenP"
PRICE_ENDPOINT   = "/uapi/domestic-stock/v1/quotations/inquire-price"
BALANCE_ENDPOINT = "/uapi/domestic-stock/v1/trading/inquire-balance"
ORDER_ENDPOINT   = "/uapi/domestic-stock/v1/trading/order-cash"


# ── TR_ID (실전 기준; auth 모듈이 모의용으로 자동 변환) ──────────────────────
TR_PRICE   = "FHKST01010100"   # 현재가 조회 (실전/모의 동일)
TR_BALANCE = "TTTC8434R"       # 잔고 조회
TR_BUY     = "TTTC0012U"       # 매수 주문
TR_SELL    = "TTTC0011U"       # 매도 주문


# ── 기타 상수 ───────────────────────────────────────────────────────────────
MARKET_CODE             = "J"
SAMSUNG_CODE            = "005930"
TOKEN_CACHE_FILE        = Path(__file__).parent / "token_cache.json"
MAX_RETRIES             = 3
API_RETRY_DELAY_SECONDS = 2
REQUEST_TIMEOUT_SECONDS = 10


# ── Config 클래스 (auth.py · market_data.py 등 기존 모듈 하위호환용) ─────────
class Config:
    APP_KEY                  = APP_KEY
    APP_SECRET               = APP_SECRET
    ACCOUNT_ID               = f"{ACCOUNT_NO}-{ACNT_PRDT_CD}"
    BASE_URL                 = BASE_URL
    TOKEN_ENDPOINT           = TOKEN_ENDPOINT
    TOKEN_CACHE_FILE         = TOKEN_CACHE_FILE
    REQUEST_TIMEOUT_SECONDS  = REQUEST_TIMEOUT_SECONDS
    API_RETRY_DELAY_SECONDS  = API_RETRY_DELAY_SECONDS
    MAX_RETRIES              = MAX_RETRIES
    PRICE_ENDPOINT           = PRICE_ENDPOINT
    ACCOUNT_BALANCE_ENDPOINT = BALANCE_ENDPOINT
    ORDER_BUY_ENDPOINT       = ORDER_ENDPOINT
    ORDER_SELL_ENDPOINT      = ORDER_ENDPOINT
    MARKET_CODE              = MARKET_CODE
    SAMSUNG_CODE             = SAMSUNG_CODE
    ORDER_QUANTITY           = ORDER_QUANTITY
    BUY_OFFSET_KRW           = BUY_OFFSET_KRW
    SELL_OFFSET_KRW          = SELL_OFFSET_KRW
    BUY                      = "01"
    SELL                     = "02"

    @classmethod
    def validate_credentials(cls) -> bool:
        if not cls.APP_KEY or not cls.APP_SECRET:
            raise ValueError("kis_devlp.yaml에 앱키/앱시크릿이 입력되지 않았습니다.")
        return True


if __name__ == "__main__":
    try:
        Config.validate_credentials()
        mode = "모의투자" if ENV_DV == "demo" else "실전투자"
        print(f"✓ 설정 로드 완료 ({mode})")
        print(f"  대상 종목 : {TARGET_STOCK}")
        print(f"  BASE_URL  : {BASE_URL}")
        print(f"  계좌번호  : {ACCOUNT_NO}-{ACNT_PRDT_CD}")
    except Exception as e:
        print(f"✗ 오류: {e}")
