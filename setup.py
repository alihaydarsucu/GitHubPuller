#!/usr/bin/env python3
from setuptools import setup, find_packages
import os

# README dosyasını oku
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Sürüm bilgisi
version = "1.0.0"

setup(
    name="github-puller",
    version=version,
    author="Ali Haydar Sucu",
    author_email="alihaydarsucu@gmail.com",
    description="Batch GitHub repository downloader application",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/alihaydarsucu/github-puller",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Version Control :: Git",
        "Environment :: X11 Applications :: GTK",
    ],
    python_requires=">=3.8",
    install_requires=[
        "PyGObject>=3.42.0",
    ],
    entry_points={
        "console_scripts": [
            "github-puller=src.app:main",
        ],
    },
    data_files=[
        ("share/applications", ["github-puller.desktop"]),
        ("share/icons/hicolor/scalable/apps", ["icons/github-puller.svg"]),
        ("share/metainfo", ["github-puller.metainfo.xml"]),
    ],
    include_package_data=True,
    zip_safe=False,
)