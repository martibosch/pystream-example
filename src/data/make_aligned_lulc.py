# -*- coding: utf-8 -*-
import logging
from os import path
from pathlib import Path

import click
import pygeoprocessing
import rasterio
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

    with rasterio.open(
            path.join(paths.processed_data_path,
                      'cropped_dem.tif')) as cropped_dem_src:
        pygeoprocessing.align_and_resize_raster_stack(
            [
                path.join(paths.external_data_path, 'g100_clc12_V18_5a',
                          'g100_clc12_V18_5.tif')
            ], [path.join(paths.interim_data_path, 'aligned_lc.tif')],
            ['near'], cropped_dem_src.res,
            bounding_box_mode=cropped_dem_src.bounds,
            target_sr_wkt=cropped_dem_src.crs.to_string())


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
