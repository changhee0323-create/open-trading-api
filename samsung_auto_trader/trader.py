"""
[트레이더 모듈] Samsung Auto Trader
────────────────────────────────────────────────────
역할: 거래 조건을 판단하고 매매 사이클(그리드 주문)을 실행합니다.

매매 사이클 (그리드 주문 1회):
  ① 현재가 조회
  ② 계좌 예수금 · 보유수량 조회
  ③ 매수 조건 충족 시 → (현재가 - BUY_OFFSET_KRW) 가격에 매수 지정가 주문
  ④ 매도 조건 충족 시 → (현재가 + SELL_OFFSET_KRW) 가격에 매도 지정가 주문

실행 방식 (config.POLLING_MODE로 선택):
  • 기본값(False) — 1회성 주문 : 위 사이클을 한 번만 실행하고 종료
  • POLLING_MODE=true — 반복 폴링 : POLLING_INTERVAL_SECONDS 초 간격으로 ①~④를 계속 반복

매수/매도 판단 기준:
  매수 : 예수금 ≥ (매수가 × 주문수량)
  매도 : 보유수량 ≥ 주문수량
"""

import logging
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import account
import config
import market_data
import orders

logger = logging.getLogger(__name__)

# 한국 거래소 정규장은 한국시간(KST, UTC+9) 기준으로 운영됩니다.
# 실행 환경의 시스템 시계가 KST가 아닌 경우(예: UTC로 설정된 서버/컨테이너)
# datetime.now()를 그대로 비교하면 실제 장 운영 시간과 어긋나므로
# 반드시 KST로 변환한 시각을 기준으로 판단합니다.
KST = ZoneInfo("Asia/Seoul")


def _now_kst() -> datetime:
    return datetime.now(KST)


# ─────────────────────────────────────────────────
# [STEP 1] 거래 가능 시간 확인
#   주말(토·일) 및 거래 시간 외에는 주문하지 않습니다.
#   한국 주식시장 정규 거래 시간: 09:00 ~ 15:30 (KST)
#   → 시초가 혼잡 방지를 위해 09:10부터 주문 시작 (config 설정)
#   ※ 공휴일 처리는 별도 API(휴장일 조회)가 필요하므로 현재는 주말만 체크
# ─────────────────────────────────────────────────
def _is_trading_time() -> bool:
    now = _now_kst()

    # 토요일(5), 일요일(6)은 거래 불가
    if now.weekday() >= 5:
        return False

    # 현재 시각(KST)이 거래 시간 범위 안에 있는지 확인
    start = (config.TRADING_START_HOUR, config.TRADING_START_MINUTE)
    end   = (config.TRADING_END_HOUR,   config.TRADING_END_MINUTE)
    cur   = (now.hour, now.minute)
    return start <= cur <= end


# ─────────────────────────────────────────────────
# [STEP 2] 매매 사이클 1회 실행
#   거래 시간 내에 POLLING_INTERVAL_SECONDS마다 호출됩니다.
# ─────────────────────────────────────────────────
def run_cycle() -> None:
    logger.info("-" * 50)

    # [2-1] 현재가 조회
    #   현재가를 기준으로 매수가(현재가 - offset)와 매도가(현재가 + offset)를 결정합니다.
    price = market_data.get_current_price(config.TARGET_STOCK)
    if price is None:
        logger.error("현재가 조회 실패 — 이번 사이클 건너뜀")
        return

    # [2-2] 계좌 잔고 및 보유수량 조회
    #   예수금: 매수 주문 가능 여부 판단에 사용
    #   보유수량: 매도 주문 가능 여부 판단에 사용
    cash, holdings = account.get_balance()
    qty_held = holdings.get(config.TARGET_STOCK, 0)  # 대상 종목 보유수량 (없으면 0)

    # [2-3] 매수 주문 처리
    #   지정가: 매수가 = 현재가 - BUY_OFFSET_KRW
    #   시장가: 오프셋 없이 현재가로 예수금 충족 여부만 판단
    if config.ORDER_DIVISION == "01":  # 시장가
        buy_price = price
    else:                              # 지정가
        buy_price = price - config.BUY_OFFSET_KRW
    buy_cost = buy_price * config.ORDER_QUANTITY
    if cash is None:
        logger.error("매수 주문 건너뜀 — 계좌 조회 실패로 예수금 확인 불가")
    elif cash >= buy_cost:
        orders.buy(config.TARGET_STOCK, buy_price, config.ORDER_QUANTITY)
    else:
        logger.info(
            f"매수 주문 건너뜀 — 예수금 부족 "
            f"(필요: {buy_cost:,} KRW, 가용: {cash:,} KRW)"
        )

    # 매수·매도 주문 사이에 1초 간격을 두어 API 부하를 줄입니다.
    time.sleep(1)

    # [2-4] 매도 주문 처리
    #   지정가: 매도가 = 현재가 + SELL_OFFSET_KRW
    #   시장가: 오프셋 없이 즉시 체결 요청
    if config.ORDER_DIVISION == "01":  # 시장가
        sell_price = price
    else:                              # 지정가
        sell_price = price + config.SELL_OFFSET_KRW
    if qty_held >= config.ORDER_QUANTITY:
        orders.sell(config.TARGET_STOCK, sell_price, config.ORDER_QUANTITY)
    else:
        logger.info(f"매도 주문 건너뜀 — 보유수량 부족 ({qty_held}주 보유)")


