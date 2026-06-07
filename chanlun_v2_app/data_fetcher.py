from __future__ import annotations

import json
import re
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .models import KLine
from .storage import load_klines, merge_klines, save_klines


SINA_KLINE_URL = "http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData"
SYMBOL = "sh000852"
PERIOD = 30
MIN_KLINES = 800


def fetch_sina_klines(datalen: int = MIN_KLINES) -> list[KLine]:
    params = urlencode({"symbol": SYMBOL, "scale": PERIOD, "ma": "no", "datalen": datalen})
    request = Request(
        f"{SINA_KLINE_URL}?{params}",
        headers={"Referer": "https://finance.sina.com.cn", "User-Agent": "Mozilla/5.0"},
    )
    with urlopen(request, timeout=15) as response:
        raw = response.read().decode("gbk", errors="replace")
    payload = _parse_payload(raw)
    klines = [
        KLine(
            dt=str(item["day"]),
            open=float(item["open"]),
            high=float(item["high"]),
            low=float(item["low"]),
            close=float(item["close"]),
            volume=float(item.get("volume") or 0),
        )
        for item in payload
    ]
    return sorted(klines, key=lambda item: item.dt)


def fetch_and_save(min_count: int = MIN_KLINES) -> dict:
    existing = load_klines()
    datalen = max(min_count, len(existing), MIN_KLINES)
    latest = fetch_sina_klines(datalen)
    merged = merge_klines(existing, latest)
    save_klines(merged)
    if len(merged) < min_count:
        raise RuntimeError(f"K线数量不足，需先采集数据：当前{len(merged)}根，要求{min_count}根")
    last = merged[-1]
    return {"count": len(merged), "latest_dt": last.dt, "latest_close": last.close}


def _parse_payload(raw: str) -> list[dict]:
    text = raw.strip()
    if not text:
        raise RuntimeError("新浪接口返回为空。")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        fixed = re.sub(r"([{,])(\w+):", r'\1"\2":', text)
        fixed = fixed.replace("'", '"')
        return json.loads(fixed)

