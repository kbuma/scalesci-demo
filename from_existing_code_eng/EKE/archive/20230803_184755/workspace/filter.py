from dataclasses import dataclass

@dataclass
class FilterData:
    order: int
    fs: float
    big_period_day: float
    small_period_day: float
    low_frequency: float
    high_frequency: float
