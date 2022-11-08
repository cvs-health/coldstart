# Copyright 2022 CVS Health and/or one of its affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# TODO: Add to PyPI
# TODO: Add pre-commit hooks with linting and formatting

# Imports
from setuptools import setup, find_packages

# Set constants
NAME = "coldstart"
# TODO: add automatic version bumping
VERSION = "0.1.0"
DESCRIPTION = "A package for automatic data curation and feature engineering"
with open("README.md") as f:
    LONG_DESCRIPTION, LONG_DESC_TYPE = f.read(), "text/markdown"
URL = "https://github.com/cvs-health/coldstart"
LICENSE = "Apache 2.0"
AUTHOR, AUTHOR_EMAIL = "Ferrante, Piero", "FerranteP@aetna.com"
PYTHON_REQ = ">=3.7"
PACKAGES = find_packages(exclude=["*.tests", "*.tests.*"])
REQUIREMENTS = [
    "numpy>=1.19.5",
    "pandas>=1.3.5",
    "pyarrow>=6.0.1",
    "joblib>=1.1.0",
    "tqdm>=4.64.0",
    "sqlalchemy>=1.4.27",
    "tenacity",
    "sqlalchemy-bigquery",
    # "dask>=2.11.0",
]

# Run setup
setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type=LONG_DESC_TYPE,
    url=URL,
    license=LICENSE,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    python_requires=PYTHON_REQ,
    packages=PACKAGES,
    install_requires=REQUIREMENTS,
    include_package_data=True,
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],
    test_suite="tests"
)

# Print snowman
snowman = """
     __
   _|==|_
    ('')___/
>--(`^^')--<
  (`^'^'`)
  `======'  **DS winter is coming!**
"""
print(snowman)
