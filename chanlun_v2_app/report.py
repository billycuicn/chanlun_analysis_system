from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .analyzer import analyze_and_save
from .paths import DATA_DIR, ensure_data_dir
from .storage import load_bis, load_config, load_klines


def generate_report() -> dict:
    ensure_data_dir()
    klines = load_klines()
    bis = load_bis()
    result = analyze_and_save()
    now = datetime.now()
    filename = f"analysis_IM_30m_{now.strftime('%Y%m%d_%H%M')}.md"
    local_path = DATA_DIR / filename
    content = build_report_content(now, klines, bis, result)
    local_path.write_text(content, encoding="utf-8")
    obsidian_path = ""
    vault = load_config().get("obsidian_vault", "").strip()
    if vault:
        target_dir = Path(vault).expanduser() / "chanlun" / "analysis"
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"IM_30m_analysis_{now.strftime('%Y%m%d_%H%M')}.md"
        target.write_text(content, encoding="utf-8")
        obsidian_path = str(target)
    return {"local_path": str(local_path), "obsidian_path": obsidian_path}


def build_report_content(now: datetime, klines: list, bis: list, result: dict) -> str:
    latest = klines[-1] if klines else None
    summary = result.get("summary", {})
    segments = result.get("segments", [])
    zones = result.get("zhongshu", [])
    signals = result.get("signals", [])
    latest_zone = zones[-1] if zones else None
    recent_high = summary.get("最近高点")
    recent_low = summary.get("最近低点")
    lines = [
        "# 中证1000缠论分析报告",
        f"> 生成时间：{now.strftime('%Y-%m-%d %H:%M')} | 数据范围：最近{len(klines)}根K线",
        "",
        "---",
        "",
        "## 一、当前走势",
        "",
        summary.get("结构定位", "暂无结构。"),
        f"当前价：{latest.close:.2f} @ {latest.dt}" if latest else "当前价：暂无K线数据",
        f"当前笔：B{bis[-1].index}{bis[-1].direction}，{bis[-1].start_dt} → {bis[-1].end_dt}，{bis[-1].start_price:.2f} → {bis[-1].end_price:.2f}" if bis else "当前笔：暂无",
        "",
        "## 二、线段列表",
        "",
    ]
    if segments:
        for item in segments:
            amplitude = item["最高"] - item["最低"]
            if item["方向"] == "向下":
                amplitude = -amplitude
            lines.append(f"- {item['id']}（{item['方向']}）：{item['起点时间']} → {item['终点时间']}，幅度{amplitude:+.2f}点，区间[{item['最低']:.2f}, {item['最高']:.2f}]")
    else:
        lines.append("- 当前笔尚未构成线段，继续观察")
    lines.extend(["", "## 三、中枢列表", ""])
    if zones:
        for item in zones:
            lines.append(f"- {item['id']}（{item['类型']}）：{item['起点时间']} → {item['终点时间']}，区间[{item['ZD']:.2f}, {item['ZG']:.2f}]，来自{item['线段']}")
    else:
        lines.append("- 暂无中枢")
    lines.extend(["", "## 四、买卖点", ""])
    if signals:
        for item in signals:
            lines.append(f"- {item['类型']}：@ {item['价格']:.2f}，时间 {item['时间']}，状态：{item['状态']}")
    else:
        lines.append("- 暂无买卖点")
    lines.extend(["", "## 五、综合判断", ""])
    lines.append(f"- 结构定位：{summary.get('结构定位', '暂无')}")
    if recent_low:
        lines.append(f"- 最近低点：{recent_low['价格']:.2f} @ {recent_low['时间']}")
    if recent_high:
        lines.append(f"- 最近高点：{recent_high['价格']:.2f} @ {recent_high['时间']}")
    if latest_zone:
        lines.append(f"- 中枢上沿ZG：{latest_zone['ZG']:.2f}")
        lines.append(f"- 中枢下沿ZD：{latest_zone['ZD']:.2f}")
    lines.extend(["", "## 六、操作建议", ""])
    if latest_zone and latest:
        lines.append(f"- 观察信号：若价格站稳ZG {latest_zone['ZG']:.2f}，短线按偏强处理。")
        lines.append(f"- 风险参考：若跌破ZD {latest_zone['ZD']:.2f}，说明结构转弱。")
    else:
        lines.append("- 当前结构还不完整，先把笔画清楚，等线段和中枢出来后再做判断。")
    lines.append("- 风险提示：本报告只做结构分析，不等于自动下单建议。")
    lines.extend(["", "---", "", "*分析工具：chan_analyzer.py | 笔数据：csi852_bi.csv*"])
    return "\n".join(lines)
