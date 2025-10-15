# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import os
from abc import ABC
from typing import Callable, Dict, Optional, Type, Union

import yaml

from mis.args import GlobalArgs
from mis.constants import HW_910B, MIS_ENGINE_TYPES, MIS_MODEL_LIST, MIS_CONFIGS_PATH, MIS_MAX_CONFIG_SIZE
from mis.logger import init_logger
from mis.utils.utils import ConfigChecker, get_soc_name

logger = init_logger(__name__)

MIS_CONFIG_DEFAULT = {
    "qwen3-8b": {HW_910B: "atlas800ia2-1x32gb-bf16-vllm-default"},
}

CHECKER_VLLM = {
    "dtype": {
        "type": "str_in",
        "valid_values": ("bfloat16",)
    },
    "tensor_parallel_size": {
        "type": "int",
        "valid_values": (1, 2, 4, 8)
    },
    "pipeline_parallel_size": {
        "type": "int",
        "valid_values": (1,)
    },
    "distributed_executor_backend": {
        "type": "str_in",
        "valid_values": ("mp",)
    },
    "max_num_seqs": {
        "type": "int",
        "min": 1,
        "max": 512
    },
    "max_model_len": {
        "type": "int",
        "min": 1,
        "max": 64000
    },
    "max_num_batched_tokens": {
        "type": "int",
        "min": 1,
        "max": 64000
    },
    "max_seq_len_to_capture": {
        "type": "int",
        "min": 1,
        "max": 64000
    },
    "gpu_memory_utilization": {
        "type": "float",
        "min": 0.0,
        "max": 1.0
    },
    "block_size": {
        "type": "int",
        "valid_values": (16, 32, 64, 128)
    },
    "swap_space": {
        "type": "int",
        "min": 0,
        "max": 1024,
    },
    "cpu_offload_gb": {
        "type": "int",
        "min": 0,
        "max": 1024
    },
    "scheduling_policy": {
        "type": "str_in",
        "valid_values": ("fcfs", "priority")
    },
    "num_scheduler_steps": {
        "type": "int",
        "min": 1,
        "max": 1024
    },
    "enable_chunked_prefill": {
        "type": "bool",
        "valid_values": (True, False)
    },
    "enable_prefix_caching": {
        "type": "bool",
        "valid_values": (True, False)
    },
    "multi_step_stream_outputs": {
        "type": "bool",
        "valid_values": (True, False)
    },
    "enforce_eager": {
        "type": "bool",
        "valid_values": (True, False)
    },
}


class AbsEngineConfigValidator(ABC):
    _engine_config_validation: Dict[str, Type["AbsEngineConfigValidator"]] = {}

    def __init__(self, config: Dict, checkers: Dict) -> None:
        """
        Initialize the AbsEngineConfigValidator class.
        :param config: The configuration dictionary.
        :param checkers: The checker dictionary OF selected engine.
        """
        self.config = config
        self.checkers = checkers
        diff_config = set(self.config.keys()) - set(self.checkers.keys())
        if diff_config:
            # Check if the backend configuration keywords for inference are updated with the version
            logger.debug(f"Configuration keys {diff_config} are not supported. ")
        self.config_update: Dict = {key: self.config[key] for key in self.config if key in self.checkers.keys()}

    @classmethod
    def register(cls, engine_type: str) -> Callable:
        """
        Register an engine configuration validator.
        :param engine_type: Engine type.
        """

        def decorator(subclass):
            cls._engine_config_validation[engine_type] = subclass
            return subclass

        return decorator

    @classmethod
    def get_validator(cls, engine_type: str) -> Type["AbsEngineConfigValidator"]:
        """
        Get the engine configuration validator.
        :param engine_type: Engine type.
        :return: Engine configuration validator class.
        """
        return cls._engine_config_validation.get(engine_type)

    def filter_and_validate_config(self) -> Dict:
        """
        Filter and validate the configuration.
        :return: Right configuration.
        """
        logger.debug("Filtering and validating configuration.")
        valid_config = {}
        for key, value in self.config_update.items():
            checker = self.checkers.get(key)

            is_valid = True
            if "valid_values" in checker:
                is_valid = ConfigChecker.is_value_in_enum(key, value, checker.get("valid_values"))
            elif "min" in checker and "max" in checker:
                is_valid = ConfigChecker.is_value_in_range(key, value, checker.get("min"), checker.get("max"))

            if is_valid:
                logger.debug(f"Configuration item {key} is valid.")
                valid_config[key] = value
        logger.debug("Configuration filtered and validated successfully.")
        return valid_config


