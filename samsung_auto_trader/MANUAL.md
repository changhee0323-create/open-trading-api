# Samsung Auto Trader — 사용 매뉴얼

> 한국투자증권(KIS) Open API를 이용한 **모의/실전 국내주식 자동매매** 프로그램
>
> **최종 업데이트**: 2026-06-08

---

## 목차

1. [프로그램 개요](#1-프로그램-개요)
2. [가동을 위한 설정](#2-가동을-위한-설정)
3. [모의투자 수행 방법](#3-모의투자-수행-방법)
4. [실전투자 수행 방법](#4-실전투자-수행-방법)
5. [프로그램 개별 요소 설명](#5-프로그램-개별-요소-설명)
6. [자주 묻는 질문 및 오류 해결](#6-자주-묻는-질문-및-오류-해결)
7. [주의 사항](#7-주의-사항)

---

## 1. 프로그램 개요

| 항목 | 내용 |
|------|------|
| 목적 | KIS Open API 모의/실전 계좌를 통해 국내 주식 자동매매 |
| 기본 전략 | 그리드 주문 (현재가 ±오프셋 지정가 주문) |
| 기본 실행 방식 | **1회성 주문** — 실행 시 매매 사이클을 한 번만 수행하고 종료 (`POLLING_MODE=true`로 반복 폴링 선택 가능) |
| 기본 종목 | 삼성전자 (005930) — 환경변수로 변경 가능 |
| 거래 시간 | 평일 09:10 ~ 15:30 KST (정규 거래 시간) |
| 지원 모드 | 모의투자 (기본값) / 실전투자 |
| 설정 파일 | `kis_devlp.yaml` (프로젝트 루트) |

### 프로그램 동작 흐름

기본값은 **실행할 때마다 매매 사이클을 1회만 수행하고 종료하는 "1회성 주문"** 방식입니다.
원할 때 실행해서 그 시점의 시세를 기준으로 주문을 넣고 끝내는 구조이며,
`POLLING_MODE=true`를 지정하면 사이클이 끝난 뒤 종료하지 않고 일정 간격으로 계속 반복하는 **폴링 모드**로 전환됩니다.

```
[시작] python main.py
  ↓
[설정 로드] kis_devlp.yaml + 환경변수            ← config.py
  ↓
[로거 초기화] auto_trader.log + 콘솔             ← logger.py
  ↓
[거래 시간 확인 (평일 09:10~15:30 KST)]           ← trader._is_trading_time()
  │
  ├─ 거래 시간 외 ─┬─ 기본값(POLLING_MODE=false) ──→ 주문 없이 즉시 종료
  │               └─ POLLING_MODE=true ──→ [POLL_INTERVAL초 대기] → 위로 돌아가 재확인
  │
  ↓ 거래 시간 내
[현재가 조회]               ← market_data.get_current_price()
  ↓
[예수금·보유수량 조회]        ← account.get_balance()
  ↓
[매수 주문] 예수금 ≥ 주문금액  ← orders.buy()
  ↓
[매도 주문] 보유수량 ≥ 주문수량 ← orders.sell()
  │
  ├─ 기본값(POLLING_MODE=false) ──→ 매매 사이클 1회 완료, 프로그램 종료
  └─ POLLING_MODE=true          ──→ [POLL_INTERVAL초 대기] → 위 사이클 처음부터 반복
```

이 매뉴얼은 **① 가동을 위한 설정 → ② 모의투자 수행 → ③ 실전투자 수행 → ④ 개별 요소 설명** 순서로 구성되어 있습니다.
처음 사용한다면 반드시 이 순서대로 따라 하세요. 실전투자는 **모의투자 검증 없이 바로 시도하지 마세요.**

---

## 2. 가동을 위한 설정

프로그램을 실행하기 전, 아래 항목을 순서대로 준비합니다.

### 2-1. 한국투자증권 Open API 신청

1. [한국투자증권 홈페이지](https://www.koreainvestment.com) 로그인
2. **트레이딩 → Open API → KIS Developers** 메뉴 접속
3. **앱 등록** → "국내 주식 주문/조회" 권한 포함하여 신청
4. 승인 후 발급받는 정보:
   - **앱키 (APP_KEY)**
   - **앱 시크릿 (APP_SECRET)**

> 모의투자용과 실전투자용 앱키·시크릿은 **별도로 발급**됩니다.
> 발급 화면에서 "모의투자" / "실전투자" 탭을 구분하여 신청하세요.

### 2-2. 모의투자 계좌 개설 및 예수금 충전

- KIS HTS 또는 앱에서 **모의투자 계좌**를 별도로 개설해야 합니다.
- 개설 후 HTS/앱에서 **모의투자 예수금 충전**이 필수입니다.
  - 예수금이 0원이면 매수 조건 미충족으로 주문이 발생하지 않습니다.

### 2-3. 계좌번호 확인

계좌번호는 **8자리-2자리** 형식입니다.

```
예) 50123456-01
    ↑ 앞 8자리 → my_paper_stock(모의) / my_acct_stock(실전) 에 입력
               ↑ 뒤 2자리 → my_prod 에 입력 (일반 위탁계좌 = "01")
```

### 2-4. Python 및 패키지 설치

```bash
# Python 버전 확인 (3.9 이상 필요)
python --version

# 의존 패키지 설치 (프로젝트 루트 또는 samsung_auto_trader/ 안에서 실행)
pip install -r samsung_auto_trader/requirements.txt
```

| 패키지 | 버전 | 용도 |
|--------|------|------|
| `requests` | 2.31.0 | KIS API HTTP 통신 |
| `python-dotenv` | 1.0.0 | .env 파일 로드 (선택적 사용) |
| `pyyaml` | 6.0 이상 | `kis_devlp.yaml` 설정 파일 읽기 |

### 2-5. kis_devlp.yaml에 자격증명 입력 (필수)

**프로젝트 루트**(`open-trading-api/kis_devlp.yaml`)를 VS Code Explorer에서 열어
아래 항목을 실제 값으로 교체합니다.

```yaml
# 실전투자 앱키 (모의투자만 사용할 경우 비워둬도 됨 — 4장에서 다시 설명)
my_app: "발급받은_실전_앱키"
my_sec: "발급받은_실전_앱시크릿"

# ★ 모의투자 앱키 (모의투자 실행을 위한 필수 입력)
paper_app: "발급받은_모의투자_앱키"
paper_sec: "발급받은_모의투자_앱시크릿"

# HTS ID (한국투자증권 로그인 아이디)
my_htsid: "HTS_아이디"

# 실전투자 계좌번호 앞 8자리 (실전투자 시 필요)
my_acct_stock: "12345678"

# ★ 모의투자 계좌번호 앞 8자리 (모의투자 실행을 위한 필수 입력)
my_paper_stock: "50123456"

# 계좌상품코드 뒤 2자리 (일반 위탁계좌 = 01)
my_prod: "01"

# 아래 항목은 수정하지 않습니다 (프로그램이 자동으로 사용)
prod: "https://openapi.koreainvestment.com:9443"
vps:  "https://openapivts.koreainvestment.com:29443"
```

> **보안 주의**: `kis_devlp.yaml`은 `.gitignore`에 포함되어 있어 Git에 올라가지 않습니다.
> 절대 공개 저장소에 업로드하지 마세요.

> 매매 파라미터(종목, 오프셋, 수량 등)는 `kis_devlp.yaml`이 아니라 **실행 시 환경변수**로 조정합니다.
> 자세한 내용은 [5-5. 환경변수 전체 목록](#5-5-환경변수-전체-목록)을 참고하세요.

### 2-6. 설정 로드 확인

자격증명 입력이 끝나면 `config.py`를 단독 실행하여 정상적으로 로드되는지 확인합니다.

```bash
cd samsung_auto_trader
python config.py
```

정상 출력 예시:
```
✓ 설정 로드 완료 (모의투자)
  대상 종목 : 005930
  BASE_URL  : https://openapivts.koreainvestment.com:29443
  계좌번호  : 50123456-01
```

오류가 표시되면 [6장 자주 묻는 질문](#6-자주-묻는-질문-및-오류-해결)을 참고하세요.

### 2-7. VS Code 작업 환경 준비

#### 파일 탐색 — Explorer 패널 (`Ctrl+Shift+E`)

```
open-trading-api/
├── kis_devlp.yaml          ← ① 여기서 자격증명 입력
└── samsung_auto_trader/
    ├── main.py             ← ② 진입점
    ├── config.py           ← ③ 설정 확인/수정
    ├── trader.py           ← ④ 매매 전략 수정
    └── auto_trader.log     ← ⑤ 실행 후 생성되는 로그
```

#### 터미널 열기 (`Ctrl+`` ` ``)

```bash
cd /workspaces/open-trading-api/samsung_auto_trader
```

#### Run and Debug (F5) — Python 디버거 연결 (선택)

`.vscode/launch.json`이 없다면 아래 내용으로 생성해두면 브레이크포인트·변수 확인 등
디버깅 기능을 바로 사용할 수 있습니다.

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Samsung Auto Trader (모의투자)",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/samsung_auto_trader/main.py",
            "cwd": "${workspaceFolder}/samsung_auto_trader",
            "console": "integratedTerminal"
        },
        {
            "name": "Samsung Auto Trader (실전투자)",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/samsung_auto_trader/main.py",
            "cwd": "${workspaceFolder}/samsung_auto_trader",
            "env": { "KIS_ENV": "real" },
            "console": "integratedTerminal"
        }
    ]
}
```

`F5`를 누르면 선택한 구성(모의투자/실전투자)으로 디버거가 연결된 채 실행됩니다.

---

## 3. 모의투자 수행 방법

> 설정(2장)이 끝났다면 이제 모의투자로 프로그램을 가동해봅니다.
> **실전투자 전에는 반드시 이 단계에서 충분히 검증해야 합니다.**

### 3-1. 단계별 모듈 점검 (최초 1회 권장)

전체 실행 전, 각 모듈을 독립 실행하여 문제를 단계별로 좁혀갈 수 있습니다.

```bash
cd /workspaces/open-trading-api/samsung_auto_trader

# Step 1: 설정 파일 로드 확인
python config.py
# 기대: ✓ 설정 로드 완료 (모의투자)

# Step 2: 인증 토큰 발급 확인
python auth.py
# 기대: ✓ Token acquired: ...

# Step 3: 현재가 조회 확인
python market_data.py
# 기대: ✓ Samsung price: XXX,XXX KRW

# Step 4: 계좌 잔고 조회 확인
python account.py
# 기대: ✓ Account ... | 예수금: X,XXX,XXX KRW

# Step 5: 전체 실행
python main.py
```

### 3-2. 기본 실행 — 1회성 주문 (기본값)

`samsung_auto_trader/` 디렉토리 안에서 실행합니다. (`KIS_ENV`를 지정하지 않으면 모의투자가 기본값입니다.)

```bash
cd /workspaces/open-trading-api/samsung_auto_trader
python main.py
```

**기본적으로 프로그램은 실행될 때마다 그 시점의 시세를 기준으로 매매 사이클을 단 한 번만 수행하고 곧바로 종료됩니다** (`POLLING_MODE` 기본값 `false`).

| 실행 시점 | 동작 |
|-----------|------|
| 거래 시간 내 (평일 09:10~15:30 KST) | 현재가 조회 → 잔고 확인 → 매수/매도 조건 평가 → (조건 충족 시) 주문 접수 → 종료 |
| 거래 시간 외 | 주문을 내지 않고 안내 로그만 남긴 뒤 즉시 종료 |

종료 시 아래와 같은 로그가 남고 프로그램이 자동으로 끝납니다 (별도로 `Ctrl+C`를 누를 필요가 없습니다).

```
2026-06-08 11:30:09 | INFO | trader | 매매 사이클 1회 완료 — 프로그램을 종료합니다. (반복 실행을 원하면 POLLING_MODE=true)
```

다시 주문을 시도하려면 `python main.py`를 다시 실행하면 됩니다.
거래 시간 동안 자동으로 계속 반복시키고 싶다면 아래 [폴링 모드](#폴링-모드-polling_mode--반복-실행으로-전환-옵션)를 사용하세요.

### 3-3. 매매 파라미터 조정

자격증명과 달리 매매 파라미터는 **환경변수**로 실행 시점에 자유롭게 바꿀 수 있습니다.
(전체 목록은 [5-5장](#5-5-환경변수-전체-목록) 참고)

#### 종목 변경

```bash
# SK하이닉스 (000660)
TARGET_STOCK=000660 python main.py

# NAVER (035420)
TARGET_STOCK=035420 python main.py
```

#### 시장가 주문 모드

```bash
# 모의투자 / 시장가
ORDER_TYPE=01 python main.py
```

> **시장가 주문 주의사항**:
> - `BUY_OFFSET` / `SELL_OFFSET` 값은 무시됩니다.
> - 주문 즉시 호가 최우선 가격으로 체결됩니다.
> - 주문단가(`ORD_UNPR`)가 자동으로 `"0"`으로 전송됩니다.

#### 폴링 모드 (`POLLING_MODE`) — 반복 실행으로 전환 (옵션)

기본값(1회성 주문)과 달리 "거래 시간 동안 계속 지켜보다가 조건이 맞을 때마다 자동으로 반복 매매"하고
싶다면 `POLLING_MODE=true`를 지정하세요. `POLL_INTERVAL`초(기본 30초) 간격으로 매매 사이클을
**`Ctrl+C`를 누르기 전까지 계속 반복**합니다.

```bash
# 폴링 모드로 전환 — 기본 간격(30초)으로 반복
POLLING_MODE=true python main.py

# 폴링 간격을 60초로 늘려서 반복
POLLING_MODE=true POLL_INTERVAL=60 python main.py
```

> 폴링 모드는 터미널을 계속 점유하는 **장기 실행 프로세스**입니다.
> 다른 명령을 함께 쓰려면 [3-4장](#3-4-실행-화면과-로그-동시-확인)처럼 터미널을 분할하고,
> 종료할 때는 [3-5장](#3-5-종료-방법)을 참고하세요.
> `POLL_INTERVAL`은 **30초 이상** 권장합니다 (자세한 이유는 [6장 FAQ](#6-자주-묻는-질문-및-오류-해결) 참고).

#### 파라미터 조합 예시

```bash
# SK하이닉스 / 오프셋 500원 / 2주씩 1회 주문
TARGET_STOCK=000660 BUY_OFFSET=500 SELL_OFFSET=500 ORDER_QTY=2 python main.py

# NAVER / 시장가 / 3주 / 1회 주문
TARGET_STOCK=035420 ORDER_TYPE=01 ORDER_QTY=3 python main.py

# 삼성전자 / 폴링 모드 / 60초 간격으로 반복 매매
POLLING_MODE=true POLL_INTERVAL=60 python main.py
```

### 3-4. 실행 화면과 로그 동시 확인

기본값(1회성 주문)은 실행 후 곧바로 종료되므로, 실행이 끝난 뒤 `auto_trader.log`만 확인해도 충분합니다.
**폴링 모드(`POLLING_MODE=true`)** 처럼 프로그램이 계속 실행 중인 상태에서 동시에 모니터링하려면,
터미널 우상단의 **분할 아이콘** 클릭 (또는 `Ctrl+Shift+5`)으로 실행과 로그 확인을 함께 진행할 수 있습니다.

| 왼쪽 터미널 | 오른쪽 터미널 |
|------------|--------------|
| `POLLING_MODE=true python main.py` 실행 | `tail -f auto_trader.log` 로그 모니터링 |

```bash
# 전체 로그 실시간 확인
tail -f auto_trader.log

# 오류만 필터링
tail -f auto_trader.log | grep -i "error\|오류"

# 주문 관련만 필터링
tail -f auto_trader.log | grep "주문"
```

정상 동작 시 콘솔/로그 출력 예시와 메시지 해석은 [5-6장 로그 메시지 해석](#5-6-로그-메시지-해석)을 참고하세요.

### 3-5. 종료 방법

| 실행 방식 | 종료 방법 |
|-----------|-----------|
| 기본값 — 1회성 주문 (`POLLING_MODE=false`) | 매매 사이클 1회 완료 후 **자동 종료** (별도 조작 불필요) |
| 폴링 모드 (`POLLING_MODE=true`) | 터미널에서 **`Ctrl+C`** 입력 시 정상 종료 |

```
2026-06-08 09:30:00 | INFO | samsung_auto_trader | 사용자가 트레이더를 종료했습니다 (Ctrl+C)
```

### 3-6. 실전투자로 넘어가기 전 체크포인트

- 1회성 주문(기본값) 또는 폴링 모드로 모의투자를 **여러 차례·충분한 기간(최소 1주일 이상)** 실행하며 매수/매도 주문이 의도대로 체결되는지 확인했는가?
- `auto_trader.log`에 오류 없이 주문이 기록되는가?
- 종목·오프셋·수량·실행 방식(`POLLING_MODE`) 등 파라미터가 원하는 전략과 일치하는가?

모두 확인되었다면 [4장 실전투자 수행 방법](#4-실전투자-수행-방법)으로 진행합니다.

---

## 4. 실전투자 수행 방법

> ⚠️ 실전투자는 **실제 자산에 영향**을 줍니다. 반드시 [3장 모의투자](#3-모의투자-수행-방법)로 충분히 검증한 후에만 진행하세요.

### 4-1. 전환 전 체크리스트

실전투자 전환 전 아래 항목을 모두 확인하세요.

- [ ] 모의투자로 최소 **1주일 이상** 정상 동작 확인
- [ ] `auto_trader.log`에서 오류 없이 주문 체결 확인
- [ ] `kis_devlp.yaml`에 실전투자 앱키(`my_app`, `my_sec`) 입력
- [ ] `kis_devlp.yaml`에 실전투자 계좌번호(`my_acct_stock`) 입력
- [ ] `ORDER_QTY=1` 소량으로 시작
- [ ] 오프셋 값이 예상 수익/손실 범위 내인지 확인

### 4-2. 실전투자 자격증명 입력

[2-1장](#2-1-한국투자증권-open-api-신청)에서 안내한 대로 **실전투자용 앱키/시크릿**을 별도로 발급받아
`kis_devlp.yaml`의 아래 항목에 입력합니다. (모의투자 항목과는 별개입니다.)

```yaml
# 실전투자 앱키 — 반드시 "실전투자" 탭에서 발급받은 값 사용
my_app: "발급받은_실전_앱키"
my_sec: "발급받은_실전_앱시크릿"

# 실전투자 계좌번호 앞 8자리
my_acct_stock: "12345678"
```

### 4-3. 실행 방법

`KIS_ENV=real` 환경변수를 지정하면 `config.py`가 자동으로 실전투자용 앱키·계좌·`BASE_URL`(`prod`)을 선택합니다.
모의투자와 마찬가지로 **기본값은 1회성 주문**(`POLLING_MODE=false`)입니다 — 실행하면 그 시점의 매매 사이클을
한 번만 수행하고 종료합니다. 처음 실전투자로 전환할 때는 의도치 않은 반복 매매를 막기 위해
**먼저 기본값(1회성)으로 실행 결과를 확인하는 것을 강력히 권장**합니다.

```bash
cd /workspaces/open-trading-api/samsung_auto_trader

# 실전투자 / 1회성 주문 (권장 — 먼저 이렇게 결과를 확인하세요)
KIS_ENV=real python main.py
```

결과를 확인했고 자동으로 반복 매매를 원한다면 모의투자와 동일하게 `POLLING_MODE=true`를 추가합니다.

```bash
# 실전투자 / SK하이닉스 / 시장가 / 1회성 주문
KIS_ENV=real TARGET_STOCK=000660 ORDER_TYPE=01 python main.py

# 실전투자 / 폴링 모드(반복 매매) / 60초 간격
KIS_ENV=real POLLING_MODE=true POLL_INTERVAL=60 python main.py
```

> ⚠️ `POLLING_MODE=true`로 실전투자를 실행하면 거래 시간 동안 **사람의 개입 없이 계속 주문이 반복**됩니다.
> 반드시 모의투자에서 폴링 모드로 충분히 검증한 뒤, 실전에서도 처음에는 1회성 주문으로 결과를 확인하고
> 단계적으로 전환하세요.

VS Code에서는 [2-7장](#2-7-vs-code-작업-환경-준비)에서 만든 `launch.json`의
**"Samsung Auto Trader (실전투자)"** 구성을 선택하고 `F5`를 눌러 실행할 수도 있습니다.

### 4-4. 실전투자 운영 수칙

- **소액(1주)** 으로 시작하고, 정상 동작이 확인되면 점진적으로 수량을 늘리세요.
- 처음에는 **기본값(1회성 주문)** 으로 실행해 결과를 확인한 뒤, 필요할 때만 `POLLING_MODE=true`로 전환하세요.
- 장 시작(09:00~09:10)·종료(15:20~15:30) 시간대는 변동성이 크므로 주의하세요.
- 폴링 모드(`POLLING_MODE=true`)로 실행 중 긴급 정지가 필요하면 터미널에서 **`Ctrl+C`** 를 누르세요.
  - 단, **이미 접수된 주문은 자동으로 취소되지 않습니다.** KIS HTS/앱에서 별도로 취소해야 합니다.
- 폴링 모드로 실행할 때는 [3-4장](#3-4-실행-화면과-로그-동시-확인)과 동일하게 `tail -f auto_trader.log`로 실시간 모니터링하는 것을 권장합니다.

---

## 5. 프로그램 개별 요소 설명

### 5-1. 파일 구조

```
samsung_auto_trader/
├── main.py          ← [진입점] 로거 초기화 후 trader.run() 호출
├── config.py        ← [설정] kis_devlp.yaml 로드 + 환경변수 + 모듈 레벨 변수 정의
├── auth.py          ← [인증] 토큰 캐시/발급 + make_headers(tr_id) 제공
├── api_client.py    ← [HTTP] GET/POST 클래스 (auth.py의 클래스 기반 사용 시)
├── market_data.py   ← [시세] get_current_price(stock_code) 제공
├── account.py       ← [계좌] get_balance() → (예수금, 보유종목) 제공
├── orders.py        ← [주문] buy() / sell() 제공
├── trader.py        ← [전략] 매매 사이클 실행 (기본: 1회 실행 / POLLING_MODE=true 시 반복 폴링)
├── logger.py        ← [로그] 콘솔·파일 동시 출력 설정
├── utils.py         ← [유틸] 시간 헬퍼 함수
├── requirements.txt ← 의존 패키지 (requests, pyyaml, python-dotenv)
├── MANUAL.md        ← 이 문서
│
├── auto_trader.log  (실행 후 자동 생성) ← 거래 로그 (5MB 초과 시 롤링)
└── token_cache.json (실행 후 자동 생성) ← 당일 토큰 캐시
```

### 5-2. 매매 전략 — 그리드 주문

매매 사이클(`run_cycle()`)이 실행될 때마다 아래 로직을 수행합니다.
기본값(`POLLING_MODE=false`)에서는 이 사이클이 **실행당 1회**만 수행되고,
`POLLING_MODE=true`(폴링 모드)에서는 `POLL_INTERVAL`초 간격으로 반복 수행됩니다.

```
현재가: 284,000원 (예시 - 삼성전자)
BUY_OFFSET:  1,000원
SELL_OFFSET: 1,000원

매수 지정가: 284,000 - 1,000 = 283,000원  ← 현재가보다 1,000원 낮게 주문
매도 지정가: 284,000 + 1,000 = 285,000원  ← 현재가보다 1,000원 높게 주문
```

- **매수**: 가격이 내려올 때 체결되어 저점 매수
- **매도**: 가격이 올라갈 때 체결되어 고점 매도
- 두 주문 모두 체결 시 **2,000원 × 수량** 수익 (수수료 제외)

#### 주문 실행 조건

| 주문 | 실행 조건 |
|------|-----------|
| 매수 | 예수금 ≥ 매수가 × 주문수량 |
| 매도 | 보유수량 ≥ 주문수량 |

조건 미충족 시 해당 주문은 건너뛰고 로그에 이유가 기록됩니다.

#### 지정가 vs 시장가 비교

| 항목 | 지정가 (`ORDER_TYPE=00`, 기본값) | 시장가 (`ORDER_TYPE=01`) |
|------|----------------------------------|--------------------------|
| 체결 방식 | 지정 가격 도달 시 체결 | 현재 호가로 즉시 체결 |
| 체결 보장 | 보장 안 됨 (미체결 가능) | 사실상 즉시 체결 |
| 체결가 예측 | 가능 (오프셋으로 결정) | 불가능 |
| 슬리피지 | 없음 | 발생 가능 |
| 적합한 상황 | 그리드 전략, 목표가 매매 | 빠른 진입/청산 |

#### 오프셋 설정 가이드 (지정가 전용)

| 오프셋 | 특징 |
|--------|------|
| 작게 (100~500원) | 체결 빈도 높음, 건당 수익 적음 |
| 크게 (2,000~5,000원) | 체결 빈도 낮음, 건당 수익 큼 |

종목의 **일중 변동폭**을 참고하여 설정하는 것을 권장합니다.
삼성전자 기준 일중 변동폭은 보통 1,000~3,000원 수준입니다.

### 5-3. 모듈별 설명

#### main.py — 진입점

| 단계 | 내용 |
|------|------|
| STEP 1 | `setup_logger()`로 루트 로거 초기화 (콘솔 + `auto_trader.log`) |
| STEP 2 | `trader.run()` 호출 — 무한 루프 시작 |

| 예외 | 동작 |
|------|------|
| `KeyboardInterrupt` (Ctrl+C) | 정상 종료 메시지 출력 후 종료 코드 0 |
| `FileNotFoundError` (`kis_devlp.yaml` 없음) | 안내 메시지 출력 후 종료 코드 1 |
| 기타 `Exception` | 스택 트레이스 출력 후 종료 코드 1 |

#### config.py — 설정 모듈

프로그램 전체 설정의 단일 출처. 모든 모듈이 이 파일의 **모듈 레벨 변수**를 직접 참조합니다.

| 단계 | 내용 |
|------|------|
| STEP 1 | `kis_devlp.yaml` 탐색 (루트 → 모듈 디렉토리 순서) |
| STEP 2 | `KIS_ENV` 환경변수로 모의(`demo`)/실전(`real`) 분기 |
| STEP 3 | 해당 환경의 앱키·시크릿·계좌번호·BASE_URL 선택 |
| STEP 4 | 환경변수로 종목·오프셋·수량·폴링 간격 설정 |
| STEP 5 | API 엔드포인트·TR_ID 상수 정의 |
| STEP 6 | `Config` 클래스 제공 (auth.py 등 구형 모듈 하위호환) |

**주요 모듈 레벨 변수**:

| 변수 | 예시 값 | 설명 |
|------|---------|------|
| `ENV_DV` | `"demo"` | 거래 환경 |
| `APP_KEY` | `"PSim..."` | 모의/실전 앱키 (yaml에서 자동 선택) |
| `BASE_URL` | `"https://openapivts..."` | API 서버 URL |
| `ACCOUNT_NO` | `"50123456"` | 계좌번호 앞 8자리 |
| `TARGET_STOCK` | `"005930"` | 매매 종목 |
| `TR_BUY` | `"TTTC0012U"` | 매수 TR_ID (실전 기준, auth가 자동 변환) |

#### auth.py — 인증 모듈

```
get_token() 호출 흐름:
  token_cache.json (당일 발급) → 있으면 재사용
                               → 없으면 KIS 서버에서 신규 발급 후 저장
```

| 함수 | 설명 |
|------|------|
| `get_token()` | 유효한 토큰 반환 (캐시 우선) |
| `make_headers(tr_id)` | API 호출용 표준 헤더 딕셔너리 반환 |
| `_convert_tr_id(tr_id)` | 모의투자 모드 시 TR_ID 첫 글자 `T/J/C` → `V` 자동 변환 |

**TR_ID 자동 변환 예시**:
```
TTTC0012U (실전 매수) → VTTC0012U (모의 매수)
TTTC8434R (실전 잔고) → VTTC8434R (모의 잔고)
FHKST01010100 (현재가) → 변환 없음 (F로 시작)
```

#### market_data.py — 시세 조회

**API**: `GET /uapi/domestic-stock/v1/quotations/inquire-price`
**TR_ID**: `FHKST01010100` (실전/모의 동일)

```python
get_current_price(stock_code: str) -> Optional[int]
```

| 요청 파라미터 | 값 | 설명 |
|------------|-----|------|
| `fid_cond_mrkt_div_code` | `"J"` | KRX 시장 |
| `fid_input_iscd` | `"005930"` | 종목코드 |

| 응답 필드 경로 | 설명 |
|-------------|------|
| `output.stck_prpr` | 현재가 (문자열 → int 변환) |

#### account.py — 계좌 조회

**API**: `GET /uapi/domestic-stock/v1/trading/inquire-balance`
**TR_ID**: `TTTC8434R` (실전) → `VTTC8434R` (모의, 자동 변환)

```python
get_balance() -> Tuple[Optional[int], dict]
# 반환: (예수금 원단위 int, {종목코드: 보유수량} dict)
# 실패 시: (None, {})
```

| 응답 필드 | 경로 | 내용 |
|---------|------|------|
| 예수금 합계 | `output2[0].dnca_tot_amt` | 매수 가능 현금 (원) |
| 보유 종목코드 | `output1[].pdno` | 보유 종목 |
| 보유 수량 | `output1[].hldg_qty` | 보유 주수 |

#### orders.py — 주문

**API**: `POST /uapi/domestic-stock/v1/trading/order-cash`

| 구분 | TR_ID (실전) | TR_ID (모의, 자동 변환) |
|------|-------------|----------------------|
| 매수 | `TTTC0012U` | `VTTC0012U` |
| 매도 | `TTTC0011U` | `VTTC0011U` |

```python
buy(stock_code: str, price: int, qty: int) -> None
sell(stock_code: str, price: int, qty: int) -> None
```

**주요 요청 본문 파라미터**:

| 키 | 예시 | 설명 |
|----|------|------|
| `CANO` | `"50123456"` | 계좌번호 앞 8자리 |
| `ACNT_PRDT_CD` | `"01"` | 계좌상품코드 |
| `PDNO` | `"005930"` | 종목코드 |
| `ORD_DVSN` | `"00"` | 주문구분 (`00`=지정가, `01`=시장가) |
| `ORD_QTY` | `"1"` | 주문수량 (문자열) |
| `ORD_UNPR` | `"283000"` | 주문단가 (시장가 시 `"0"` 자동 설정) |

#### trader.py — 트레이더 (핵심 전략)

| 함수 | 역할 |
|------|------|
| `_is_trading_time()` | 평일 09:10~15:30 (KST) 여부 확인 — `zoneinfo`로 KST 변환 후 비교 |
| `run_cycle()` | 1회 매매 사이클 실행 (현재가→잔고→매수→매도) |
| `run()` | 메인 실행부. `POLLING_MODE=false`(기본값): `run_cycle()` 1회 실행 후 자동 종료(1회성 주문) / `POLLING_MODE=true`: `POLL_INTERVAL`초 간격 폴링 무한 루프(Ctrl+C 전까지 반복) |

#### logger.py — 로그 설정

`setup_logger(name, log_file, level)` 함수로 콘솔 핸들러와 `RotatingFileHandler`(5MB, 백업 3개)를
동시에 등록합니다. `main.py`가 루트 로거(`""`)에 적용하므로 `trader`/`market_data`/`account`/`orders` 등
모든 하위 모듈의 로그가 콘솔과 `auto_trader.log` 양쪽에 함께 기록됩니다.

#### utils.py — 유틸리티

거래 시간 판별, 남은 시간 계산, 가격 포맷팅 등 공용 헬퍼 함수를 제공합니다
(`is_within_trading_window`, `is_trading_day`, `format_price` 등).

### 5-4. api_client.py 에 대하여

`api_client.py`는 `APIClient`/`MarketData`/`Account`/`Orders` 클래스 기반의 HTTP 래퍼를 제공합니다.
다만 실제 매매 루프(`trader.py`)는 `auth.py`/`market_data.py`/`account.py`/`orders.py`의
**모듈 레벨 함수**(`get_token`, `get_current_price`, `get_balance`, `buy`/`sell`)를 직접 호출하므로,
평소 실행 흐름에서는 `api_client.py`의 클래스가 사용되지 않습니다. 클래스 기반 구조로 확장하고 싶을 때 참고하는 용도입니다.

### 5-5. 환경변수 전체 목록

| 변수명 | 기본값 | 설명 |
|--------|--------|------|
| `KIS_ENV` | `demo` | 거래 모드 (`demo`=모의투자, `real`=실전투자) |
| `TARGET_STOCK` | `005930` | 매매 대상 종목코드 |
| `ORDER_TYPE` | `00` | 주문 방식 (`00`=지정가, `01`=시장가) |
| `BUY_OFFSET` | `1000` | 매수가 오프셋 (원, 현재가에서 낮출 금액) — 지정가 전용 |
| `SELL_OFFSET` | `1000` | 매도가 오프셋 (원, 현재가에서 높일 금액) — 지정가 전용 |
| `ORDER_QTY` | `1` | 1회 주문 수량 (주) |
| `POLLING_MODE` | `false` | `true`/`1`/`yes` 지정 시 반복 폴링 모드로 전환 (기본값 `false`=1회성 주문, 1회 실행 후 자동 종료) |
| `POLL_INTERVAL` | `30` | 매매 사이클 반복 간격 (초), 최소 30 권장 — **`POLLING_MODE=true`일 때만 사용됨** |

> **자격증명(앱키·계좌번호)은 환경변수로 설정하지 않습니다.**
> 반드시 `kis_devlp.yaml`에 직접 입력하세요. (→ [2-5장](#2-5-kis_devlpyaml에-자격증명-입력-필수), [4-2장](#4-2-실전투자-자격증명-입력))

### 5-6. 로그 메시지 해석

프로그램 실행 시 **콘솔**과 **`auto_trader.log` 파일** 양쪽에 동시 기록됩니다.

정상 동작 시 콘솔 출력 예시:
```
2026-06-08 09:10:05 | INFO | samsung_auto_trader | ==================================================
2026-06-08 09:10:05 | INFO | samsung_auto_trader | Samsung Auto Trader 시작  (모의투자)
2026-06-08 09:10:05 | INFO | samsung_auto_trader | 대상 종목  : 005930
2026-06-08 09:10:05 | INFO | samsung_auto_trader | 매수 오프셋: -1,000 KRW
2026-06-08 09:10:05 | INFO | samsung_auto_trader | 매도 오프셋: +1,000 KRW
2026-06-08 09:10:05 | INFO | samsung_auto_trader | 주문 수량  : 1주
2026-06-08 09:10:05 | INFO | samsung_auto_trader | 거래 시간  : 09:10 – 15:30
2026-06-08 09:10:05 | INFO | samsung_auto_trader | 폴링 간격  : 30초
2026-06-08 09:10:05 | INFO | samsung_auto_trader | ==================================================
2026-06-08 09:10:06 | INFO | auth        | Using cached token from today
2026-06-08 09:10:07 | INFO | market_data | [005930] 현재가: 284,000 KRW
2026-06-08 09:10:08 | INFO | account     | 예수금: 10,000,000 KRW | 보유종목: {}
2026-06-08 09:10:08 | INFO | orders      | 매수 주문: [005930] 1주 @ 283,000 KRW
2026-06-08 09:10:09 | INFO | orders      | 매수 주문 완료 (주문번호: 0000012345)
2026-06-08 09:10:09 | INFO | trader      | 매도 주문 건너뜀 — 보유수량 부족 (0주 보유)
```

| 메시지 | 의미 | 상태 |
|--------|------|------|
| `Using cached token from today` | 오늘 발급된 토큰 재사용 | 정상 |
| `[005930] 현재가: XXX,XXX KRW` | 시세 조회 성공 | 정상 |
| `예수금: X,XXX,XXX KRW` | 잔고 조회 성공 | 정상 |
| `매수 주문 완료 (주문번호: ...)` | 주문 접수 완료 | 정상 |
| `매수 주문 건너뜀 — 예수금 부족` | 잔고 부족 | 예수금 충전 필요 |
| `매도 주문 건너뜀 — 보유수량 부족` | 미보유 종목 | 매수 체결 후 자동 해소 |
| `시세 조회 오류:` | API 오류 | 오류 내용 확인 필요 |
| `계좌 조회 예외:` | 네트워크/API 오류 | 재시도 자동 처리 |

`auto_trader.log` 파일은 5MB 초과 시 자동 롤링됩니다 (최대 3개 백업).

```bash
# 실시간 확인
tail -f auto_trader.log

# 오류만 필터
tail -f auto_trader.log | grep -i "error\|오류\|실패"

# 주문 내역만 확인
grep "주문" auto_trader.log
```

---

## 6. 자주 묻는 질문 및 오류 해결

**Q. `AttributeError: module 'config' has no attribute 'LOG_FILE'` 오류가 납니다.**

A. `config.py`가 구버전입니다. 수정된 최신 `config.py`로 교체하세요.
   최신 버전은 `kis_devlp.yaml`을 직접 읽으며 모듈 레벨 변수를 제공합니다.

---

**Q. `kis_devlp.yaml을 찾을 수 없습니다` 오류가 발생합니다.**

A. 프로젝트 루트(`open-trading-api/kis_devlp.yaml`)에 파일이 있는지 확인하세요.
   파일이 있다면 `paper_app`, `paper_sec`, `my_paper_stock` 값이 비어있지 않은지 확인하세요.

---

**Q. `API 오류 [APBK0013]: 접근토큰 발급 실패` 오류가 발생합니다.**

A. `kis_devlp.yaml`의 `paper_app`과 `paper_sec` 값이 올바른지 확인하세요.
   앱키는 모의투자/실전투자용이 별도로 발급됩니다. KIS Developers에서 "모의투자" 탭을 선택하여 재발급받으세요.

---

**Q. 주문이 나가지 않고 "예수금 부족"으로 건너뜁니다.**

A. 모의투자 계좌 예수금을 충전해야 합니다.
   KIS HTS 또는 앱 → 모의투자 → 예수금 충전 메뉴에서 가상 잔고를 추가하세요.

---

**Q. 거래 시간인데 주문이 체결되지 않습니다.**

A. 지정가 주문이므로 설정한 가격에 도달해야 체결됩니다.
   `BUY_OFFSET`과 `SELL_OFFSET`을 줄여보세요 (예: `200`~`500`).
   또는 `ORDER_TYPE=01`로 시장가 주문을 사용하면 즉시 체결됩니다.

---

**Q. 거래 시간 외에 실행하면 어떻게 되나요?**

A. 동작은 실행 방식에 따라 다릅니다.
   - **기본값(1회성 주문, `POLLING_MODE=false`)**: 주문을 내지 않고 "거래 시간 외... 종료합니다" 안내 로그만 남긴 뒤 곧바로 프로그램이 종료됩니다. 거래 시간에 다시 `python main.py`를 실행하면 됩니다.
   - **폴링 모드(`POLLING_MODE=true`)**: 프로그램이 종료되지 않고 `POLL_INTERVAL`초마다 시간을 체크하며 대기하다가, 거래 시간이 되면 자동으로 매매를 시작합니다.

---

**Q. 토큰을 매일 새로 발급받아야 하나요?**

A. 자동 처리됩니다. 당일 발급된 토큰이 `token_cache.json`에 저장되고,
   다음날 첫 실행 시 자동으로 갱신됩니다.

---

**Q. `module 'market_data' has no attribute 'get_current_price'` 오류가 납니다.**

A. `market_data.py`가 구버전입니다. 수정된 최신 파일로 교체하세요.
   최신 버전은 `get_current_price()`, `account.py`는 `get_balance()`,
   `orders.py`는 `buy()`/`sell()` 모듈 레벨 함수를 제공합니다.

---

**Q. 폴링 모드에서 간격(`POLL_INTERVAL`)을 5초로 설정해도 되나요?**

A. 권장하지 않습니다. KIS Open API는 요청 횟수 제한이 있습니다(모의투자 초당 1회, 실전투자 초당 5회).
   매 사이클마다 현재가·잔고·주문 최소 3회 API를 호출하므로,
   `POLLING_MODE=true`로 반복 실행할 때는 `POLL_INTERVAL`을 **30초 이상**으로 사용하세요.
   (기본값인 1회성 주문 모드에서는 `POLL_INTERVAL`이 사용되지 않으므로 해당하지 않습니다.)

---

## 7. 주의 사항

> ⚠️ **투자 원칙**

- 이 프로그램은 **교육·실습 목적**으로 제공됩니다.
- 자동매매는 예상치 못한 손실이 발생할 수 있습니다.
- **반드시 모의투자로 충분히 검증** 후 실전투자에 적용하세요.
- 실전투자 전환 시 처음에는 **소액(1주)** 으로 시작하세요.
- 장 시작(09:00~09:10)·종료(15:20~15:30) 시간대는 변동성이 크므로 주의하세요.

> ⚠️ **API 이용 규정**

- KIS Open API 요청 횟수 제한: 모의투자 초당 1회, 실전투자 초당 5회
- 기본값(1회성 주문)은 실행당 API 호출이 적어 제한에 걸릴 위험이 낮습니다.
- **폴링 모드(`POLLING_MODE=true`)** 사용 시 `POLL_INTERVAL`을 너무 짧게 설정하면 API 제한에 걸려 오류가 발생합니다 — **30초 이상** 권장합니다.

> ⚠️ **보안**

- `kis_devlp.yaml`과 `token_cache.json`은 절대 공개 저장소(GitHub 등)에 업로드하지 마세요.
- 두 파일 모두 `.gitignore`에 포함되어 있어 `git add .` 시 자동 제외됩니다.
- VS Code Source Control 패널에서 두 파일이 추적되지 않는지 확인하세요.
