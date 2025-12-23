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
import signal
import subprocess
import sys

from mis.logger import init_logger, LogType

logger = init_logger(__name__, log_type=LogType.SERVICE)


def main() -> None:
    """The main function is responsible for starting and managing the launcher process.
    """
    process = None
    exit_code = 0

    def signal_handler(*_) -> None:
        logger.error("receive signal, terminated")
        raise KeyboardInterrupt("terminated")

    signal.signal(signal.SIGTERM, signal_handler)

    try:
        logger.info("start mis_launcher")
        command = [
            sys.executable, "-c",
            ("import sys; sys.path.insert(0, sys.argv[1]);"
             "from mis.llm.entrypoints.launcher import _run_server,"
             "environment_preparation, ARGS;"
             "import uvloop; args = environment_preparation(ARGS);"
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
