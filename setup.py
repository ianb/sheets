#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'Click>=6.0',
    'astor',
    'watchdog',
    'python-rocksdb',
    'tempita',
    'webob',
    'matplotlib',
    'ws4py',
]

setup_requirements = [
    'pytest-runner',
    # TODO(ianb): put setup requirements (distutils extensions, etc.) here
]

test_requirements = [
    'pytest',
    # TODO: put package test requirements here
]

setup(
    name='sheets',
    version='0.1.0',
    description="Like an interpreter / spreadsheet",
    long_description=readme + '\n\n' + history,
    author="Ian Bicking",
    author_email='ian@ianbicking.org',
    url='https://github.com/ianb/sheets',
    packages=find_packages(include=['sheets']),
    entry_points={
        'console_scripts': [
            'sheets=sheets.cli:main'
        ]
    },
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords='sheets',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    setup_requires=setup_requirements,
)
