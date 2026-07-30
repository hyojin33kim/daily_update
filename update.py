"""Fetch verified public market data for the static dashboard."""
from __future__ import annotations

import datetime as dt
import json
import re
import urllib.parse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "market-data-history-6m.js"
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
    start = dt.datetime.now(KST).date() - dt.timedelta(days=183)
    url = f"https://production.dataviz.cnn.io/index/fearandgreed/graphdata/{start.isoformat()}"
    response = session.get(url, headers={"Referer": page}, timeout=45)
    response.raise_for_status()
    payload = response.json()
    item = payload["fear_and_greed"]
    history = payload["fear_and_greed_historical"]["data"]
    daily = [{"date": dt.datetime.fromtimestamp(row["x"] / 1000, dt.timezone.utc).date().isoformat(),
              "value": round(float(row["y"]), 1), "rating": row["rating"]}
             for row in history if row.get("x") is not None and row.get("y") is not None]
    if len(daily) < 80:
        raise RuntimeError(f"insufficient six-month CNN Fear & Greed rows: {len(daily)}")
    return {"value": round(float(item["score"]), 1), "rating": item["rating"],
            "as_of": item["timestamp"], "daily": daily, "source": page}


def monthly_last(rows: list[dict], count: int = 6) -> list[dict]:
    months = {row["date"][:7]: row for row in rows}
    return [{"date": key, "value": months[key]["close"]} for key in sorted(months)[-count:]]


def high_gap(rows: list[dict], count: int = 24) -> list[dict]:
    points = []
    for i, row in enumerate(rows):
        high = max(item["high"] for item in rows[max(0, i - 251):i + 1])
        points.append({"date": row["date"], "close": round((row["close"] / high - 1) * 100, 1)})
    return monthly_last(points, count)


def existing_put_call() -> dict[str, float]:
    if not OUTPUT.exists():
        return {}
    match = re.match(r"window\.MARKET_DATA=(.*);\s*$", OUTPUT.read_text(encoding="utf-8"))
    if not match:
        return {}
    try:
        rows = json.loads(match.group(1)).get("put_call", {}).get("daily", [])
        return {row["date"]: float(row["value"]) for row in rows}
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return {}


def fetch_cboe_ratio(day: dt.date) -> tuple[str, float] | None:
    url = f"https://www.cboe.com/markets/us/options/market-statistics/daily?dt={day.isoformat()}"
    response = requests.get(url, headers={"User-Agent": UA}, timeout=45)
    if not response.ok:
        return None
    match = re.search(r'EQUITY PUT/CALL RATIO[^0-9]{1,40}([0-9]+\.[0-9]+)', response.text)
    return (day.isoformat(), float(match.group(1))) if match else None


def cboe_put_call_history() -> list[dict]:
    """Maintain six calendar months of official daily Cboe Equity P/C data."""
    end = dt.datetime.now(KST).date() - dt.timedelta(days=1)
    start = end - dt.timedelta(days=183)
    values = {date: value for date, value in existing_put_call().items() if date >= start.isoformat()}
    missing = []
    day = start
    while day <= end:
        if day.weekday() < 5 and day.isoformat() not in values:
            missing.append(day)
        day += dt.timedelta(days=1)
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(fetch_cboe_ratio, day) for day in missing]
        for future in as_completed(futures):
            result = future.result()
            if result:
                values[result[0]] = result[1]
    rows = [{"date": date, "value": values[date]} for date in sorted(values)]
    if len(rows) < 80:
        raise RuntimeError(f"insufficient six-month Cboe Put/Call rows: {len(rows)}")
    return rows


def build() -> dict:
    kospi, sp500, vix = yahoo("^KS11"), yahoo("^GSPC"), yahoo("^VIX", "6mo")
    put_call = cboe_put_call_history()
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
                "daily": [{"date": row["date"], "value": row["close"]} for row in vix],
                "source": "https://finance.yahoo.com/quote/%5EVIX/history/"},
        "fear_greed": cnn_fear_greed(),
        "put_call": {"value": put_call[-1]["value"], "as_of": put_call[-1]["date"],
                     "daily": put_call, "kind": "Equity Put/Call Ratio",
                     "source": "https://www.cboe.com/markets/us/options/market-statistics/daily"},
        "aaii": {"bull": None, "neutral": None, "bear": None, "as_of": None,
                 "note": "AAII 최신 설문은 구독 데이터", "source": "https://www.aaii.com/sentimentsurvey"},
    }


def validate(data: dict) -> None:
    if not 100 <= data["kospi"]["close"] <= 20000: raise ValueError("invalid KOSPI")
    if not 0 < data["vix"]["value"] < 150: raise ValueError("invalid VIX")
    if not 0 <= data["fear_greed"]["value"] <= 100: raise ValueError("invalid Fear & Greed")
    if any(not 0 <= row["value"] <= 100 for row in data["fear_greed"]["daily"]):
        raise ValueError("invalid Fear & Greed history")


if __name__ == "__main__":
    data = build(); validate(data)
    OUTPUT.write_text("window.MARKET_DATA=" + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    print(json.dumps({"generated_at": data["generated_at"], "kospi": data["kospi"]["close"],
                      "vix": data["vix"]["value"], "fear_greed": data["fear_greed"]["value"]}, ensure_ascii=False))
