# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import json
import logging
import signal
import subprocess
import time
from dataclasses import dataclass
from http import HTTPStatus
from typing import Optional, List, AsyncGenerator

import httpx
from vllm import PoolingRequestOutput, RequestOutput
from vllm.config import VllmConfig, DecodingConfig, ModelConfig
from vllm.core.scheduler import SchedulerOutputs
from vllm.engine.protocol import EngineClient
from vllm.inputs.preprocess import InputPreprocessor
from vllm.lora.request import LoRARequest
from vllm.model_executor.layers.sampler import SamplerOutput
from vllm.transformers_utils.tokenizer import AnyTokenizer

from mis import constants, envs
from mis.logger import init_logger

logger = init_logger(__name__)

LOG_LEVEL_MAP = {
    "DEBUG": "Debug",
    "INFO": "Info",
    "WARNING": "Warning",
    "ERROR": "Error",
    "CRITICAL": "Error",  # mindie-service not have CRITICAL level
}

STOP_WAIT_TIMES = 5


@dataclass
class MindIEServiceArgs:
    vllm_config: VllmConfig
    address: str = "127.0.0.1"
    server_port: int = 1025
    manage_port: int = 1026
    metrics_port: int = 1027
    inter_comm_port: int = 1121
    multi_node_infer_port: int = 1120


class MindIEServiceStartError(Exception):
    pass


