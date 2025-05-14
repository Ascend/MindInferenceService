# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import logging
import signal
import subprocess
import time
from dataclasses import dataclass
from http import HTTPStatus

import httpx
from loguru import logger

STOP_WAIT_TIMES = 5


@dataclass
class TEIServiceArgs:
    model_id: str
    port: int


class TEIServiceStartError(Exception):
    pass


class TEIServiceEngine:
    def __init__(self, tei_args: TEIServiceArgs):
        self.tei_args = tei_args
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
        return Exception("TEIServiceEngine dead")

    def is_service_running(self):
        if self.process and not self.process.poll():
            return True
        return False

    def start_service(self):
        self.process = subprocess.Popen(["/home/HwHiAiUser/.cargo/bin/text-embeddings-router",
                                         "--model-id", f"{self.tei_args.model_id}",
                                         "--hostname", "127.0.0.1", "--port", f"{self.tei_args.port}"])

        while True:
            logger.info("wait tei service ready...")
            time.sleep(3)
            try:
                if not self.is_service_running():
                    raise TEIServiceStartError("tei-service start error")
                r = httpx.get(f"http://127.0.0.1:{self.tei_args.port}/info", timeout=1)
                if r.status_code == HTTPStatus.OK:
                    logger.info("tei-service start success")
                    return
                else:
                    logger.warning(f"get tei service status code:{r.status_code}")
            except TEIServiceStartError:
                raise
            except Exception:
                logging.info("waiting for tei-service start")

    def stop_service(self):
        if self.is_service_running():
            logger.info("send stop message to tei-service")
            self.process.send_signal(signal.SIGINT)

            for _ in range(STOP_WAIT_TIMES):
                time.sleep(10)
                if self.is_service_running():
                    logger.info("waiting for tei-service exit")
                else:
                    logger.info("tei-service exit success")
                    return
            logger.warning("tei-service can not exit")
