PYTHON_INTERPRETER = python3

environment:
	conda create --name mahalangur python=3
	@echo ">>> New conda env created. Activate with:\nconda activate mahalangur"

install_requirements:
	$(PYTHON_INTERPRETER) -m pip install -U pip setuptools wheel
	$(PYTHON_INTERPRETER) -m pip install -r requirements.txt

hdb_dataset:
	$(PYTHON_INTERPRETER) -m mahalangur.data.hdb

osm_metadata:
	$(PYTHON_INTERPRETER) -m mahalangur.data.osm

mahalangur_database:
	$(PYTHON_INTERPRETER) -m mahalangur.data.sqlitedb