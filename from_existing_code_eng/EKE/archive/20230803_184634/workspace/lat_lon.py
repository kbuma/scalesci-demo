from dataclasses import dataclass
import numpy as np

@dataclass
class LatLonData:
    lat: np.ndarray
    lon: np.ndarray
    lat_index_north: int
    lat_index_south: int
    lon_index_west: int
    lon_index_east: int
