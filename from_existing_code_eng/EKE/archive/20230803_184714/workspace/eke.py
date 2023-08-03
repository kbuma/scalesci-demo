from dataclasses import dataclass
import numpy as np

@dataclass
class EKEData:
    eke_list: list[np.ndarray]
    total_eke_list: list[float]
    total_eke_avg: float
    eke_avg: np.ndarray
