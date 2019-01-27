# -*- coding: utf-8 -*-
import logging
from os import path
from pathlib import Path

import click
import geopandas as gpd
import rasterio
from dotenv import find_dotenv, load_dotenv
from rasterio import mask

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

    with rasterio.open(
            path.join(paths.external_data_path,
                      'swissALTI_reduced_res_lv95_3.tif')) as dataset:
        gser = gpd.read_file(
            path.join(paths.external_data_path, 'watershed',
                      'wshed.shp')).to_crs(dataset.crs)['geometry']
        out_image, out_transform = mask.mask(dataset, gser, crop=True)
        out_meta = dataset.meta
        out_meta.update({
            'driver': 'GTiff',
            'height': out_image.shape[1],
            'width': out_image.shape[2],
            'transform': out_transform
        })
        with rasterio.open(
                path.join(paths.processed_data_path, 'cropped_dem.tif'), 'w',
                **out_meta) as out_dataset:
            out_dataset.write(out_image)


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
