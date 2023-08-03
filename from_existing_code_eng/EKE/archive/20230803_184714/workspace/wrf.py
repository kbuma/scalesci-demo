from dataclasses import dataclass
import xarray as xr

@dataclass
class WRFData:
    u_data: xr.Dataset
    v_data: xr.Dataset
    u_4d_full: xr.DataArray
    v_4d_full: xr.DataArray
    u_4d: xr.DataArray
    v_4d: xr.DataArray
    lat_index_south: int
    lat_index_north: int
    lon_index_west: int
    lon_index_east:
