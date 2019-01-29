# -*- coding: utf-8 -*-
import logging
from os import path
from pathlib import Path

import click
import geopandas as gpd
import numpy as np
import pandas as pd
import pygeoprocessing
import rasterio
import richdem
import salem  # noqa
import xarray as xr
from dotenv import find_dotenv, load_dotenv
from rasterio import mask


@click.group()
@click.pass_context
def cli(ctx):
    """ Runs data processing scripts to turn raw data from (../raw) into
        cleaned data ready to be analyzed (saved in ../processed).
    """
    logger = logging.getLogger(__name__)
    ctx.ensure_object(dict)
    ctx.obj['LOGGER'] = logger


@cli.command()
@click.pass_context
@click.argument('dem_fp', type=click.Path(exists=True))
@click.argument('watershed_fp', type=click.Path(exists=True))
@click.argument('cropped_dem_fp', type=click.Path())
def cropped_dem(ctx, dem_fp, watershed_fp, cropped_dem_fp):
    logger = ctx.obj['LOGGER']
    logger.info("Cropping DEM to watershed extent")
    with rasterio.open(dem_fp) as dataset:
        gser = gpd.read_file(watershed_fp).to_crs(dataset.crs)['geometry']
        out_image, out_transform = mask.mask(dataset, gser, crop=True)
        out_meta = dataset.meta
        out_meta.update({
            'driver': 'GTiff',
            'height': out_image.shape[1],
            'width': out_image.shape[2],
            'transform': out_transform
        })
        with rasterio.open(cropped_dem_fp, 'w', **out_meta) as out_dataset:
            out_dataset.write(out_image)
    logger.info("DONE")


@cli.command()
@click.pass_context
@click.argument('cropped_dem_fp', type=click.Path(exists=True))
@click.argument('filled_dem_fp', type=click.Path())
def filled_dem(ctx, cropped_dem_fp, filled_dem_fp):
    logger = ctx.obj['LOGGER']
    logger.info("Cropping DEM to watershed extent")
    with rasterio.open(cropped_dem_fp) as dataset:
        dem = dataset.read(1)
        rdem = richdem.rdarray(dem, no_data=dataset.nodata)
        filled_dem = richdem.FillDepressions(rdem)
        logger.info("Filled {} pixels".format(np.sum(filled_dem != rdem)))
        out_meta = dataset.meta
        with rasterio.open(filled_dem_fp, 'w', **out_meta) as out_dataset:
            out_dataset.write(filled_dem, indexes=1)
    logger.info("DONE")


@cli.command()
@click.pass_context
@click.argument('input_raster_fp', type=click.Path(exists=True))
@click.argument('reference_raster_fp', type=click.Path(exists=True))
@click.argument('output_raster_fp', type=click.Path())
def aligned_raster(ctx, input_raster_fp, reference_raster_fp,
                   output_raster_fp):
    logger = ctx.obj['LOGGER']
    logger.info("Aligning {} to {}".format(input_raster_fp,
                                           reference_raster_fp))
    with rasterio.open(reference_raster_fp) as reference_src:
        pygeoprocessing.align_and_resize_raster_stack(
            [input_raster_fp], [output_raster_fp], ['near'], reference_src.res,
            bounding_box_mode=reference_src.bounds,
            target_sr_wkt=reference_src.crs.to_string())
    logger.info("DONE")


@cli.command()
@click.pass_context
@click.argument('lc_to_cropf_fp', type=click.Path(exists=True))
@click.argument('aligned_lc_fp', type=click.Path(exists=True))
@click.argument('cropf_fp', type=click.Path())
def crop_factor(ctx, lc_to_cropf_fp, aligned_lc_fp, cropf_fp):
    logger = ctx.obj['LOGGER']
    logger.info("Computing crop factor from LC")
    lulc_cfactor_map = pd.read_csv(lc_to_cropf_fp,
                                   index_col=0).to_dict()['c_factor']

    with rasterio.open(aligned_lc_fp) as dataset:
        land_cover_arr = dataset.read(1)
        out_meta = dataset.meta
        out_dtype = rasterio.dtypes.float32
        out_meta.update({'dtype': out_dtype})
        with rasterio.open(cropf_fp, 'w', **out_meta) as out_dataset:
            crop_factor_arr = np.vectorize(
                lulc_cfactor_map.get)(land_cover_arr).astype(out_dtype)
            out_dataset.write(crop_factor_arr, indexes=1)
        logger.info("DONE")


@cli.command()
@click.pass_context
@click.argument('mfds_dir', type=click.Path(exists=True))
@click.argument('cropped_dem_fp', type=click.Path(exists=True))
@click.argument('cropped_ds_fp', type=click.Path())
def cropped_ds(ctx, mfds_dir, cropped_dem_fp, cropped_ds_fp):
    logger = ctx.obj['LOGGER']
    logger.info(
        "Cropping mfdataset in {} to watershed extent".format(mfds_dir))

    # we open a multi-file dataset with all `*.nc` files in the folder, and
    # pass `decode_times=False` since xarray cannot process time in the "months
    # since" format
    mfds = xr.open_mfdataset(path.join(mfds_dir, '*.nc'), decode_times=False)

    # drop unnecessary dimensions so that salem can understand the grid
    drop_dims = ['lon', 'lat', 'dummy', 'swiss_coordinates']
    rename_dims_map = {'chx': 'x', 'chy': 'y'}
    mfds = mfds.drop(drop_dims).rename(rename_dims_map)

    # set projection attribute to all data variables
    ds_src = 'epsg:21781'  # ugly hardcoded meteoswiss crs
    mfds.attrs['pyproj_srs'] = ds_src
    for data_var in list(mfds.data_vars):
        mfds[data_var].attrs['pyproj_srs'] = ds_src

    # open the DEM in xarray and preprocess it so that salem can understand
    # the grid (same as for the `mfds`)
    dem_ds = xr.open_rasterio(cropped_dem_fp)
    dem_ds = dem_ds.drop('band')
    dem_ds.attrs['pyproj_srs'] = 'epsg:2056'  # ugly hardcoded DEM crs

    # crop region of interest of the dataset and store it in a single `.nc`
    # file
    roi = mfds.salem.roi(dem_ds)
    roi.to_netcdf(cropped_ds_fp)

    logger.info("DONE")


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    cli()
