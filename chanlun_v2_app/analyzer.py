from __future__ import annotations

from .models import Bi
from .paths import SEGMENTS_JSON, SIGNALS_JSON, ZHONGSHU_JSON
from .storage import load_bis, load_klines, save_json


def analyze_and_save() -> dict:
    bis = load_bis()
    if len(bis) < 3:
        result = {
            "segments": [],
            "zhongshu": [],
            "signals": [],
            "summary": {"message": f"笔数量不足（{len(bis)}笔），至少需要3笔才能识别线段"},
        }
        _save_result(result)
        return result
    segments = build_segments(bis)
    zhongshu = build_zhongshu(bis, segments)
    signals = build_signals(bis, segments, zhongshu)
    result = {"segments": segments, "zhongshu": zhongshu, "signals": signals, "summary": build_summary(bis, segments, zhongshu)}
    _save_result(result)
    return result


def build_segments(bis: list[Bi]) -> list[dict]:
    segments: list[dict] = []
    for i in range(len(bis) - 2):
        group = bis[i : i + 3]
        if not _directions_match_segment(group):
            continue
        overlap_low = max(group[0].low, group[2].low)
        overlap_high = min(group[0].high, group[2].high)
        if overlap_high < overlap_low:
            continue
        direction = "向上" if [item.direction for item in group] == ["下", "上", "下"] else "向下"
        segments.append(
            {
                "id": f"D{len(segments) + 1}",
                "方向": direction,
                "起点时间": group[0].start_dt,
                "终点时间": group[-1].end_dt,
                "起点价": group[0].start_price,
                "终点价": group[-1].end_price,
                "最高": max(item.high for item in group),
                "最低": min(item.low for item in group),
                "笔序号": [item.index for item in group],
                "重叠低点": overlap_low,
                "重叠高点": overlap_high,
            }
        )
    return segments


def build_zhongshu(bis: list[Bi], segments: list[dict]) -> list[dict]:
    zones: list[dict] = []
    for segment in segments:
        segment_indexes = set(segment["笔序号"])
        group = [item for item in bis if item.index in segment_indexes]
        if len(group) < 3:
            continue
        zd = max(item.low for item in group)
        zg = min(item.high for item in group)
        if zg < zd:
            continue
        zones.append(
            {
                "id": f"Z{len(zones) + 1}",
                "类型": "上升中枢" if segment["方向"] == "向上" else "下降中枢",
                "起点时间": group[0].start_dt,
                "终点时间": group[-1].end_dt,
                "ZD": zd,
                "ZG": zg,
                "线段": segment["id"],
                "笔序号": [item.index for item in group],
            }
        )
    return zones


def build_signals(bis: list[Bi], segments: list[dict], zhongshu: list[dict]) -> list[dict]:
    if not segments:
        return []
    latest_close = _latest_close()
    signals: list[dict] = []
    for segment in segments:
        group = [item for item in bis if item.index in set(segment["笔序号"])]
        if segment["方向"] == "向上":
            high_bi = max(group, key=lambda item: item.high)
            signals.append(_signal("一卖", high_bi.end_dt, high_bi.high, latest_close, "sell"))
            pullbacks = [item for item in group if item.direction == "下"]
            if pullbacks:
                second = pullbacks[-1]
                signals.append(_signal("二卖", second.end_dt, second.high, latest_close, "sell"))
        else:
            low_bi = min(group, key=lambda item: item.low)
            signals.append(_signal("一买", low_bi.end_dt, low_bi.low, latest_close, "buy"))
            rebounds = [item for item in group if item.direction == "上"]
            if rebounds:
                second = rebounds[-1]
                signals.append(_signal("二买", second.end_dt, second.low, latest_close, "buy"))
    if zhongshu:
        zone = zhongshu[-1]
        signals.append({"类型": "三买/三卖", "时间": zone["终点时间"], "价格": zone["ZG"], "状态": "待观察", "说明": "等待离开中枢后的回抽确认。"})
    return signals


def build_summary(bis: list[Bi], segments: list[dict], zhongshu: list[dict]) -> dict:
    last_bi = bis[-1] if bis else None
    latest_close = _latest_close()
    recent_high = max(bis[-5:], key=lambda item: item.high) if bis else None
    recent_low = min(bis[-5:], key=lambda item: item.low) if bis else None
    latest_zone = zhongshu[-1] if zhongshu else None
    if latest_zone and latest_close is not None:
        if latest_close > latest_zone["ZG"]:
            position = f"价格在中枢上沿{latest_zone['ZG']:.2f}上方，短线偏强。"
        elif latest_close < latest_zone["ZD"]:
            position = f"价格跌到中枢下沿{latest_zone['ZD']:.2f}下方，短线偏弱。"
        else:
            position = f"价格在中枢{latest_zone['ZD']:.2f}-{latest_zone['ZG']:.2f}之间震荡。"
    else:
        position = "当前笔尚未构成中枢，继续观察。"
    return {
        "当前笔": last_bi.to_dict() if last_bi else None,
        "最近线段方向": segments[-1]["方向"] if segments else "暂无线段",
        "最近高点": {"时间": recent_high.end_dt, "价格": recent_high.high} if recent_high else None,
        "最近低点": {"时间": recent_low.end_dt, "价格": recent_low.low} if recent_low else None,
        "结构定位": position,
    }


def _directions_match_segment(group: list[Bi]) -> bool:
    directions = [item.direction for item in group]
    return directions in (["下", "上", "下"], ["上", "下", "上"])


def _latest_close() -> float | None:
    klines = load_klines()
    return klines[-1].close if klines else None


def _signal(kind: str, dt: str, price: float, latest_close: float | None, side: str) -> dict:
    if latest_close is None:
        status = "待确认"
    elif side == "buy":
        status = "已触发" if latest_close > price else "待确认"
    else:
        status = "已触发" if latest_close < price else "待确认"
    return {"类型": kind, "时间": dt, "价格": price, "状态": status}


def _save_result(result: dict) -> None:
    save_json(SEGMENTS_JSON, result["segments"])
    save_json(ZHONGSHU_JSON, result["zhongshu"])
    save_json(SIGNALS_JSON, result["signals"])

