# -*- coding: utf-8 -*-
import logging
from os import path
from pathlib import Path

import click
import numpy as np
import rasterio
import richdem
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
                      'cropped_dem.tif')) as dataset:
        dem = dataset.read(1)
        rdem = richdem.rdarray(dem, no_data=dataset.nodata)
        filled_dem = richdem.FillDepressions(rdem)
        logger.info("Filled {} pixels".format(np.sum(filled_dem != rdem)))
        out_meta = dataset.meta
        with rasterio.open(
                path.join(paths.processed_data_path, 'filled_dem.tif'), 'w',
                **out_meta) as out_dataset:
            out_dataset.write(filled_dem, indexes=1)


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
