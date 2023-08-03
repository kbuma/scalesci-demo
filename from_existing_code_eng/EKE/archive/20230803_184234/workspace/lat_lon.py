import wrf

def lat_lon(data):
    # get lat and lon values
    lat = wrf.getvar(data, "lat") # ordered lat, lon
    lon = wrf.getvar(data, "lon") # ordered lat, lon
    # get the cropping indices since we don't want the lat/lon for the entire domain
    lon_index_west, lat_index_south = wrf.ll_to_xy(data,-10.,-40., meta=False) # 10S, 40W
    lon_index_east, lat_index_north = wrf.ll_to_xy(data,40.,30., meta=False) # 40N, 30E
    lat_crop = lat.values[lat_index_south:lat_index_north+1,lon_index_west:lon_index_east+1]
    lon_crop = lon.values[lat_index_south:lat_index_north+1,lon_index_west:lon_index_east+1]
    # get more zoomed in cropping indices
    lon_west = -20. # 20W
    lon_east = 20. # 20E
    lat_north = 20. # 20N
    lat_south = 0. # 0N
    lat_index_north = np.argmin((np.abs(lat_crop - lat_north)), axis=0)[0]
    lat_index_south = np.argmin((np.abs(lat_crop - lat_south)), axis=0)[0] 
    lon_index_west = (np.abs(lon_crop - lon_west)).argmin() 
    lon_index_east = (np.abs(lon_crop - lon_east)).argmin() 

    return lat_crop, lon_crop, lat_index_north, lat_index_south, lon_index_west, lon_index_east
