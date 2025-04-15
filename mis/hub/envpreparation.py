# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import os
import platform

import torch

import mis.constants as constants
import mis.envs as envs
from mis.logger import init_logger
from mis.args import GlobalArgs
from mis.hub.downloader import ModelerDownloader
from mis.llm.engines.config import ConfigParser

logger = init_logger(__name__)

arch = platform.machine()
cxx_abi = 1 if torch.compiled_with_cxx11_abi() else 0

toolkit_path = constants.ASCEND_TOOLKIT_PATH
nnal_atb_home_path = f"{constants.ASCEND_NNAL_PATH}/latest/atb/cxx_abi_{cxx_abi}"

mindie_rt_home = constants.MINDIE_RT_PATH
mindie_torch_path = constants.MINDIE_TORCH_PATH
mindie_service_path = constants.MINDIE_SERVICE_PATH
mindie_llm_path = constants.MINDIE_LLM_PATH

mindie_atb_path = constants.MINDIE_ATB_PATH

# environments those need to be appended, not to be overridden
APPENDABLE_ENVIRONMENTS = [
    "LD_LIBRARY_PATH",
    "PYTHONPATH",
    "PATH",
    "ASCEND_CUSTOM_OPP_PATH",
]

ascend_toolkit_envs = {
    "ASCEND_TOOLKIT_HOME": toolkit_path,

    "LD_LIBRARY_PATH": [f"{toolkit_path}/lib64",
                        f"{toolkit_path}/lib64/plugin/opskernel",
                        f"{toolkit_path}/lib64/plugin/nnengine",
                        f"{toolkit_path}/opp/built-in/op_impl/ai_core/tbe/op_tiling/lib/linux/{arch}",
                        f"{toolkit_path}/tools/aml/lib64",
                        f"{toolkit_path}/tools/aml/lib64/plugin", ],
    "PYTHONPATH": [f"{toolkit_path}/python/site-packages",
                   f"{toolkit_path}/opp/built-in/op_impl/ai_core/tbe", ],
    "PATH": [f"{toolkit_path}/bin",
             f"{toolkit_path}/compiler/ccec_compiler/bin",
             f"{toolkit_path}/tools/ccec_compiler/bin", ],

    "ASCEND_AICPU_PATH": toolkit_path,
    "ASCEND_OPP_PATH": f"{toolkit_path}/opp",
    "TOOLCHAIN_HOME": f"{toolkit_path}/toolkit",
    "ASCEND_HOME_PATH": toolkit_path,
}

