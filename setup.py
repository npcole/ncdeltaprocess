#!/usr/bin/env python3
# from distutils.core import setup
from setuptools import setup, find_packages

setup(
    name="ncdeltaprocess",
    version="0.1",
    description="A processor for Quilljs Delta Files.",
    author="Nicholas Cole",
    author_email="n@npcole.com",
    url="http://www.quillproject.net/",
    install_requires=['richtextpy'],
    packages=find_packages(),
    include_package_data=True,
    license='Private Code',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python :: 3',
    ],
    long_description="""This is the Quill Library database and document processor."""
)
