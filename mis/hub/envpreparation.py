# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import os
import platform
from typing import Optional

import torch

import mis.constants as constants
import mis.envs as envs
from mis.args import GlobalArgs
from mis.llm.engines.config import ConfigParser
from mis.logger import init_logger
from mis.utils.utils import ContainerIPDetector, get_model_path

logger = init_logger(__name__)

arch = platform.machine()
cxx_abi = 1 if torch.compiled_with_cxx11_abi() else 0

logger.info("The installation path for the Ascend package has been set "
            "according to the executing user")
toolkit_path = constants.ASCEND_TOOLKIT_PATH

nnal_atb_home_path = f"{constants.ASCEND_NNAL_PATH}/latest/atb/cxx_abi_{cxx_abi}"

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

    # Acceleration Library Environment Variables
    "ATB_STREAM_SYNC_EVERY_KERNEL_ENABLE": "0",  # Synchronize after each Kernel execution
    "ATB_STREAM_SYNC_EVERY_RUNNER_ENABLE": "0",  # Synchronize after each Runner execution
    "ATB_STREAM_SYNC_EVERY_OPERATION_ENABLE": "0",  # Synchronize after each Operation execution
    "ATB_OPSRUNNER_SETUP_CACHE_ENABLE": "1",  # Enable SetupCache to skip setup when inputs/outputs remain unchanged

    "ATB_OPSRUNNER_KERNEL_CACHE_TYPE": "3",
    # Cache mode: 0=Disabled, 1=Local cache only, 2=Global cache only, 3=Both local and global cache

    "ATB_OPSRUNNER_KERNEL_CACHE_LOCAL_COUNT": "1",  # Number of local cache entries (1-1024)
    "ATB_OPSRUNNER_KERNEL_CACHE_GLOABL_COUNT": "5",  # Number of global cache entries (1-1024)
    "ATB_OPSRUNNER_KERNEL_CACHE_TILING_SIZE": "10240",  # Default tiling size (1-1073741824)

    "ATB_WORKSPACE_MEM_ALLOC_ALG_TYPE": "1",
    # Memory allocation algorithm: # 0 Brute force, 1 Block allocation, 2 Ordered heap, 3 Block merging

    "ATB_WORKSPACE_MEM_ALLOC_GLOBAL": "0",
    # Enable global intermediate tensor memory allocation (0=Disabled, 1=Enabled)

    "ATB_COMPARE_TILING_EVERY_KERNEL": "0",  # Compare tiling content before and after each Kernel execution
    "ATB_HOST_TILING_BUFFER_BLOCK_NUM": "128",  # Number of HostTilingBuffer blocks (128-1024)
    "ATB_DEVICE_TILING_BUFFER_BLOCK_NUM": "32",  # Number of DeviceTilingBuffer blocks (32-1024)
    "ATB_SHARE_MEMORY_NAME_SUFFIX": "",  # Suffix for shared memory naming to avoid conflicts
    "ATB_LAUNCH_KERNEL_WITH_TILING": "1",  # Enable tiling copy with kernel launch
    "ATB_MATMUL_SHUFFLE_K_ENABLE": "1",  # Enable Shuffle-K optimization (default enabled)
    "ATB_RUNNER_POOL_SIZE": "64",  # Number of runners in the pool (0-1024, 0=disabled)

    # Operator Library Environment Variables
    "ASDOPS_HOME_PATH": nnal_atb_home_path,
    "ASDOPS_MATMUL_PP_FLAG": "1",  # Enable PP MATMUL in operator library
    "ASDOPS_LOG_LEVEL": "ERROR",  # Logging level for operator library
    "ASDOPS_LOG_TO_STDOUT": "0",  # Output logs to console (0=Disabled, 1=Enabled)
    "ASDOPS_LOG_TO_FILE": "0",  # Output logs to file (0=Disabled, 1=Enabled)
    "ASDOPS_LOG_TO_FILE_FLUSH": "0",  # Enable log file flushing (0=Disabled, 1=Enabled)
    "ASDOPS_LOG_TO_BOOST_TYPE": "atb",  # Logging type for operator library (default "atb")
    "ASDOPS_LOG_PATH": "~",  # Path to save operator library logs
    "ASDOPS_TILING_PARSE_CACHE_DISABLE": "0",  # Disable tiling parse cache optimization
    "LCCL_DETERMINISTIC": "0",  # Enable deterministic AllReduce (0=Disabled, 1=Enabled)
}


