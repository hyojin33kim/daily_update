"""
KOSPI 대시보드 자동 업데이트
GitHub Actions에서 매일 KST 07:00 실행
"""
import os, re, json, datetime, requests

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
HTML_FILE     = "index.html"
KST           = datetime.timezone(datetime.timedelta(hours=9))
TODAY         = datetime.datetime.now(KST)
TODAY_STR     = TODAY.strftime("%Y-%m-%d")
TODAY_KR      = TODAY.strftime("%Y년 %m월 %d일")

def fetch_data():
    print(f"[1] 데이터 수집 ({TODAY_STR})")
    if not ANTHROPIC_KEY:
        print("  ANTHROPIC_API_KEY 없음 → 더미 데이터")
        return dummy()

    prompt = f"""오늘 {TODAY_STR} 기준 데이터를 웹검색해서 JSON만 반환해줘.
마크다운 없이 순수 JSON만 출력:
{{
  "kospi":{{"date":"{TODAY_STR}","open":0,"high":0,"low":0,"close":0,"change_pct":0.0}},
  "vix":0.0, "fear_greed":0, "put_call_ratio":0.0,
  "sp500_breadth":0.0, "kospi_breadth":0.0,
  "aaii_bull":0, "aaii_neutral":0, "aaii_bear":0
}}
검색 항목: KOSPI 종가 {TODAY_STR}, VIX index today,
CNN Fear Greed Index today, CBOE Put Call Ratio today,
AAII investor sentiment survey latest"""

    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"Content-Type":"application/json",
                     "x-api-key":ANTHROPIC_KEY,
                     "anthropic-version":"2023-06-01"},
            json={"model":"claude-sonnet-4-6","max_tokens":1024,
                  "tools":[{"type":"web_search_20250305","name":"web_search"}],
                  "messages":[{"role":"user","content":prompt}]},
            timeout=90
        )
        r.raise_for_status()
        texts = [b["text"] for b in r.json().get("content",[]) if b.get("type")=="text"]
        raw   = re.sub(r"```\w*","","\n".join(texts)).strip()
        m     = re.search(r"\{[\s\S]*\}", raw)
        if not m: raise ValueError("JSON 없음")
        d = json.loads(m.group())
        k = d["kospi"]
        s = "▲" if k["change_pct"]>=0 else "▼"
        print(f"  ✓ KOSPI {k['close']:,.0f} ({s}{k['change_pct']:+.2f}%)")
        print(f"    VIX {d['vix']} | F&G {d['fear_greed']} | P/C {d['put_call_ratio']}")
        return d
    except Exception as e:
        print(f"  ✗ 실패({e}) → 더미 데이터")
        return dummy()

def dummy():
    return {
        "kospi":{"date":TODAY_STR,"open":5620,"high":5700,
                 "low":5550,"close":5593,"change_pct":-1.23},
        "vix":20.7,"fear_greed":68,"put_call_ratio":0.65,
        "sp500_breadth":-13.0,"kospi_breadth":-16.2,
        "aaii_bull":52,"aaii_neutral":24,"aaii_bear":24
    }

def kpi(html, label, val, sub):
    html = re.sub(
        rf'(<div class="kpi-label">{re.escape(label)}</div>\s*<div class="kpi-value [^"]*">)[^<]*(</div>)',
        rf'\g<1>{val}\g<2>', html)
    html = re.sub(
        rf'({re.escape(label)}.*?kpi-sub">)[^<]*(</div>)',
        rf'\g<1>{sub}\g<2>', html, flags=re.DOTALL)
    return html

def update_html(d):
    print("[2] HTML 업데이트")
    html = open(HTML_FILE, encoding="utf-8").read()
    k    = d["kospi"]
    s    = "▲" if k["change_pct"]>=0 else "▼"
    fg   = d["fear_greed"]
    zone = "극탐욕" if fg>=75 else "탐욕" if fg>=55 else "중립" if fg>=45 else "공포"

    # 타임스탬프 고정
    html = re.sub(r'(ts\.textContent=)[^;]*(;)',
                  f'\\1"{TODAY_KR} 07:00 자동업데이트"\\2', html)

    # Alert 배너
    alert = (f'KOSPI {TODAY_KR}: <strong>{k["close"]:,.0f}</strong>'
             f' ({s}{k["change_pct"]:+.2f}%) &nbsp;—&nbsp;'
             f'VIX <strong>{d["vix"]}</strong> &nbsp;—&nbsp;'
             f'F&amp;G <strong>{fg}({zone})</strong>')
    html = re.sub(r'(<div class="alert-dot"></div>\s*<span)[^<]*(</span>)',
                  f'\\g<1>{alert}\\g<2>', html, flags=re.DOTALL)

    # KPI 카드
    html = kpi(html, "KOSPI 현재가",
               f"{k['close']:,.0f}", f"{s}{k['change_pct']:+.2f}% ({TODAY_STR})")
    html = kpi(html, "KOSPI Breadth",
               f"{d['kospi_breadth']:+.1f}%", "쏠림 유지 = 랠리 에너지 잔존")
    html = kpi(html, "Fear &amp; Greed",
               str(fg), f"{zone} 구간 (75↑ 위험)")
    html = kpi(html, "VIX 변동성",
               str(d["vix"]), "30↑ 공포 / 20~30 경계 / 20↓ 안정")
    html = kpi(html, "P/C Ratio",
               str(d["put_call_ratio"]), "1↑ 공포 / 0.7↓ 낙관과잉")

    # 오늘 OHLC 캔들 추가
    ohlc = (f'\n      {{s:{k["open"]},e:{k["close"]},'
            f'n:1,v:0.010}},  // {TODAY_STR} 자동업데이트')
    html = re.sub(
        r'\s*\{s:\d+,e:\d+,n:1,v:0\.010\},\s*// \d{4}-\d{2}-\d{2} 자동업데이트',
        '', html)
    html = re.sub(r'(    \];\s*const out=\[\];)',
                  f'\n{ohlc}\n\\1', html)

    open(HTML_FILE,"w",encoding="utf-8").write(html)
    print(f"  ✓ 저장 완료")

if __name__ == "__main__":
    print("="*50)
    print(f"KOSPI 대시보드 자동업데이트 ({TODAY_KR})")
    print("="*50)
    data = fetch_data()
    update_html(data)
    print("="*50)
    print("완료!")
