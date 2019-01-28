# -*- coding: utf-8 -*-
import logging
from os import path
from pathlib import Path

import click
import numpy as np
import pandas as pd
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

    lulc_cfactor_map = pd.read_csv(
        path.join(paths.external_data_path, 'lulc_to_crop_factor.csv'),
        index_col=0).to_dict()['c_factor']

    with rasterio.open(path.join(paths.interim_data_path,
                                 'aligned_lc.tif')) as dataset:
        land_cover_arr = dataset.read(1)
        out_meta = dataset.meta
        out_dtype = rasterio.dtypes.float32
        out_meta.update({'dtype': out_dtype})
        with rasterio.open(
                path.join(paths.processed_data_path, 'crop_factor.tif'), 'w',
                **out_meta) as out_dataset:
            crop_factor_arr = np.vectorize(
                lulc_cfactor_map.get)(land_cover_arr).astype(out_dtype)
            out_dataset.write(crop_factor_arr, indexes=1)


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
