from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class KLine:
    dt: str
    open: float
    high: float
    low: float
    close: float
    volume: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Bi:
    index: int
    direction: str
    start_dt: str
    end_dt: str
    kline_count: int
    start_price: float
    end_price: float
    note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def high(self) -> float:
        return max(self.start_price, self.end_price)

    @property
    def low(self) -> float:
        return min(self.start_price, self.end_price)

