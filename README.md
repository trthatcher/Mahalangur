# Mahalangur: Summiting the Himalayas

**Mahalangur** is a small Python data science project that demonstrates how to design Scikit Learn models with a replicable project structure and how to create a simple web API and visualization in Flask. The project structure is largely based on the [Cookiecutter Data Science template](https://drivendata.github.io/cookiecutter-data-science/) and is outlined in the [Project Organization](#Project-Organization) section below.

## Visualization Demo

A [demo](https://mahalangur.pythonanywhere.com/) of the web interface for Mahalangur is hosted on PythonAnywhere:

<p align="center">
    <a href="https://mahalangur.pythonanywhere.com/">
    <img width="460" height="300" src="https://raw.githubusercontent.com/trthatcher/Mahalangur/assets/mahalangur.gif">
    </a>
</p>

## Acknowledgement

This project is named after the [Mahalangur Himal](https://en.wikipedia.org/wiki/Mahalangur_Himal), a section of the Himalayas that contains four of the six tallest mountains - including [Mount Everest](https://en.wikipedia.org/wiki/Mount_Everest). The expedition data is sourced from the [Himalayan Database](https://www.himalayandatabase.com/).

## License

This project is [ISC licensed](https://en.wikipedia.org/wiki/ISC_license). However, the climb data is sourced from the [Himalayan Database](https://www.himalayandatabase.com/) - please reach out to them if you wish to use their data for anything other than personal use.

## Project Organization

The repository is a Python project using the following folder structure:

    Mahalangur
    ├── LICENSE
    ├── README.md          <- The top-level README for developers using this project
    ├── Makefile           <- Makefile with commands like `make install_requirements`
    │
    ├── mahalangur
    │   ├── assets         <- Serialized models that are to be distributed with the
    │   │                     package
    │   │
    │   ├── data           <- Code for downloading or generating raw data
    │   │   ├── metadata   <- Static metadata such as code tables
    │   │   └── sql        <- Database definitions for SQLite datastore
    │   │
    │   ├── feat           <- Code to turn raw data into features for modelling
    │   ├── web            <- Flask API and web visualization code
    │   └── rfmodel.py     <- Code for training the model
    │
    ├── notebooks          <- Jupyter notebooks used for exploring/analysing the data and
    │                         for prototyping models
    │
    └── references         <- Data dictionaries, manuals and other explanatory materials

## Usage

### Installation

Clone Mahalangur to a folder of your choice:

```bash
git clone https://github.com/trthatcher/Mahalangur.git
cd Mahalangur
```

Next, create the `mahalangur` conda environment and install the requirements:

```bash
make environment
conda activate mahalangur
make install_requirements
```

This will install the package and its dependencies.

### Getting the Latest Data

By default, this package will download training data to a `.mahalangur` directory in your home directory. You can override this by setting a `MAHALANGUR_HOME` environment variable to the directory of your choosing. The Mahalangur data directory is laid out in the following way:

    .mahalangur
    │
    ├── data
    │   ├── raw            <- Raw data is downloaded to this directory
    │   ├── processed      <- Processed data is stored in this directory
    │   └── mahalangur.db  <- This database is created to store the processed data
    │
    ├── metadata           <- Processed metadata is output here
    │
    └── models             <- Serialized models are output here

To download the latest version of the Himalayan Database, run the following command in the terminal:

```bash
make dataset
```

This will populate the `.mahalangur/data` directory with updated extracts and transfer them into the `mahalangur.db` SQLite database. An updated model can be created by running:

```bash
make model_rf
```

The model will be stored in the `.mahalangur/models` directory. Note that if you would like to update the model used by the package, you will need to transfer it to the `assets` directory in the package.

### Starting the API

Once the package has been cloned and installed, you can run the web visualization locally with the following command:

```bash
make api
```