def _enable_envs(env_dicts: dict) -> None:
    for env, value in env_dicts.items():
        if env not in APPENDABLE_ENVIRONMENTS:
            os.environ[env] = str(value)
            logger.debug(f"Set environment variable {env} to {value}")
            continue

        if isinstance(value, list):
            for v in value:
                os.environ[env] = f"{str(v)}:{os.environ.get(env, '')}"
                logger.debug(f"Appended {v} to environment variable {env}")
        else:
            os.environ[env] = f"{str(value)}:{os.environ.get(env, '')}"
            logger.debug(f"Appended {value} to environment variable {env}")


def _source_ascend_envs() -> None:
    os.environ["VLLM_LOGGING_LEVEL"] = envs.MIS_LOG_LEVEL
    logger.debug(f"Set VLLM_LOGGING_LEVEL to {envs.MIS_LOG_LEVEL}")
    _enable_envs(ascend_toolkit_envs)
    logger.debug("Loaded Ascend toolkit environment variables")

    _enable_envs(nnal_envs)
    logger.debug("Loaded NNAL environment variables")


ENGINE_ENVS = {
    "vllm": _source_ascend_envs,
}


def _source_components_envs() -> None:
    for components_env in constants.SOURCE_COMPONENTS_ENVS:
        if components_env not in os.environ:
            os.environ[components_env] = "1"
            logger.debug(f"Set environment variable {components_env} to 1")


def _is_private_key_encrypted(key_file_path: str) -> bool:
    """Check if a PEM formatted private key file is encrypted

    Args:
        key_file_path (str): Path to the private key file

    Returns:
        bool: True if encrypted, False if not encrypted
    """
    if not os.path.isfile(key_file_path):
        logger.warning(f"SSL key file not found")
        return False

    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.serialization import load_pem_private_key

        with open(key_file_path, 'rb') as key_file:
            key_data = key_file.read()

        try:
            load_pem_private_key(key_data, password=None)
            return False  # Successfully loaded, indicating it is not encrypted
        except TypeError:
            return True  # Requires a password, indicating it is encrypted

    except Exception as e:
        logger.warning(f"Failed to parse SSL key file: {e}")
        return False


def _check_ssl_config(ssl_keyfile: Optional[str], ssl_certfile: Optional[str]) -> None:
    """Check SSL configuration to ensure that the necessary files are provided and
    that the private key is properly encrypted.

    Args:
        ssl_keyfile (str): Path to the SSL private key file.
        ssl_certfile (str): Path to the SSL certificate file.

    Returns:
        None
    """
    if not ssl_keyfile or not ssl_certfile:
        logger.warning("SSL not configured. To ensure security, "
                       "you must provide a certificate and encrypted private key.")
        return

    try:
        if _is_private_key_encrypted(ssl_keyfile):
            logger.info(f"SSL private key is encrypted!. You may need to provide a password for startup")
        else:
            logger.warning(f"SSL private key is not encrypted. "
                           f"The private key will be mounted in plain text, "
                           f"which poses a serious security risk. It is suggest to encrypt the private key.")

    except Exception as e:
        logger.warning(f"SSL configuration error: {e}")


def environment_preparation(args: GlobalArgs, resolve_env: bool = False) -> GlobalArgs:
    """Do some preparations for mis
        include:
            - model-preferred-config-resolve
            - set environment variables if needed
    """
    logger.info("Starting environment preparation")

    _source_components_envs()
    logger.info("Loaded component environment variables")

    ip_update = ContainerIPDetector.get_ip(args.host)
    if ip_update is None:
        logger.error(f"Unable to automatically detect Host IP. "
                     f"Please manually set the Host IP via the environment variable MIS_HOST.")
        raise RuntimeError("Host IP could not be detected automatically.")
    else:
        args.host = ip_update

    # preferred config
    configparser = ConfigParser(args)
    args = configparser.engine_config_loading()
    logger.debug("Loaded engine configuration")

    if args.served_model_name is None:
        args.served_model_name = args.model
        logger.info(f"Set served_model_name to {args.model}")

    args.model = get_model_path(args.model)
    logger.debug(f"Resolved model path")

    _check_ssl_config(args.ssl_keyfile, args.ssl_certfile)
    logger.debug("Checked SSL configuration")

    # source envs in main process
    if resolve_env:
        if args.engine_type in ENGINE_ENVS.keys():
            ENGINE_ENVS[args.engine_type]()
            logger.debug(f"Loaded environment variables for engine type {args.engine_type}")
    logger.info("Environment preparation completed")
    return args
