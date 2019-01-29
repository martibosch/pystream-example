# -*- coding: utf-8 -*-
import logging
from os import path
from pathlib import Path

import click
import salem
import xarray as xr
from dotenv import find_dotenv, load_dotenv

from src import paths


@click.command()
# @click.argument('input_filepath', type=click.Path(exists=True))
# @click.argument('output_filepath', type=click.Path())
# def main(input_filepath, output_filepath)
def main():
    """ Runs data processing scripts to turn raw data from (../raw) into
        cleaned data ready to be analyzed (saved in ../processed).
    """
    logger = logging.getLogger(__name__)
    logger.info('making final data set from raw data')

    # we open a multi-file dataset with all `*.nc` files in the folder, and
    # pass `decode_times=False` since xarray cannot process time in the "months
    # since" format
    temp_ds = xr.open_mfdataset(
        path.join(paths.external_data_path, 'meteoswiss', 'monthly',
                  'temp_avg', '*.nc'), decode_times=False)

    # drop unnecessary dimensions so that salem can understand the grid
    drop_dims = ['lon', 'lat', 'dummy', 'swiss_coordinates']
    rename_dims_map = {'chx': 'x', 'chy': 'y'}
    temp_ds = temp_ds.drop(drop_dims).rename(rename_dims_map)

    # set projection attribute to all data variables
    ds_src = 'epsg:21781'  # ugly hardcoded meteoswiss crs
    temp_ds.attrs['pyproj_srs'] = ds_src
    for data_var in list(temp_ds.data_vars):
        temp_ds[data_var].attrs['pyproj_srs'] = ds_src

    # open the DEM in xarray and preprocess it so that salem can understand
    # the grid (same as for the `prec_ds`)
    dem_ds = xr.open_rasterio(
        path.join(paths.processed_data_path, 'cropped_dem.tif'))
    dem_ds = dem_ds.drop('band')
    dem_ds.attrs['pyproj_srs'] = 'epsg:2056'  # ugly hardcoded DEM crs

    # crop region of interest of the dataset and store it in a single `.nc`
    # file
    roi = temp_ds.salem.roi(dem_ds)
    roi.to_netcdf(path.join(paths.processed_data_path, 'cropped_temp.nc'))


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
