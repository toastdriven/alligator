#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup


setup(
    name="alligator",
    version="1.0.0-alpha-2",
    description="Simple offline task queues.",
    author="Daniel Lindsley",
    author_email="daniel@toastdriven.com",
    url="http://github.com/toastdriven/alligator/",
    long_description=open("README.rst", "r").read(),
    packages=["alligator", "alligator/backends"],
    include_package_data=True,
    zip_safe=False,
    scripts=["bin/latergator.py"],
    requires=[],
    install_requires=[],
    tests_require=["pytest", "coverage", "pytest-cov", "redis", "boto"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Environment :: No Input/Output (Daemon)",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Topic :: Utilities",
    ],
)
