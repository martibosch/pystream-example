.PHONY: clean all_datasets cropped_dem filled_dem aligned_lulc crop_factor \
   cropped_prec cropped_temp lint requirements sync_data_to_s3 sync_data_from_s3

#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
BUCKET = ceat-stream
PROFILE = ceat
PROJECT_NAME = pystream-example
PYTHON_INTERPRETER = python3
VIRTUALENV = conda

DEM = data/external/swissALTI_reduced_res_lv95_3.tif
WSHED = data/external/watershed/wshed.shp
CROPPED_DEM = data/processed/cropped_dem.tif
FILLED_DEM = data/processed/filled_dem.tif
LC = data/external/g100_clc12_V18_5a/g100_clc12_V18_5.tif
ALIGNED_LC = data/interim/aligned_lc.tif
LC_TO_CROPF = data/external/lulc_to_crop_factor.csv
CROPF = data/processed/crop_factor.tif
PREC_DIR = data/external/meteoswiss/monthly/prec
CROPPED_PREC = data/processed/cropped_prec.nc
TEMP_DIR = data/external/meteoswiss/monthly/temp_avg
CROPPED_TEMP = data/processed/cropped_temp.nc

#################################################################################
# COMMANDS                                                                      #
#################################################################################

## Install Python Dependencies
requirements: test_environment
ifeq (conda, $(VIRTUALENV))
	conda env update --name $(PROJECT_NAME) -f environment.yml
else
	$(PYTHON_INTERPRETER) -m pip install -U pip setuptools wheel
	$(PYTHON_INTERPRETER) -m pip install -r requirements.txt
endif

## Make Datasets
all_datasets: cropped_dem filled_dem aligned_lulc crop_factor cropped_prec cropped_temp

cropped_dem: requirements
	$(PYTHON_INTERPRETER) src/data/make_dataset.py cropped-dem $(DEM) $(WSHED) $(CROPPED_DEM)

filled_dem: $(CROPPED_DEM)
	$(PYTHON_INTERPRETER) src/data/make_dataset.py filled-dem $(CROPPED_DEM) $(FILLED_DEM)

aligned_lulc: $(CROPPED_DEM)
	$(PYTHON_INTERPRETER) src/data/make_dataset.py aligned-lc $(CROPPED_DEM) $(LC) $(ALIGNED_LC)

crop_factor: $(ALIGNED_LC)
	$(PYTHON_INTERPRETER) src/data/make_dataset.py crop-factor $(LC_TO_CROPF) $(ALIGNED_LC) $(CROPF)

cropped_prec: $(CROPPED_DEM)
	$(PYTHON_INTERPRETER) src/data/make_dataset.py cropped-ds $(PREC_DIR) $(CROPPED_DEM) $(CROPPED_PREC)

cropped_temp: $(CROPPED_DEM)
	$(PYTHON_INTERPRETER) src/data/make_dataset.py cropped-ds $(TEMP_DIR) $(CROPPED_DEM) $(CROPPED_TEMP)

## Delete all compiled Python files
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete

## Clean interim and processed data
clean_data:
	find data/interim/ ! -name '.gitkeep' -type f -exec rm -f {} +
	find data/interim/ ! -path data/interim/ -type d -exec rm -rf {} +
	find data/processed/ ! -name '.gitkeep' -type f -exec rm -f {} +
	find data/processed/ ! -path data/processed/ -type d -exec rm -rf {} +

## Lint using flake8
lint:
	flake8 src

## Upload Data to S3
sync_data_to_s3:
ifeq (default,$(PROFILE))
	aws s3 sync data/external s3://$(BUCKET)/data/external --exclude '.gitkeep'
	aws s3 sync data/raw s3://$(BUCKET)/data/raw --exclude '.gitkeep'
else
	aws s3 sync data/external s3://$(BUCKET)/data/external --profile $(PROFILE) --exclude '.gitkeep'
	aws s3 sync data/raw s3://$(BUCKET)/data/raw --profile $(PROFILE) --exclude '.gitkeep'
