# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2025. All rights reserved.
import logging
import os
import signal
import subprocess
import time
from dataclasses import dataclass
from http import HTTPStatus

import httpx
from loguru import logger

STOP_WAIT_TIMES = 5


@dataclass
class ClipServiceArgs:
    config_path: str
    port: int


class ClipServiceStartError(Exception):
    pass


class ClipServiceEngine:
    def __init__(self, clip_args: ClipServiceArgs):
        self.clip_args = clip_args
        self.process = None
        self.start_service()

    def __del__(self):
        self.stop_service()

    @property
    def is_running(self) -> bool:
        return self.is_service_running()

    @property
    def is_stopped(self) -> bool:
        return not self.is_service_running()

    @property
    def errored(self) -> bool:
        return False

    @property
    def dead_error(self) -> BaseException:
        return Exception("ClipServiceEngine dead")

    def is_service_running(self):
        if self.process and not self.process.poll():
            return True
        return False

    def start_service(self):
        config_path = os.getenv("CLIP_CONFIG_PATH", "")
        if not config_path or not os.path.exists(config_path):
            logger.error(f"config path:{config_path} not exist, start service failed")
            return

        self.process = subprocess.Popen(["/usr/bin/python3", "-m", "clip_server", config_path])
        while True:
            logger.info("wait clip service ready...")
            time.sleep(3)
            try:
                if not self.is_service_running():
                    raise ClipServiceStartError("clip-service start error")
                r = httpx.get(f"http://127.0.0.1:{self.clip_args.port}/", timeout=3)
                if r.status_code == HTTPStatus.OK:
                    logger.info("clip-service start success")
                return
            except ClipServiceStartError:
                raise
            except Exception:
                logging.info("waiting for clip-service start")

    def stop_service(self):
        if self.is_service_running():
            logger.info("send stop message to clip-service")
            self.process.send_signal(signal.SIGINT)

            for _ in range(STOP_WAIT_TIMES):
                time.sleep(10)
                if self.is_service_running():
                    logger.info("waiting for clip-service exit")
                else:
                    logger.info("clip-service exit success")
                    return
            logger.warning("clip-service can not exit")
