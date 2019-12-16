import datetime as dt
import numpy as np
#from .. import RAW_DIR
from netCDF4 import Dataset
import itertools

### Globals

#BEST_DIR = (RAW_DIR / 'best').resolve()
from pathlib import Path
BEST_DIR = Path('/home/tim/Projects/Mahalangur/mahalangur/datasets/raw/best/').resolve()

NC_PATH = (BEST_DIR / 'Complete_TMAX_Daily_LatLong1_2010.nc').resolve()

# Lat/Lon inclusion grid
GRID_POINTS = {
    31.5: [81.5],
    30.5: [80.5 + i for i in range(3)],
    29.5: [80.5 + i for i in range(5)],
    28.5: [81.5 + i for i in range(9)],
    27.5: [83.5 + i for i in range(7)],
    26.5: [86.5 + i for i in range(4)]
}


# 27,81,30,89

### Logic

#def get_grid_points(grid_points=GRID_POINTS):
#    points = {}
#    i = 1
#    for lat, lon_list in grid_points.items():
#        coords = [(lat, lon) for lon in lon_list]
#        for lon in lon_list:


def get_grid_map(grid_points=GRID_POINTS):
    i = 1
    grid_map = {}
    for lat, lon_list in grid_points.items():
        for lon in lon_list:
            grid_map[(lat,lon)] = i
            i += 1

    return grid_map



def get_temperatures(nc_path, grid_map):
    data = Dataset(nc_path, 'r')

    climate = data.variables['climatology'][:]

    lat_list = np.ma.getdata(data.variables['latitude' ][:])
    lon_list = np.ma.getdata(data.variables['longitude'][:])

    coord_mask = np.array([[(lat, lon) in grid_map for lon in lon_list]
                           for lat in lat_list])

    yyyy = np.ma.getdata(data.variables['year'       ][:]).astype(int)
    mm   = np.ma.getdata(data.variables['month'      ][:]).astype(int)
    dd   = np.ma.getdata(data.variables['day'        ][:]).astype(int)
    ddd  = np.ma.getdata(data.variables['day_of_year'][:]).astype(int)

    records = []
    for t, X_t in enumerate(data.variables['temperature']):
        date = dt.date(yyyy[t], mm[t], dd[t])

        X_0 = climate[ddd[t]-1]

        data_mask = np.logical_and(~np.ma.getmask(X_0), ~np.ma.getmask(X_t))

        i_range, j_range = np.where(np.logical_and(data_mask, coord_mask))

        for i, j in zip(i_range, j_range):
            point = grid_map.get((lat_list[i], lon_list[j]), None)
            records.append([
                point,
                date,
                X_0[i, j],
                X_t[i, j]
            ])

    data.close()

    return records


#data = Dataset(NC_PATH, 'r')
#climate = data.variables['climatology'][:]
#
#lat = np.ma.getdata(data.variables['latitude' ][:])
#lon = np.ma.getdata(data.variables['longitude'][:])
#
#lat_mask = np.logical_and(27 <= lat, lat <= 30)
#lon_mask = np.logical_and(81 <= lon, lon <= 89)
#
#latlon_mask = np.vstack(lat_mask) * np.hstack(lon_mask)
#
#yyyy = np.ma.getdata(data.variables['year'       ][:]).astype(int)
#mm   = np.ma.getdata(data.variables['month'      ][:]).astype(int)
#dd   = np.ma.getdata(data.variables['day'        ][:]).astype(int)
#ddd  = np.ma.getdata(data.variables['day_of_year'][:]).astype(int)

grid_map = get_grid_map(GRID_POINTS)
temperatures = get_temperatures(NC_PATH, grid_map)

