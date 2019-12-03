# Mahalangur: Statistical Insights on the Himalayas

## Project Organization

The repository is a Python project using the following folder structure:

    Mahalangur
    ├── LICENSE
    ├── README.md          <- The top-level README for developers using this project
    ├── Makefile           <- Makefile with commands like `make install_requirements`
    │
    ├── mahalangur
    │   ├── assets         <- Serialized models and reference data for application
    │   │
    │   ├── datasets
    │   │   ├── meta       <- Static metadata such as code tables and other reference
    │   │   ├── raw        <- The original, immutable data dump
    │   │   ├── interim    <- Intermediate data that has been processed
    │   │   └── processed  <- The final, canonical data used for modelling
    │   │
    │   ├── data           <- Code for downloading or generating data
    │   ├── features       <- Code to turn raw data into features for modelling
    │   ├── models         <- Code to train, test and evaluate models
    │   └── serve          <- Code for the interactive web application
    │
    ├── notebooks          <- Jupyter notebooks used for exploring/analysing the data and
    │                         for prototyping models
    │
    └── references         <- Data dictionaries, manuals and all other explanatory materials
