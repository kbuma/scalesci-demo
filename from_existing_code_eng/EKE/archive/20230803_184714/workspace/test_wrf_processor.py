import numpy as np
import pytest
from lat_lon import LatLonData
from filter import FilterData
from wrf import WRFData
from wrf_processor import WRFProcessor

@pytest.fixture
def lat_lon_data():
    lat = np.array([0, 1, 2, 3, 4])
    lon = np.array([0, 1, 2, 3, 4])
    lat_index_north = 4
    lat_index_south = 0
    lon_index_west = 0
    lon_index_east = 4
    return LatLonData(lat, lon, lat_index_north, lat_index_south, lon_index_west, lon_index_east)

@pytest.fixture
def filter_data():
    return FilterData(order=6, fs=1/6, big_period_day=5.0, small_period_day=3.0, low_frequency=0.008333333333333333, high_frequency=0.016666666666666666)

@pytest.fixture
def wrf_data():
    u_data = None  # Replace with appropriate data
    v_data = None  # Replace with appropriate data
    u_4d_full = None  # Replace with appropriate data
    v_4d_full = None  # Replace with appropriate data
    u_4d = None  # Replace with appropriate data
    v_4d = None  # Replace with appropriate data
    lat_index_south = 0
    lat_index_north = 4
    lon_index_west = 0
    lon_index_east = 4
    return WRFData(u_data, v_data, u_4d_full, v_4d_full, u_4d, v_4d, lat_index_south, lat_index_north, lon_index_west, lon_index_east)

def test_butter_bandpass_filter(wrf_data, filter_data):
    wrf_processor = WRFProcessor(None, filter_data)
    filtered_variable = wrf_processor.butter_bandpass_filter(wrf_data.u_4d)
    assert filtered_variable.shape == wrf_data.u_4d.shape

def test_process_wrf_data(wrf_data, lat_lon_data, filter_data):
    wrf_processor = WRFProcessor(lat_lon_data, filter_data)
    eke_data = wrf_processor.process_wrf_data(wrf_data)
    assert len(eke_data.eke_list) == 10
    assert len(eke_data.total_eke_list) == 10
    assert eke_data.total_eke_avg.shape == ()
    assert eke_data.eke_avg.shape == (5, 5)