nnal_envs = {
    "ATB_HOME_PATH": nnal_atb_home_path,

    "LD_LIBRARY_PATH": [f"{nnal_atb_home_path}/lib",
                        f"{nnal_atb_home_path}/examples",
                        f"{nnal_atb_home_path}/tests/atbopstest", ],
    "PATH": [f"{nnal_atb_home_path}/bin", ],

    # 加速库环境变量
    "ATB_STREAM_SYNC_EVERY_KERNEL_ENABLE": "0",  # 每个Kernel的Execute时就做同步
    "ATB_STREAM_SYNC_EVERY_RUNNER_ENABLE": "0",  # 每个Runner的Execute时就做同步
    "ATB_STREAM_SYNC_EVERY_OPERATION_ENABLE": "0",  # 每个Operation的Execute时就做同步
    "ATB_OPSRUNNER_SETUP_CACHE_ENABLE": "1",  # 是否开启SetupCache，当检查到输入和输出没有变化时，不做setup
    "ATB_OPSRUNNER_KERNEL_CACHE_TYPE": "3",  # 0:不开启 1:开启本地缓存 2:开启全局缓存 3:同时开启本地和全局缓存
    "ATB_OPSRUNNER_KERNEL_CACHE_LOCAL_COUNT": "1",  # 本地缓存个数，支持范围1~1024
    "ATB_OPSRUNNER_KERNEL_CACHE_GLOABL_COUNT": "5",  # 全局缓存个数，支持范围1~1024
    "ATB_OPSRUNNER_KERNEL_CACHE_TILING_SIZE": "10240",  # tiling默认大小，支持范围1~1073741824
    "ATB_WORKSPACE_MEM_ALLOC_ALG_TYPE": "1",  # 0:暴力算法 1:block分配算法 2:有序heap算法 3:引入block合并(SOMAS算法退化版)
    "ATB_WORKSPACE_MEM_ALLOC_GLOBAL": "0",  # 0:不开启 1:开启全局中间tensor内存分配
    "ATB_COMPARE_TILING_EVERY_KERNEL": "0",  # 每个Kernel运行后，比较运行前和后的NPU上tiling内容是否变化
    "ATB_HOST_TILING_BUFFER_BLOCK_NUM": "128",  # Context内部HostTilingBuffer块数，通常使用默认值即可，可配置范围：最小128，最大1024
    "ATB_DEVICE_TILING_BUFFER_BLOCK_NUM": "32",  # Context内部DeviceTilingBuffer块数，通常使用默认值即可，可配置范围：最小32，最大1024
    "ATB_SHARE_MEMORY_NAME_SUFFIX": "",  # 共享内存命名后缀，多用户同时使用通信算子时，需通过设置该值进行共享内存区分
    "ATB_LAUNCH_KERNEL_WITH_TILING": "1",  # tiling拷贝随算子下发功能开关
    "ATB_MATMUL_SHUFFLE_K_ENABLE": "1",  # Shuffle-K使能，默认开
    "ATB_RUNNER_POOL_SIZE": "64",  # 加速库runner池中可存放runner的个数，支持范围0~1024，为0时不开启runner池功能
    # 算子库环境变量
    "ASDOPS_HOME_PATH": nnal_atb_home_path,
    "ASDOPS_MATMUL_PP_FLAG": "1",  # 算子库开启使用PPMATMUL
    "ASDOPS_LOG_LEVEL": "ERROR",  # 算子库日志级别
    "ASDOPS_LOG_TO_STDOUT": "0",  # 算子库日志是否输出到控制台
    "ASDOPS_LOG_TO_FILE": "0",  # 算子库日志是否输出到文件
    "ASDOPS_LOG_TO_FILE_FLUSH": "0",  # 日志写文件是否刷新
    "ASDOPS_LOG_TO_BOOST_TYPE": "atb",  # 算子库对应加速库日志类型，默认atb
    "ASDOPS_LOG_PATH": "~",  # 算子库日志保存路径
    "ASDOPS_TILING_PARSE_CACHE_DISABLE": "0",  # 算子库tilingParse禁止进行缓存优化
    "LCCL_DETERMINISTIC": "0",  # LCCL确定性AllReduce(保序加)是否开启，0关闭，1开启。
}

mindie_envs = {
    "LD_LIBRARY_PATH": [f"{mindie_rt_home}/lib",
                        f"{mindie_torch_path}/lib",
                        f"{mindie_service_path}/lib",
                        f"{mindie_service_path}/lib/grpc",
                        f"{mindie_llm_path}/lib",
                        f"{mindie_llm_path}/lib/grpc", ],
    "PYTHONPATH": [f"{mindie_service_path}/bin",
                   f"{mindie_llm_path}",
                   f"{mindie_llm_path}/lib", ],
    "ASCEND_CUSTOM_OPP_PATH": [f"{mindie_rt_home}/ops/vendors/customize",
                               f"{mindie_rt_home}/ops/vendors/aie_ascendc", ],

    "ASCENDIE_HOME": f"{mindie_rt_home}",
    "TUNE_BANK_PATH": f"{mindie_rt_home}/aoe",

    "MINDIE_TORCH_HOME": mindie_torch_path,

    "MIES_INSTALL_PATH": mindie_service_path,
    "ATB_OPERATION_EXECUTE_ASYNC": "1",
    "TASK_QUEUE_ENABLE": "1",
    "HCCL_BUFFSIZE": "120",
    # mindie-service日志
    "MINDIE_LOG_TO_STDOUT": "0",
    "MINDIE_LOG_TO_FILE": "0",
    # 运行时日志
    "ASCEND_SLOG_PRINT_TO_STDOUT": "0",
    "ASCEND_GLOBAL_LOG_LEVEL": "3",
    "ASCEND_GLOBAL_EVENT_ENABLE": "0",
    # 加速库日志
    "ATB_LOG_TO_FILE": "0",
    "ATB_LOG_TO_FILE_FLUSH": "3",
    "ATB_LOG_TO_STDOUT": "0",
    "ATB_LOG_LEVEL": "ERROR",
    # OCK后处理日志
    "OCK_LOG_LEVEL": "ERROR",
    "OCK_LOG_TO_STDOUT": "0",

    "MINDIE_LLM_HOME_PATH": mindie_llm_path,
    "MINDIE_LLM_PYTHON_LOG_LEVEL": "ERROR",
    "MINDIE_LLM_PYTHON_LOG_TO_STDOUT": "0",
    "MINDIE_LLM_PYTHON_LOG_TO_FILE": "0",
    "MINDIE_LLM_PYTHON_LOG_PATH": f"{mindie_llm_path}/logs",
    "MINDIE_LLM_CONTINUOUS_BATCHING": "1",
    "MINDIE_LLM_RECOMPUTE_THRESHOLD": "0.5",
    "MINDIE_LLM_LOG_LEVEL": "ERROR",
    "MINDIE_LLM_LOG_TO_STDOUT": "0",
    "MINDIE_LLM_LOG_TO_FILE": "0",
}