# ─────────────────────────────────────────────────
# [STEP 3] 메인 실행부
#   기본값 — POLLING_MODE=false (1회성 주문) :
#     거래 시간이면 run_cycle()을 단 1회만 실행하고 즉시 종료.
#     (거래 시간 외라면 주문 없이 바로 종료)
#   옵션  — POLLING_MODE=true  (반복 폴링) :
#     거래 시간 동안 POLLING_INTERVAL_SECONDS 간격으로 run_cycle()을 계속 반복.
#     Ctrl+C 입력 시 main.py에서 KeyboardInterrupt를 받아 종료합니다.
# ─────────────────────────────────────────────────
def run() -> None:
    mode = "모의투자" if config.ENV_DV == "demo" else "실전투자"
    run_mode = "반복 폴링" if config.POLLING_MODE else "1회 실행 후 종료"
    logger.info("=" * 50)
    logger.info(f"Samsung Auto Trader 시작  ({mode})")
    logger.info(f"대상 종목  : {config.TARGET_STOCK}")
    logger.info(f"매수 오프셋: -{config.BUY_OFFSET_KRW:,} KRW")
    logger.info(f"매도 오프셋: +{config.SELL_OFFSET_KRW:,} KRW")
    logger.info(f"주문 수량  : {config.ORDER_QUANTITY}주")
    logger.info(
        f"거래 시간  : {config.TRADING_START_HOUR:02d}:{config.TRADING_START_MINUTE:02d} – "
        f"{config.TRADING_END_HOUR:02d}:{config.TRADING_END_MINUTE:02d}"
    )
    logger.info(f"실행 방식  : {run_mode}" + (f" (간격 {config.POLLING_INTERVAL_SECONDS}초)" if config.POLLING_MODE else ""))
    logger.info("=" * 50)

    while True:
        # 거래 가능 시간인지 먼저 확인
        if not _is_trading_time():
            now = _now_kst()
            if not config.POLLING_MODE:
                logger.warning(
                    f"거래 시간 외 (KST {now.strftime('%H:%M:%S')}) "
                    f"— 주문을 내지 않고 종료합니다. (반복 실행을 원하면 POLLING_MODE=true)"
                )
                return
            logger.debug(
                f"거래 시간 외 (KST {now.strftime('%H:%M:%S')}) "
                f"— {config.POLLING_INTERVAL_SECONDS}초 후 재확인"
            )
            time.sleep(config.POLLING_INTERVAL_SECONDS)
            continue

        # 매매 사이클 실행 — 예외가 발생해도 (폴링 모드에서는) 루프가 계속됩니다.
        try:
            run_cycle()
        except Exception as exc:
            logger.error(f"사이클 오류: {exc}", exc_info=True)

        if not config.POLLING_MODE:
            logger.info("매매 사이클 1회 완료 — 프로그램을 종료합니다. (반복 실행을 원하면 POLLING_MODE=true)")
            return

        # 다음 사이클까지 대기
        time.sleep(config.POLLING_INTERVAL_SECONDS)
