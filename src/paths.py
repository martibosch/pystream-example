import os
import pathlib

# Based on https://github.com/hackalog/bus_number/blob/master/src/paths.py

# Get the project directory as the parent of this module location
src_module_dir = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))
project_dir = pathlib.Path(os.path.dirname(os.path.abspath(__file__))).parent

data_path = project_dir / 'data'

external_data_path = data_path / 'external'
raw_data_path = data_path / 'raw'
interim_data_path = data_path / 'interim'
processed_data_path = data_path / 'processed'

model_path = project_dir / 'models'

reports_path = project_dir / 'reports'
figures_path = reports_path / 'figures'