class MindIEServiceEngine(EngineClient):
    def __init__(self, mindie_args: MindIEServiceArgs):
        self.mindie_args = mindie_args
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
        return Exception("MindIEServiceEngine dead")

    def is_service_running(self):
        if self.process and not self.process.poll():
            return True
        return False

    def start_service(self):
        self.generate_config()

        self.process = subprocess.Popen(
            ["/bin/bash", "-c", "./bin/mindieservice_daemon"], cwd=constants.MINDIE_SERVICE_PATH
        )

        while True:
            time.sleep(10)
            try:
                if not self.is_service_running():
                    raise MindIEServiceStartError("mindie-service start error")
                r = httpx.get(f"http://{self.mindie_args.address}:{self.mindie_args.server_port}/v1/models")
                if r.status_code == HTTPStatus.OK:
                    logger.info("mindie-service start success")
                return
            except MindIEServiceStartError:
                raise
            except Exception:
                logging.info("waiting for mindie-service start")

    def stop_service(self):
        if self.is_service_running():
            logger.info("send stop message to mindie-service")
            self.process.send_signal(signal.SIGINT)

            for _ in range(STOP_WAIT_TIMES):
                time.sleep(10)
                if self.is_service_running():
                    logger.info("waiting for mindie-service exit")
                else:
                    logger.info("mindie-service exit success")
                    return
            logger.warning("mindie-service can not exit")

    def generate_config(self):
        config = {
            "Version": "1.0.0",
            "LogConfig": {
                "logLevel": LOG_LEVEL_MAP[envs.MIS_LOG_LEVEL],
                "logFileSize": 20,
                "logFileNum": 20,
                "logPath": "logs/mindie-server.log"
            },
            "ServerConfig": self.generate_server_config(),
            "BackendConfig": self.generate_backend_config(),
        }

        with open(constants.MINDIE_SERVICE_CONFIG_PATH, "w") as json_file:
            json.dump(config, json_file, ensure_ascii=False, indent=4)

    def generate_server_config(self):
        return {
            "ipAddress": self.mindie_args.address,
            "managementIpAddress": self.mindie_args.address,
            "port": self.mindie_args.server_port,
            "managementPort": self.mindie_args.manage_port,
            "metricsPort": self.mindie_args.metrics_port,
            "allowAllZeroIpListening": True,
            "maxLinkNum": 1000,
            "httpsEnabled": False,
            "fullTextEnabled": False,

            "tlsCaPath": "security/ca/",
            "tlsCaFile": ["ca.pem"],
            "tlsCert": "security/certs/server.pem",
            "tlsPk": "security/keys/server.key.pem",
            "tlsPkPwd": "security/pass/key_pwd.txt",
            "tlsCrlPath": "security/certs/",
            "tlsCrlFiles": ["server_crl.pem"],
            "managementTlsCaFile": ["management_ca.pem"],
            "managementTlsCert": "security/certs/management/server.pem",
            "managementTlsPk": "security/keys/management/server.key.pem",
            "managementTlsPkPwd": "security/pass/management/key_pwd.txt",
            "managementTlsCrlPath": "security/management/certs/",
            "managementTlsCrlFiles": ["server_crl.pem"],

            "kmcKsfMaster": "tools/pmt/master/ksfa",
            "kmcKsfStandby": "tools/pmt/standby/ksfb",

            "inferMode": "standard",
            "interCommTLSEnabled": False,
            "interCommPort": self.mindie_args.inter_comm_port,
            "interCommTlsCaPath": "security/grpc/ca/",
            "interCommTlsCaFiles": ["ca.pem"],
            "interCommTlsCert": "security/grpc/certs/server.pem",
            "interCommPk": "security/grpc/keys/server.key.pem",
            "interCommPkPwd": "security/grpc/pass/key_pwd.txt",
            "interCommTlsCrlPath": "security/grpc/certs/",
            "interCommTlsCrlFiles": ["server_crl.pem"],

            "openAiSupport": "vllm",
        }

    def generate_backend_config(self):
        return {
            "backendName": "mindieservice_llm_engine",
            "modelInstanceNumber": 1,
            "npuDeviceIds": [[i for i in range(self.mindie_args.vllm_config.parallel_config.world_size)]],
            "tokenizerProcessNumber": 8,
            "multiNodesInferEnabled": False,
            "multiNodesInferPort": self.mindie_args.multi_node_infer_port,
            "interNodeTLSEnabled": False,
            "interNodeTlsCaPath": "security/grpc/ca/",
            "interNodeTlsCaFiles": ["ca.pem"],
            "interNodeTlsCert": "security/grpc/cert/server.pem",
            "interNodeTlsPk": "security/grpc/keys/server.key.pem",
            "interNodeTlsPkPwd": "security/grpc/pass/mindie_server_key_pwd.txt",
            "interNodeTlsCrlPath": "security/grpc/certs/",
            "interNodeTlsCrlFiles": ["server_crl.pem"],
            "interNodeKmcKsfMaster": "tools/pmt/master/ksfa",
            "interNodeKmcKsfStandby": "tools/pmt/standby/ksfb",
            "ModelDeployConfig": {
                "maxSeqLen": self.mindie_args.vllm_config.model_config.max_model_len,
                "maxInputTokenLen": self.mindie_args.vllm_config.model_config.max_model_len,
                "truncation": False,
                "ModelConfig": [{"modelInstanceType": "Standard",
                                 "modelName": self.mindie_args.vllm_config.model_config.served_model_name,
                                 "modelWeightPath": self.mindie_args.vllm_config.model_config.model,
                                 "worldSize": self.mindie_args.vllm_config.parallel_config.world_size,
                                 "cpuMemSize": 5,
                                 "npuMemSize": -1,
                                 "backendType": "atb",
                                 "trustRemoteCode": False}]
            },
            "ScheduleConfig": {
                "templateType": "Standard",
                "templateName": "Standard_LLM",
                "cacheBlockSize": 128,
                "maxPrefillBatchSize": 50,
                "maxPrefillTokens": self.mindie_args.vllm_config.model_config.max_model_len,
                "prefillTimeMsPerReq": 150,
                "prefillPolicyType": 0,

                "decodeTimeMsPerReq": 50,
                "decodePolicyType": 0,

                "maxBatchSize": 200,
                "maxIterTimes": self.mindie_args.vllm_config.model_config.max_model_len,
                "maxPreemptCount": 0,
                "supportSelectBatch": False,
                "maxQueueDelayMicroseconds": 5000,
            },
        }

    def generate(self, *args, **kwargs) -> AsyncGenerator[RequestOutput, None]:
        pass

    def encode(self, *args, **kwargs) -> AsyncGenerator[PoolingRequestOutput, None]:
        pass

    async def abort(self, request_id: str) -> None:
        pass

    async def get_model_config(self) -> ModelConfig:
        """Get the model configuration of the vLLM engine."""
        return self.mindie_args.vllm_config.model_config

    async def get_decoding_config(self) -> DecodingConfig:
        pass

    async def get_input_preprocessor(self) -> InputPreprocessor:
        pass

    async def get_tokenizer(self, lora_request: Optional[LoRARequest] = None) -> AnyTokenizer:
        pass

    async def is_tracing_enabled(self) -> bool:
        pass

    async def do_log_stats(self,
                           scheduler_outputs: Optional[SchedulerOutputs] = None,
                           model_output: Optional[List[SamplerOutput]] = None) -> None:
        pass

    async def check_health(self) -> None:
        pass

    async def start_profile(self) -> None:
        pass

    async def stop_profile(self) -> None:
        pass

    async def reset_prefix_cache(self) -> None:
        pass

    async def add_lora(self, lora_request: LoRARequest) -> None:
        pass
