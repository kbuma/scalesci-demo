from lat_lon import LatLonData
from filter import FilterData
from wrf import WRFData
from wrf_processor import WRFProcessor

def main():
    lat_lon_data = LatLonData(lat, lon, lat_index_north, lat_index_south, lon_index_west, lon_index_east)
    filter_data = FilterData(order=6, fs=1/6, big_period_day=5.0, small_period_day=3.0, low_frequency=0.008333333333333333, high_frequency=0.016666666666666666)
    wrf_data = WRFData(u_data, v_data, u_4d_full, v_4d_full, u_4d, v_4d, lat_index_south, lat_index_north, lon_index_west, lon_index_east)

    wrf_processor = WRFProcessor(lat_lon_data, filter_data)
    eke_data = wrf_processor.process_wrf_data(wrf_data)

    eke_avg = eke_data.eke_avg
    wrf_processor.plot_eke(lat, eke_avg)

if __name__ == "__main__":
    cluster = LocalCluster()
    client = Client(cluster)
    main()
