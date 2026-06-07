from __future__ import annotations

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
KLINE_CSV = DATA_DIR / "csi852_30min.csv"
BI_CSV = DATA_DIR / "csi852_bi.csv"
SEGMENTS_JSON = DATA_DIR / "segments.json"
ZHONGSHU_JSON = DATA_DIR / "zhongshu.json"
SIGNALS_JSON = DATA_DIR / "signals.json"
CONFIG_JSON = DATA_DIR / "config.json"
HISTORY_JSON = DATA_DIR / "history.json"


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

