#!/usr/bin/env python3
"""
[진입점] Samsung Auto Trader
────────────────────────────────────────────────────
역할: 프로그램의 시작점입니다.
      로거를 설정하고 trader.run()을 호출하여 매매 사이클을 시작합니다.
      기본값은 1회성 주문(실행 후 즉시 종료)이며, POLLING_MODE=true 지정 시
      반복 폴링 모드로 전환됩니다.

실행 방법:
  python main.py                            # 모의투자 / 1회성 주문 (기본값)
  KIS_ENV=real python main.py               # 실전투자 / 1회성 주문
  TARGET_STOCK=000660 python main.py        # SK하이닉스 / 1회성 주문
  BUY_OFFSET=500 SELL_OFFSET=500 python main.py     # 오프셋 조정 / 1회성 주문
  POLLING_MODE=true python main.py          # 반복 폴링 모드 (옵션)
"""

import sys
import logging

# 로거 설정 함수 (logger.py에 정의)
from logger import setup_logger

# 설정 모듈: kis_devlp.yaml 로드 및 환경변수 적용
import config

# 트레이더 모듈: 폴링 기반 매매 루프
import trader


def main() -> None:
    # ─────────────────────────────────────────────
    # [STEP 1] 로거 초기화
    #   - 루트 로거("")에 핸들러를 붙여 trader/market_data/account/orders 등
    #     모든 하위 모듈 로그가 콘솔·파일(auto_trader.log) 양쪽에 기록되게 합니다.
    # ─────────────────────────────────────────────
    setup_logger("", log_file=config.LOG_FILE, level=config.LOG_LEVEL)
    logger = logging.getLogger("samsung_auto_trader")

    # ─────────────────────────────────────────────
    # [STEP 2] 트레이더 실행 (무한 루프)
    #   trader.run()은 Ctrl+C 입력 전까지 종료되지 않습니다.
    #   예외 처리:
    #     KeyboardInterrupt : Ctrl+C → 정상 종료 (종료 코드 0)
    #     FileNotFoundError : kis_devlp.yaml 미존재 → 안내 메시지 출력 후 종료 (코드 1)
    #     기타 Exception    : 예상치 못한 오류 → 스택 트레이스 출력 후 종료 (코드 1)
    # ─────────────────────────────────────────────
    try:
        trader.run()
    except KeyboardInterrupt:
        logger.info("사용자가 트레이더를 종료했습니다 (Ctrl+C)")
        sys.exit(0)
    except FileNotFoundError as exc:
        # kis_devlp.yaml이 없을 때 사용자에게 설정 방법 안내
        logger.error(str(exc))
        sys.exit(1)
    except Exception as exc:
        logger.critical(f"예상치 못한 오류: {exc}", exc_info=True)
        sys.exit(1)


# 이 파일을 직접 실행했을 때만 main()을 호출합니다.
# (다른 파일에서 import할 때는 자동으로 실행되지 않음)
if __name__ == "__main__":
    main()
