#!/usr/bin/env python
# coding=utf-8
"""
-------------------------------------------------------------------------
This file is part of the Mind Inference Service project.
Copyright (c) 2025 Huawei Technologies Co.,Ltd.

Mind Inference Service is licensed under Mulan PSL v2.
You can use this software according to the terms and conditions of the Mulan PSL v2.
You may obtain a copy of Mulan PSL v2 at:

         http://license.coscl.org.cn/MulanPSL2

THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
See the Mulan PSL v2 for more details.
-------------------------------------------------------------------------
"""
import os
import shutil
import zipapp

MIS_NAME = "mis"


def build_zipapp():
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    os.makedirs("dist", exist_ok=True)

    build_dir = "dist/build"
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(build_dir)

    shutil.copytree(MIS_NAME, os.path.join(build_dir, MIS_NAME), ignore=shutil.ignore_patterns("tests"))

    with open(os.path.join(build_dir, "__main__.py"), "w", encoding="utf-8") as f:
        f.write('''
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from mis.run import main

if __name__ == '__main__':
    main()
''')

    zipapp.create_archive(
        build_dir,
        target=f"dist/{MIS_NAME}.pyz",
        interpreter="/usr/bin/env python3"
    )
    if os.path.exists("dist/build"):
        shutil.rmtree("dist/build")


if __name__ == "__main__":
    build_zipapp()
