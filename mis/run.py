# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import signal
import subprocess

from mis.args import ARGS
from mis.hub.envpreparation import environment_preparation


def main():
    environment_preparation(ARGS, True)
    process = None
    try:
        process = subprocess.Popen(["/usr/local/bin/mis_launcher"])
        process.wait()
    except KeyboardInterrupt:
        if process:
            process.send_signal(signal.SIGINT)
            process.wait()


if __name__ == "__main__":
    main()