endif

## Download Data from S3
sync_data_from_s3:
ifeq (default,$(PROFILE))
	aws s3 sync s3://$(BUCKET)/data/external data/external
	aws s3 sync s3://$(BUCKET)/data/raw data/raw
else
	aws s3 sync s3://$(BUCKET)/data/external data/external --profile $(PROFILE)
	aws s3 sync s3://$(BUCKET)/data/raw data/raw --profile $(PROFILE)
endif

## Set up python interpreter environment
create_environment:
ifeq (conda,$(VIRTUALENV))
		@echo ">>> Detected conda, creating conda environment."
	conda env create --name $(PROJECT_NAME) -f environment.yml
		@echo ">>> New conda env created. Activate with:\nconda activate $(PROJECT_NAME)"
		@echo ">>> Registering environment as jupyter kernelspec"
	$(PYTHON_INTERPRETER) -m ipykernel install --user --name $(PROJECT_NAME) --display-name "Python ($(PROJECT_NAME))"
		@echo ">>> DONE"
else
	$(PYTHON_INTERPRETER) -m pip install -q virtualenv virtualenvwrapper
	@echo ">>> Installing virtualenvwrapper if not already intalled.\nMake sure the following lines are in shell startup file\n\
	export WORKON_HOME=$$HOME/.virtualenvs\nexport PROJECT_HOME=$$HOME/Devel\nsource /usr/local/bin/virtualenvwrapper.sh\n"
	@bash -c "source `which virtualenvwrapper.sh`;mkvirtualenv $(PROJECT_NAME) --python=$(PYTHON_INTERPRETER)"
	@echo ">>> New virtualenv created. Activate with:\nworkon $(PROJECT_NAME)"
endif

## Test python environment is setup correctly
test_environment:
ifeq (conda,$(VIRTUALENV))
ifneq (${CONDA_DEFAULT_ENV}, $(PROJECT_NAME))
	$(error Must activate `$(PROJECT_NAME)` environment before proceeding)
endif
endif
	$(PYTHON_INTERPRETER) test_environment.py

#################################################################################
# PROJECT RULES                                                                 #
#################################################################################



#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := help

# Inspired by <http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html>
# sed script explained:
# /^##/:
# 	* save line in hold space
# 	* purge line
# 	* Loop:
# 		* append newline + line to hold space
# 		* go to next line
# 		* if line starts with doc comment, strip comment character off and loop
# 	* remove target prerequisites
# 	* append hold space (+ newline) to line
# 	* replace newline plus comments by `---`
# 	* print line
# Separate expressions are necessary because labels cannot be delimited by
# semicolon; see <http://stackoverflow.com/a/11799865/1968>
.PHONY: help
help:
	@echo "$$(tput bold)Available rules:$$(tput sgr0)"
	@echo
	@sed -n -e "/^## / { \
		h; \
		s/.*//; \
		:doc" \
		-e "H; \
		n; \
		s/^## //; \
		t doc" \
		-e "s/:.*//; \
		G; \
		s/\\n## /---/; \
		s/\\n/ /g; \
		p; \
	}" ${MAKEFILE_LIST} \
	| LC_ALL='C' sort --ignore-case \
	| awk -F '---' \
		-v ncol=$$(tput cols) \
		-v indent=19 \
		-v col_on="$$(tput setaf 6)" \
		-v col_off="$$(tput sgr0)" \
	'{ \
		printf "%s%*s%s ", col_on, -indent, $$1, col_off; \
		n = split($$2, words, " "); \
		line_length = ncol - indent; \
		for (i = 1; i <= n; i++) { \
			line_length -= length(words[i]) + 1; \
			if (line_length <= 0) { \
				line_length = ncol - indent - length(words[i]) - 1; \
				printf "\n%*s ", -indent, " "; \
			} \
			printf "%s ", words[i]; \
		} \
		printf "\n"; \
	}' \
	| more $(shell test $(shell uname) = Darwin && echo '--no-init --raw-control-chars')
