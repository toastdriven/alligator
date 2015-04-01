#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup


setup(
    name='alligator',
    version='0.10.0',
    description='Simple offline task queues.',
    author='Daniel Lindsley',
    author_email='daniel@toastdriven.com',
    url='http://github.com/toastdriven/alligator/',
    long_description=open('README.rst', 'r').read(),
    packages=[
        'alligator',
        'alligator/backends',
    ],
    include_package_data=True,
    zip_safe=False,
    scripts=[
        'bin/latergator.py',
    ],
    requires=[
        # 'six(>=1.4.0)',
    ],
    install_requires=[
        # 'six>=1.4.0',
    ],
    tests_require=[
        'pytest',
        'coverage',
        'pytest-cov',
        'redis',
        'beanstalkc',
        'PyYAML',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Environment :: No Input/Output (Daemon)',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Utilities'
    ],
)
