import numpy as np
import xarray as xr
from scipy import signal
import dask.array as da
from dask.distributed import Client, LocalCluster
from lat_lon import LatLonData
from filter import FilterData
from eke import EKEData
from wrf import WRFData

class WRFProcessor:
    def __init__(self, lat_lon_data: LatLonData, filter_data: FilterData):
        self.lat_lon_data = lat_lon_data
        self.filter_data = filter_data

    def butter_bandpass_filter(self, variable):
        print("Temporal filter...")
        b, a = signal.butter(self.filter_data.order, [self.filter_data.low_frequency, self.filter_data.high_frequency], btype='bandpass')
        filtered_variable = signal.lfilter(b, a, variable, axis=0)
        return filtered_variable

    def plot_eke(self, lat, eke_avg):
        fig, ax = plt.subplots()
        clevels = np.linspace(-8, 8, 33)
        cmap = plt.cm.PuOr
        units = '$\mathrm{m}^{2}$ $\mathrm{s}^{-2}$'
        p_levels = np.linspace(1000, 100, 19)
        X, Y = np.meshgrid(lat[:, 0], p_levels)
        plt.xlabel("Latitude")
        plt.ylabel("Pressure (hPa)")
        contours_fill = plt.contourf(X, Y, eke_avg, cmap=cmap, levels=clevels, extend="both")
        ax.set_xlim(-5, 25)
        plt.minorticks_on()
        plt.gca().invert_yaxis()
        cbar = plt.colorbar(contours_fill, shrink=.58, orientation='horizontal')
        ax.set_aspect(1. / ax.get_data_ratio())
        fig.savefig('WRF_TCM_M-O_2001-2010avg_' + scenario_type + '_EKE.pdf', bbox_inches='tight')

    def process_wrf_data(self, wrf_data: WRFData) -> EKEData:
        lat = wrf_data.lat
        lon = wrf_data.lon
        lat_index_north = wrf_data.lat_index_north
        lat_index_south = wrf_data.lat_index_south
        lon_index_west = wrf_data.lon_index_west
        lon_index_east = wrf_data.lon_index_east

        eke_list = []
        total_eke_list = []

        for year in range(2001, 2011):
            print('Year =', year)
            file_location = '/global/cscratch1/sd/ebercosh/WRF_TCM/' + scenario_type + '/' + str(year) + '/'

            u_data = xr.open_dataset(file_location + 'ua_' + scenario_type + '_' + str(year) + '.nc')
            v_data = xr.open_dataset(file_location + 'va_' + scenario_type + '_' + str(year) + '.nc')
            u_4d_full = u_data.ua
            v_4d_full = v_data.va
            u_4d = u_4d_full[:-120, :, :, :]
            v_4d = v_4d_full[:-120, :, :, :]

            u_temp_filt = self.butter_bandpass_filter(u_4d)
            v_temp_filt = self.butter_bandpass_filter(v_4d)

            uu = np.square(u_temp_filt)
            vv = np.square(v_temp_filt)

            uu_3d = np.mean(uu, axis=0)
            vv_3d = np.mean(vv, axis=0)

            uu_vv_3d = uu_3d + vv_3d

            uu_vv_2d = np.mean(uu_vv_3d[:, :, lon_index_west:lon_index_east + 1], axis=2)

            eke_2d = 0.5 * uu_vv_2d
            eke_list.append(eke_2d)

            eke_1d = 0.5 * np.mean(uu_vv_2d[:, lat_index_south:lat_index_north + 1] / g, axis=1)

            total_eke = np.trapz(eke_1d, dx=5000., axis=0)
            total_eke_list.append(total_eke)

        total_eke_avg = np.mean(total_eke_list, axis=0)
        eke_avg = np.mean(eke_list, axis=0)

        return EKEData(eke_list=eke_list, total_eke_list=total_eke_list, total_eke_avg=total_eke_avg, eke_avg=eke_avg)
