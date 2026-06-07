from __future__ import annotations

from .models import Bi
from .storage import load_bis, load_klines, save_bis


def create_bi(start_dt: str, end_dt: str, start_price: float, end_price: float, note: str = "") -> Bi:
    klines = load_klines()
    dt_to_index = {item.dt: index for index, item in enumerate(klines)}
    if start_dt not in dt_to_index or end_dt not in dt_to_index:
        raise ValueError("起点或终点时间不在K线数据中。")
    start_index = dt_to_index[start_dt]
    end_index = dt_to_index[end_dt]
    if start_index == end_index:
        raise ValueError("起点和终点不能是同一根K线。")
    if start_index > end_index:
        start_dt, end_dt = end_dt, start_dt
        start_price, end_price = end_price, start_price
        start_index, end_index = end_index, start_index
    kline_count = end_index - start_index + 1
    if kline_count < 5:
        raise ValueError(f"笔至少需要5根K线，当前只有{kline_count}根。")
    direction = "上" if end_price >= start_price else "下"
    bis = load_bis()
    if bis and bis[-1].end_dt != start_dt:
        raise ValueError("相邻笔必须共用端点，请从上一笔终点开始画。")
    bi = Bi(
        index=len(bis) + 1,
        direction=direction,
        start_dt=start_dt,
        end_dt=end_dt,
        kline_count=kline_count,
        start_price=start_price,
        end_price=end_price,
        note=note,
    )
    save_bis(bis + [bi])
    return load_bis()[-1]


def update_bi(index: int, note: str = "") -> Bi:
    bis = load_bis()
    for idx, item in enumerate(bis):
        if item.index == index:
            bis[idx] = Bi(
                index=item.index,
                direction=item.direction,
                start_dt=item.start_dt,
                end_dt=item.end_dt,
                kline_count=item.kline_count,
                start_price=item.start_price,
                end_price=item.end_price,
                note=note,
            )
            save_bis(bis)
            return load_bis()[idx]
    raise KeyError(f"找不到第{index}笔。")


def delete_bi(index: int) -> None:
    bis = [item for item in load_bis() if item.index != index]
    if len(bis) == len(load_bis()):
        raise KeyError(f"找不到第{index}笔。")
    save_bis(bis)

