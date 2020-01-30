# Tests

There are two types of tests which can be run for MaaS: 1) project testing and 2) application testing.

Project testing is lightweight and should at minimum be run before pushing any new model metadata files.

Application testing has more overhead associated with it, and therefore needs to be run when making changes to the MaaS API.

## Project testing

Project level tests are found in the `/tests` directory and can be run using `pytest` by simply running `pytest tests` from your CLI. These tests focus on ensuring metadata format compliance and other basic project level functionality.

## Application testing

These tests are found in `REST-Server/tests`. These are managed through `tox` and `nose`. The configuration for these tests can be found in the `tox.ini` file at the top level of the `REST-Server` directory. 

Tox creates a virtual environment using `REST-Server/test-requirements.txt` and `conda` (for the geo libraries). It then executes the tests in `REST-Server/tests` using `nose`.

The test suite founf in `REST-Server/tests` focuses on testing the **`exploration`** and **`concepts`** endpoints. It has some lightweight tests for the **`execution`** endpoints, but does not execute a model or try to retrieve results.

> **Note:** application tests assume that you have a local Redis and PostgreSQL instance running. They also assume that you have an Eidos concept mapping service available at `localhost:9000`. 


## Travis CI

Travis CI is managed through the `.travis.yml` configuration file at the top level of the project. This specifies a separate requirements file which can be found in `tests/test-requirements.txt`. These are minimal requirements only required to run the tests found in the top-level `tests` directory. 

Due to the requirement of having access to Redis, PostgreSQL, and the Eidos concept mapping service, application testing is not implemented with Travis CI at the moment. 