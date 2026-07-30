# KOSPI 쏠림 & 센티먼트 대시보드

> KB증권 이은택 이그전 기반 한국 주식시장 분석 대시보드

## 자동화
- **매일 KST 07:00** GitHub Actions 자동 실행
- 매일 아침 직전 거래일 공개 시장 데이터 수집
- KOSPI·S&P 500·VIX: Yahoo Finance 공개 차트 데이터
- Fear & Greed: CNN 공식 지표
- Equity Put/Call Ratio: Cboe 날짜별 Daily Market Statistics
- VIX와 Put/Call 차트는 최근 6개월 거래일별 시계열 표시
- GitHub Pages 자동 배포

## 주요 지표
| 지표 | 임계값 | 의미 |
|------|--------|------|
| 50일 이격도 | 130% 이상 | 과열 조정 빌미 |
| Market Breadth | 0% 위로 반전 | 랠리 종료 신호 |
| VIX | 20 돌파 | 경계 구간 |
| Fear & Greed | 75 이상 | 역발상 매도 고려 |
| 미국 10년물 | 5% 돌파 | 버블 붕괴 트리거 |

## 기술 스택
- HTML/CSS/JS (단일 파일)
- Chart.js 4.4.1
- SVG 커스텀 캔들차트 (한국식: 상승=빨강, 하락=파랑)
- GitHub Actions + GitHub Pages