mindie_atb_envs = {
    "LD_LIBRARY_PATH": [f"{mindie_atb_path}/lib", ],
    "PYTHONPATH": [mindie_atb_path, ],

    "ATB_SPEED_HOME_PATH": mindie_atb_path,

    "TASK_QUEUE_ENABLE": "1",  # 是否开启TaskQueue，该环境变量属于PyTorch
    "ATB_OPERATION_EXECUTE_ASYNC": "1",  # Operation 是否异步运行
    "ATB_CONTEXT_HOSTTILING_RING": "1",
    "ATB_CONTEXT_HOSTTILING_SIZE": "102400",
    "ATB_WORKSPACE_MEM_ALLOC_GLOBAL": "1",
    "ATB_USE_TILING_COPY_STREAM": "0",  # 是否开启双stream功能
    "ATB_OPSRUNNER_KERNEL_CACHE_LOCAL_COUNT": "1",  # 设置op runner的本地cache槽位数
    "ATB_OPSRUNNER_KERNEL_CACHE_GLOABL_COUNT": "16",  # 设置op runner的全局cache槽位数
}


def enable_envs(env_dicts: dict):
    for env, value in env_dicts.items():
        if env not in APPENDABLE_ENVIRONMENTS:
            os.environ[env] = str(value)
            continue

        if isinstance(value, list):
            for v in value:
                os.environ[env] = f"{str(v)}:{os.environ.get(env, '')}"
        else:
            os.environ[env] = f"{str(value)}:{os.environ.get(env, '')}"


def source_ascend_envs():
    os.environ["VLLM_PLUGINS"] = "ascend"
    os.environ["VLLM_LOGGING_LEVEL"] = envs.MIS_LOG_LEVEL

    enable_envs(ascend_toolkit_envs)
    enable_envs(nnal_envs)


def source_mindie_service_envs():
    os.environ["VLLM_PLUGINS"] = "ascend"
    os.environ["VLLM_LOGGING_LEVEL"] = envs.MIS_LOG_LEVEL

    enable_envs(ascend_toolkit_envs)
    enable_envs(nnal_envs)
    enable_envs(mindie_envs)
    enable_envs(mindie_atb_envs)


ENGINE_ENVS = {
    "vllm": source_ascend_envs,
    "mindie-service": source_mindie_service_envs
}


def environment_preparation(args: GlobalArgs, resolve_env: bool = False) -> GlobalArgs:
    """Do some preparations for mis
        include:
            - model-pre-downloading
            - model-preferred-config-resolve
            - set environment variables if needed
    """
    # preferred config
    configparser = ConfigParser(args)
    args = configparser.engine_config_loading()

    if args.served_model_name is None:
        args.served_model_name = args.model

    # download model
    args.model = ModelerDownloader.get_model_path(args.model)

    # source envs in main process
    if resolve_env:
        if args.engine_type in ENGINE_ENVS.keys():
            ENGINE_ENVS[args.engine_type]()
    else:
        quantization = args.engine_optimization_config.get("quantization") \
            if hasattr(args, "engine_optimization_config") else None
        if quantization is not None and quantization == "awq":
            from vllm.model_executor.layers.quantization.awq import AWQConfig
            logger.info("Ascend AWQ (Torch NPU) registered")
        elif quantization is not None and quantization == "compressed-tensors":
            from vllm.model_executor.layers.quantization.compressed_tensors.compressed_tensors import (
                CompressedTensorsConfig)
            logger.info("Ascend Compressed-Tensors (Torch NPU) registered")
        elif quantization is not None and quantization == "ms-model-slim":
            from vllm_ascend.quantization.quant_config import AscendQuantConfig
    return args
