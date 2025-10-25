#!/usr/bin/env python
# coding=utf-8
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
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

    shutil.copytree(MIS_NAME, os.path.join(build_dir, MIS_NAME))

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