@AbsEngineConfigValidator.register("vllm")
class VLLMEngineConfigValidator(AbsEngineConfigValidator):
    """
    VLLM engine configuration validator.
    """

    def __init__(self, config: Dict) -> None:
        """
        vLLM Engine configuration validator initialization.
        :param config: Configuration parameters.
        """
        super().__init__(config, CHECKER_VLLM)


class ConfigParser:
    def __init__(self, args: GlobalArgs) -> None:
        """
        Check all args are valid.
        :param args: global args
        """
        logger.debug(f"Initializing ConfigParser with args.")
        self.args = args
        self.args.engine_optimization_config = {}

        self._check_all_args_valid()

        self.model_type = self.args.model.split('/')[-1]
        self.model_folder_path = os.path.join(MIS_CONFIGS_PATH, self.model_type.lower())
        self.engine_type = self.args.engine_type
        self.mis_config = self.args.mis_config
        logger.debug(f"ConfigParser initialized successfully")

    @staticmethod
    def _config_attr_update(selected_engine_type: str, selected_engine_config: Dict) -> Dict:
        """
        Update the attributes of the selected engine.
        :param selected_engine_type: The type of the selected engine.
        :param selected_engine_config: The configuration of the selected engine.
        :return: updated config dictionary. 
        """
        logger.debug(f"Updating attributes for engine type: {selected_engine_type}.")
        validator_class = AbsEngineConfigValidator.get_validator(selected_engine_type)
        validator = validator_class(selected_engine_config.get(selected_engine_type))
        logger.debug(f"Attributes for engine type {selected_engine_type} updated successfully.")
        return validator.filter_and_validate_config()

    def engine_config_loading(self) -> GlobalArgs:
        """
        Obtain the engine configuration. If the parameters are successfully obtained, update the args.
        :return: Update global parameters
        """
        logger.debug("Loading engine configuration.")
        engine_optimization_config = self._load_config_from_file()
        if not engine_optimization_config or not self._is_config_valid(engine_optimization_config):
            logger.warning("Using default engine configuration.")
            return self.args

        engine_type_selected = engine_optimization_config.get("engine_type")
        self.args.engine_optimization_config = self._config_attr_update(engine_type_selected,
                                                                        engine_optimization_config)

        model_by_config = engine_optimization_config.get("model")
        self.args.model = model_by_config if model_by_config in MIS_MODEL_LIST else self.args.model
        self.args.engine_type = engine_type_selected
        logger.info("Engine configuration loaded successfully.")
        return self.args

    def _config_yaml_file_loading(self, config_file_path: str) -> Union[Dict, None]:
        """
        Load config file.
        :params config_file_path: config path
        :return: Parsed configuration dictionary if successful, None otherwise.
        """
        logger.debug(f"Loading configuration: {self.mis_config}.")
        try:
            current_user_id = os.getuid()
            path_stat = os.stat(config_file_path)
            path_owner_id = path_stat.st_uid
            if current_user_id != path_owner_id:
                logger.error(f"The configuration {self.mis_config} is not owned by the current user.")
                raise Exception("The configuration file is not owned by the current user.")

            if os.path.islink(config_file_path):
                logger.error(f"The configuration {self.mis_config} is a symbolic link.")
                raise Exception("The configuration file is a symbolic link.")

            file_size = os.path.getsize(config_file_path)
            if file_size > MIS_MAX_CONFIG_SIZE:
                logger.error(f"The size of the configuration {self.mis_config} exceeds 1MB.")
                raise Exception("The size of the configuration file exceeds 1MB.")

            with open(config_file_path, "r", encoding="utf-8") as file:
                config = yaml.safe_load(file)
                logger.info(f"Configuration {self.mis_config} loaded successfully.")

            return config

        except FileNotFoundError:
            logger.warning(f"Config {self.mis_config} not found. "
                         "The engine will be started with default parameters.")
            return None
        except (OSError, yaml.YAMLError) as e:
            logger.error(f"Failed to load configuration {self.mis_config}: {e}")
            raise e
        except Exception as e:
            logger.error(f"Unexpected error while loading configuration {self.mis_config}: {e}")
            raise e

    def _load_config_from_file(self) -> Optional[Dict]:
        """
        Loading the configuration from a specified YAML file.
        If the specified configuration file does not exist or the environment variable `MIS_CONFIG` is not set,
        the method will use the default configuration.

        :returns: A dictionary containing the configuration loaded from the YAML file,
        or `None` if no valid configuration is found.
        """
        logger.debug("Loading configuration from file.")
        if self.mis_config is None:
            logger.warning("The environment variable MIS_CONFIG is missed. "
                           "Please check if the environment variables is valid."
                           "The engine will be started with the default parameters.")
            self.mis_config = self._get_default_config()

        elif not os.path.exists(os.path.join(self.model_folder_path, self.mis_config + ".yaml")):
            logger.debug(f"Selected config {self.mis_config} does not exist."
                         f"The engine will be started with the default config.")
            self.mis_config = self._get_default_config()

        if self.mis_config is None:
            logger.warning("No valid configuration found. Using default parameters.")
            return None

        config_file_path = os.path.join(self.model_folder_path, self.mis_config + ".yaml")
        engine_optimization_config = self._config_yaml_file_loading(config_file_path)
        logger.debug("Configuration file loaded successfully.")
        return engine_optimization_config

    def _is_config_valid(self, config: Dict) -> bool:
        """
        Checks if the config is valid.
        :param config: Config to check.
        :return: True if the config is valid, False otherwise.
        """
        logger.debug("Validating configuration.")
        if config is None or not isinstance(config, dict):
            logger.debug(f"The YAML config file for {self.model_type} ({self.mis_config}) is invalid."
                         f"The engine will be started with the default parameters.")
            return False

        if config.get("engine_type") is None or config.get("model") is None:
            logger.debug(f"Please check if keywords engine_type and model in "
                         f"{self.model_type} ({self.mis_config}) YAML is complete."
                         f"The engine will be started with the default parameters.")
            return False

        engine_type = config.get("engine_type")
        if engine_type not in MIS_ENGINE_TYPES:
            logger.warning(f"engine_type in YAML config file must in {MIS_ENGINE_TYPES}")
            return False

        if config.get(engine_type) is None:
            logger.warning(f"Config of engine type {config.get('engine_type')} is required. "
                         f"The engine will be started with the default parameters.")
            return False
        logger.debug("Configuration is valid.")
        return True

    def _check_all_args_valid(self) -> None:
        """
        Check all args are valid. If not, raise ValueError
        """
        logger.debug("Checking all arguments.")
        if not isinstance(self.args, GlobalArgs):
            logger.error("args must be an instance of GlobalArgs")
            raise TypeError("args must be an instance of GlobalArgs")

        for attr in ("engine_type", "mis_config"):
            # Verify the attribute character string.
            args_attr = getattr(self.args, attr, None)
            if args_attr is not None:
                try:
                    ConfigChecker.check_string_input(attr, args_attr)
                except Exception as e:
                    raise Exception(f"{attr} in args is not a valid string: {e}") from e
        logger.info("All arguments are valid.")

    def _get_default_config(self) -> Union[str, None]:
        logger.info("Getting default configuration.")
        if self.model_type.lower() not in MIS_CONFIG_DEFAULT:
            logger.info(f"The current model {self.model_type} is not included in the optimization configuration "
                        f"or is not a large model (e.g., a embedding model).")
            return None

        soc_name = get_soc_name()
        model_config_dict = MIS_CONFIG_DEFAULT.get(self.model_type.lower())
        if model_config_dict is None:
            logger.warning(f"Default configuration for {self.model_type} is not found. "
                           f"Please check whether the model name is consistent with the image description.")
            return None
        model_config_default = model_config_dict.get(soc_name)
        if model_config_default is None:
            logger.warning(f"The current model {self.model_type} is not compatible with "
                           f"the hardware platform {soc_name}. "
                           f"Check the hardware support status of the model in the image description.")
            return None
        logger.info(f"Default configuration for {self.model_type} on {soc_name} is {model_config_default}.")
        return model_config_default
