"""Fetch verified public market data for the static dashboard."""
from __future__ import annotations

import datetime as dt
import json
import urllib.parse
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "market-data.js"
KST = dt.timezone(dt.timedelta(hours=9))
UA = "Mozilla/5.0"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA})


def get(url: str, headers: dict[str, str] | None = None) -> bytes:
    response = SESSION.get(url, headers=headers, timeout=45)
    response.raise_for_status()
    return response.content


def yahoo(symbol: str, range_: str = "1y") -> list[dict]:
    symbol = urllib.parse.quote(symbol, safe="")
    url = f"https://query2.finance.yahoo.com/v8/finance/chart/{symbol}?range={range_}&interval=1d"
    result = json.loads(get(url))["chart"]["result"][0]
    quote = result["indicators"]["quote"][0]
    rows = []
    for i, timestamp in enumerate(result["timestamp"]):
        values = {key: quote[key][i] for key in ("open", "high", "low", "close")}
        if any(value is None for value in values.values()):
            continue
        rows.append({"date": dt.datetime.fromtimestamp(timestamp, dt.timezone.utc).date().isoformat(),
                     **{key: round(value, 2) for key, value in values.items()}})
    if len(rows) < 50:
        raise RuntimeError(f"insufficient data: {len(rows)} rows")
    return rows


def cnn_fear_greed() -> dict:
    page = "https://www.cnn.com/markets/fear-and-greed"
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36"})
    page_response = session.get(page, timeout=45)
    page_response.raise_for_status()
    url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
    response = session.get(url, headers={"Referer": page}, timeout=45)
    response.raise_for_status()
    item = response.json()["fear_and_greed"]
    return {"value": round(float(item["score"]), 1), "rating": item["rating"],
            "as_of": item["timestamp"], "source": page}


def monthly_last(rows: list[dict], count: int = 6) -> list[dict]:
    months = {row["date"][:7]: row for row in rows}
    return [{"date": key, "value": months[key]["close"]} for key in sorted(months)[-count:]]


def high_gap(rows: list[dict], count: int = 24) -> list[dict]:
    points = []
    for i, row in enumerate(rows):
        high = max(item["high"] for item in rows[max(0, i - 251):i + 1])
        points.append({"date": row["date"], "close": round((row["close"] / high - 1) * 100, 1)})
    return monthly_last(points, count)


def build() -> dict:
    kospi, sp500, vix = yahoo("^KS11"), yahoo("^GSPC"), yahoo("^VIX", "6mo")
    latest, previous = kospi[-1], kospi[-2]
    ma50 = sum(row["close"] for row in kospi[-50:]) / 50
    return {
        "schema_version": 1, "generated_at": dt.datetime.now(KST).isoformat(timespec="seconds"),
        "status": "verified-public-sources",
        "kospi": {**latest, "as_of": latest["date"],
                  "change_pct": round((latest["close"] / previous["close"] - 1) * 100, 2),
                  "disparity_50": round(latest["close"] / ma50 * 100, 1), "candles": kospi,
                  "high_gap": high_gap(kospi),
                  "source": "https://finance.yahoo.com/quote/%5EKS11/history/"},
        "sp500": {"as_of": sp500[-1]["date"], "high_gap": high_gap(sp500),
                  "source": "https://finance.yahoo.com/quote/%5EGSPC/history/"},
        "vix": {"as_of": vix[-1]["date"], "value": vix[-1]["close"],
                "monthly": monthly_last(vix), "source": "https://finance.yahoo.com/quote/%5EVIX/history/"},
        "fear_greed": cnn_fear_greed(),
        "put_call": {"value": None, "as_of": None, "note": "Cboe 무료 최신 시계열 미제공",
                     "source": "https://www.cboe.com/us/options/market_statistics/"},
        "aaii": {"bull": None, "neutral": None, "bear": None, "as_of": None,
                 "note": "AAII 최신 설문은 구독 데이터", "source": "https://www.aaii.com/sentimentsurvey"},
    }


def validate(data: dict) -> None:
    if not 100 <= data["kospi"]["close"] <= 20000: raise ValueError("invalid KOSPI")
    if not 0 < data["vix"]["value"] < 150: raise ValueError("invalid VIX")
    if not 0 <= data["fear_greed"]["value"] <= 100: raise ValueError("invalid Fear & Greed")


if __name__ == "__main__":
    data = build(); validate(data)
    OUTPUT.write_text("window.MARKET_DATA=" + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    print(json.dumps({"generated_at": data["generated_at"], "kospi": data["kospi"]["close"],
                      "vix": data["vix"]["value"], "fear_greed": data["fear_greed"]["value"]}, ensure_ascii=False))
