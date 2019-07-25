#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

requirements = ["Click>=6.0"]

setup_requirements = ["pytest-runner"]

test_requirements = ["pytest"]

setup(
    author="Johan Carlin",
    author_email="johan.carlin@gmail.com",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    description="Takes the drudgery out of bind-mounting volumes on Docker and Singularity",
    entry_points={"console_scripts": ["bindit=bindit.cli:main",
        "bindit_partial=bindit.partial:main"]},
    install_requires=requirements,
    license="MIT license",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="bindit",
    name="bindit",
    packages=find_packages(include=["bindit"]),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/jooh/bindit",
    version="0.2.0",
    zip_safe=False,
)
