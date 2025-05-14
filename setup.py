# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import glob
import os
import shutil
from pathlib import Path
import logging

import yaml
from setuptools import setup
from Cython.Build import cythonize
from setuptools.extension import Extension

this_directory = Path(__file__).parent
build_folder = ('build/bdist*', 'build/lib*')
cache_folder = ('mis.egg-info',)


def get_ci_version_info():
    """
    Get version information from ci config file
    :return: version number
    """
    src_path = this_directory.parent
    ci_version_file = src_path.joinpath('mindxsdk', 'build', 'conf', 'config.yaml')
    version = '7.0.0'
    logging.info("get version from %s", ci_version_file)
    try:
        with open(ci_version_file, 'r') as f:
            config = yaml.safe_load(f)
            version = config['version']['mindx_sdk']
    except Exception as ex:
        logging.warning("get version failed, %s", str(ex))
    return version


def clean():
    """Clear local files"""
    for folder in cache_folder:
        if os.path.exists(folder):
            shutil.rmtree(folder)
    for pattern in build_folder:
        for name in glob.glob(pattern):
            if os.path.exists(name):
                shutil.rmtree(name)


def get_extensions():
    """
        Get all py files to be cythonize
        :return: Extension list
    """
    # generate Extension for every py file in mis
    extensions = []

    for mod in Path("mis").glob("**/*.py"):
        if mod.is_file():
            new_pkg = str(mod.parent).replace("/", ".")
            extensions.extend([Extension(f"{new_pkg}.{mod.stem}", [str(mod)])])

    return extensions


setup(
    name="mis",
    version=get_ci_version_info(),
    author="MindSDK",
    license="Apache 2.0",
    description="MindSDK Inference Server",
    ext_modules=cythonize(get_extensions()),
    python_requires=">=3.10, <3.12",
    entry_points={
        "console_scripts": [
            "mis_run=mis.run:main",
            "mis_launcher=mis.llm.entrypoints.launcher:main",
            "mis_tei=mis.emb.entrypoints.tei.launcher:main",
            "mis_clip=mis.emb.entrypoints.clip.launcher:main"
        ]
    }
)

clean()
