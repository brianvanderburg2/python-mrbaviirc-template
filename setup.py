#!/usr/bin/env python

from setuptools import setup, find_namespace_packages

metadata = {}
with open("mrbaviirc/template/_version.py") as handle:
    exec(handle.read(), metadata)

setup(
    name="mrbaviirc.template",
    version=metadata["__version__"],
    description=metadata["__doc__"].strip(),
    author=metadata["__author__"],
    packages=find_namespace_packages()
)
