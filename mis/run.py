# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import signal
import subprocess
import sys

from mis.args import ARGS
from mis.hub.envpreparation import environment_preparation
from mis.logger import init_logger, LogType

logger = init_logger(__name__, log_type=LogType.SERVICE)


def main() -> None:
    """The main function is responsible for starting and managing the launcher process.
    """
    process = None
    exit_code = 0

    environment_preparation(ARGS, True)

    def signal_handler(*_) -> None:
        logger.error("receive signal, terminated")
        raise KeyboardInterrupt("terminated")

    signal.signal(signal.SIGTERM, signal_handler)

    try:
        logger.info(f"start mis_launcher")
        command = [
            sys.executable, "-c",
            ("import sys; sys.path.insert(0, sys.argv[1]);"
             "from mis.llm.entrypoints.launcher import _run_server,"
             "environment_preparation, ARGS;"
             "import uvloop; args = environment_preparation(ARGS, True);"
             "uvloop.run(_run_server(args))"),
            sys.argv[0]
        ]
        process = subprocess.Popen(command, shell=False)
        logger.info("mis_launcher started successfully")
        exit_code = process.wait()
        logger.info(f"mis_launcher exit with {exit_code}")
    except KeyboardInterrupt:
        if process:
            process.send_signal(signal.SIGINT)
            logger.info("Waiting for mis_launcher to complete")
            exit_code = process.wait()
            logger.info(f"mis_launcher completed with exit code {exit_code}")
    finally:
        logger.info(f"Exiting with code {exit_code}")
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
