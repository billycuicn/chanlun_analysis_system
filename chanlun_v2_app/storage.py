from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .models import Bi, KLine
from .paths import BI_CSV, CONFIG_JSON, HISTORY_JSON, KLINE_CSV, ensure_data_dir


KLINE_HEADER = ["时间", "开盘", "最高", "最低", "收盘", "成交量"]
BI_HEADER = ["序号", "方向", "起点时间", "终点时间", "K线数", "起点价", "终点价", "标注"]


def load_klines(path: Path | None = None) -> list[KLine]:
    path = path or KLINE_CSV
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    klines = [
        KLine(
            dt=row["时间"],
            open=float(row["开盘"]),
            high=float(row["最高"]),
            low=float(row["最低"]),
            close=float(row["收盘"]),
            volume=float(row["成交量"]),
        )
        for row in rows
    ]
    return sorted(klines, key=lambda item: item.dt)


def save_klines(klines: list[KLine], path: Path | None = None) -> None:
    path = path or KLINE_CSV
    ensure_data_dir()
    merged = {item.dt: item for item in klines}
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(KLINE_HEADER)
        for item in sorted(merged.values(), key=lambda value: value.dt):
            writer.writerow([item.dt, item.open, item.high, item.low, item.close, item.volume])


def merge_klines(old: list[KLine], new: list[KLine]) -> list[KLine]:
    merged = {item.dt: item for item in old}
    for item in new:
        merged[item.dt] = item
    return sorted(merged.values(), key=lambda item: item.dt)


def load_bis(path: Path | None = None) -> list[Bi]:
    path = path or BI_CSV
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    bis = [
        Bi(
            index=int(row["序号"]),
            direction=row["方向"],
            start_dt=row["起点时间"],
            end_dt=row["终点时间"],
            kline_count=int(row["K线数"]),
            start_price=float(row["起点价"]),
            end_price=float(row["终点价"]),
            note=row.get("标注", ""),
        )
        for row in rows
    ]
    return sorted(bis, key=lambda item: item.index)


def save_bis(bis: list[Bi], path: Path | None = None, record_history: bool = True) -> None:
    path = path or BI_CSV
    ensure_data_dir()
    if record_history:
        record_bi_snapshot(load_bis(path))
    normalized = [
        Bi(
            index=index + 1,
            direction=item.direction,
            start_dt=item.start_dt,
            end_dt=item.end_dt,
            kline_count=item.kline_count,
            start_price=item.start_price,
            end_price=item.end_price,
            note=item.note,
        )
        for index, item in enumerate(bis)
    ]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(BI_HEADER)
        for item in normalized:
            writer.writerow(
                [
                    item.index,
                    item.direction,
                    item.start_dt,
                    item.end_dt,
                    item.kline_count,
                    item.start_price,
                    item.end_price,
                    item.note,
                ]
            )


def save_json(path: Path, payload: Any) -> None:
    ensure_data_dir()
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def load_config() -> dict:
    return load_json(CONFIG_JSON, {"obsidian_vault": ""})


def save_config(config: dict) -> dict:
    current = load_config()
    current.update(config)
    save_json(CONFIG_JSON, current)
    return current


def record_bi_snapshot(bis: list[Bi]) -> None:
    history = load_json(HISTORY_JSON, [])
    history.append([item.to_dict() for item in bis])
    save_json(HISTORY_JSON, history[-30:])


def undo_bis() -> dict:
    history = load_json(HISTORY_JSON, [])
    if not history:
        return {"undone": False, "message": "没有可撤销的画笔操作。"}
    previous = history.pop()
    save_json(HISTORY_JSON, history)
    restored = [Bi(**item) for item in previous]
    save_bis(restored, record_history=False)
    return {"undone": True, "message": "已撤销上一步画笔操作。"}
