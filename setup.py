#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
from setuptools import find_packages, setup

import notenbildung
from notenbildung.version import *

NVOPackage = GitVersion('.')

setup(
    name='notenbildung',
    version=notenbildung.__version__,
    description='notentransparenz',
    url='https://github.com/tna76874/notentransparenz.git',
    author='lmh',
    author_email='',
    license='BSD 2-clause',
    packages=find_packages(),
    install_requires=[
        "numpy",
        "pandas",
        "datetime",
        "matplotlib",
    ],
    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',  
        'Operating System :: POSIX :: Linux',        
        'Programming Language :: Python :: 3.9',
    ],
    python_requires=">=3.8",
    entry_points={
        'console_scripts': [
            'notenbildung = notenbildung.cli:main',
        ],
    },
)
