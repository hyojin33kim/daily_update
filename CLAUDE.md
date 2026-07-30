# KOSPI 대시보드 프로젝트

## 프로젝트 목적
매일 한국 주식시장(KOSPI) 쏠림 현상과 투자심리를 자동으로 분석하는 대시보드.
KB증권 이은택 전략가의 이그전(이격도 기반) 분석 프레임워크 적용.

## 파일 구조
```
kospi-dashboard/
├── index.html          ← 메인 대시보드 (Chart.js + SVG 캔들차트)
├── update.py           ← 매일 데이터 수집 및 HTML 업데이트
├── CLAUDE.md           ← 이 파일 (Claude 컨텍스트)
└── .github/
    └── workflows/
        └── update.yml  ← GitHub Actions 스케줄러
```

## 대시보드 구성 (위→아래 순서)
1. **이그전 집중 가이드** - 5개 탭 (투자전략 가이드)
2. **KPI 5개** - KOSPI현재가, Breadth, F&G, VIX, P/C Ratio
3. **Market Breadth** - S&P500 vs KOSPI 52주 비교차트
4. **KOSPI 이평선 + 이격도** - SVG 캔들차트(1년) + 50일 이격도
5. **센티먼트 4종** - Fear&Greed게이지, VIX스파크라인, P/C바차트, AAII도넛

## 핵심 지표 및 임계값 (이그전 기준)
- **50일 이격도 130% 이상** = 과열 조정 빌미
- **Market Breadth 확산 전환** = 랠리 종료 신호 (가장 중요)
- **VIX 20 돌파** = 경계 구간
- **Fear&Greed 75 이상** = 극도 탐욕 (역발상 매도 고려)
- **미국 10년물 금리 5% 돌파** = 버블 붕괴 트리거

## 차트 기술 스택
- KOSPI 캔들차트: 순수 SVG (Chart.js 사용 안 함, 좌표 정밀 제어)
- 한국식 캔들: 상승=빨강(양봉), 하락=파랑(음봉)
- 이평선: MA3(황), MA5(녹), MA20(청), MA50(적)
- 나머지 차트: Chart.js 4.4.1

## 데이터 수집 방식
- 매일 KST 07:00에 `update.py`가 공개 시장 데이터를 수집
- KOSPI·S&P 500·VIX: Yahoo Finance 공개 차트 데이터
- Fear & Greed: CNN 공식 페이지와 JSON 데이터
- Equity Put/Call Ratio: Cboe Daily Market Statistics 날짜별 자료
- VIX·Put/Call 차트는 월별 집계 없이 거래일별 표시
- 실제 KOSPI OHLC로 이동평균과 50일 이격도 계산
- 검증 실패 시 더미 데이터를 생성하지 않고 워크플로를 실패 처리
- 무료 최신 자료가 없는 AAII는 `N/A` 표시

## update.py 수정 시 주의사항
- HTML 파일 직접 정규식으로 업데이트
- KPI 카드 클래스: kpi-value danger/warn/ok/blue/purple
- Alert 배너: class="alert-dot" 바로 다음 <span> 태그
- 타임스탬프: ts.textContent= 패턴으로 교체

## GitHub Actions
- 실행 시각: UTC 22:00 = KST 07:00
- 별도 API Secret 불필요
- 배포: GitHub Pages (main 브랜치 루트)
