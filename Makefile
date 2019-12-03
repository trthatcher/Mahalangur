PYTHON_INTERPRETER = python3

environment:
	conda create --name mahalangur python=3
	@echo ">>> New conda env created. Activate with:\nconda activate mahalangur"

install_requirements:
	$(PYTHON_INTERPRETER) -m pip install -U pip setuptools wheel
	$(PYTHON_INTERPRETER) -m pip install -r requirements.txt