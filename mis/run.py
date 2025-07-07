# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import signal
import subprocess
import sys

from mis.args import ARGS
from mis.constants import MIS_LOCAL_BIN_PATH
from mis.hub.envpreparation import environment_preparation


def main():
    environment_preparation(ARGS, True)
    process = None
    exit_code = 0

    def signal_handler(*_) -> None:
        raise KeyboardInterrupt("terminated")

    signal.signal(signal.SIGTERM, signal_handler)

    try:
        process = subprocess.Popen([f"{MIS_LOCAL_BIN_PATH}/bin/mis_launcher"])
        exit_code = process.wait()
    except KeyboardInterrupt:
        if process:
            process.send_signal(signal.SIGINT)
            exit_code = process.wait()
    finally:
        sys.exit(exit_code)


if __name__ == "__main__":
    main()