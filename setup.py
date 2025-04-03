# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
from setuptools import find_packages, setup

setup(
    name="mis",
    version="0.1.1",
    author="MindSDK",
    license="Apache 2.0",
    description="MindSDK Inference Server",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "openmind_hub"
    ],
    entry_points={}
)
