PYTHON_INTERPRETER = python3

environment:
	conda create --name mahalangur python=3
	@echo ">>> New conda env created. Activate with:\nconda activate mahalangur"

install_requirements:
	$(PYTHON_INTERPRETER) -m pip install -U pip setuptools wheel
	$(PYTHON_INTERPRETER) -m pip install -r requirements.txt

data_hdb:
	$(PYTHON_INTERPRETER) -m mahalangur.data.hdb

feature_peaks:
	$(PYTHON_INTERPRETER) -m mahalangur.features.peaks

database_mahalangur:
	$(PYTHON_INTERPRETER) -m mahalangur.data.db

model_rf:
	$(PYTHON_INTERPRETER) -m mahalangur.models.rf


### Optional metadata update

osm_metadata:
	$(PYTHON_INTERPRETER) -m mahalangur.data.osm