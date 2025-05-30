# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
from abc import ABC
import os
from typing import Dict, Type

import yaml

from mis.logger import init_logger
from mis.args import GlobalArgs
from mis.utils.utils import ConfigChecker

logger = init_logger(__name__)

ROOT_DIR = "configs/llm/"
OPTIMAL_ENGINE_TYPE = "optimal_engine_type"

CHECKER_VLLM = {
    "dtype": {
        "type": "str_in",
        "valid_values": ["bfloat16"]
    },
    "tensor_parallel_size": {
        "type": "int",
        "valid_values": [1, 2, 4, 8]
    },
    "pipeline_parallel_size": {
        "type": "int",
        "valid_values": [1, 2, 4, 8]
    },
    "distributed_exector_size": {
        "type": "str_in",
        "valid_values": ["ray", "mp"]
    },
    "max_num_seqs": {
        "type": "int",
        "min": 1,
        "max": 1024
    },
    "max_model_len": {
        "type": "int",
        "min": 1,
        "max": 131072
    },
    "max_num_batched_tokens": {
        "type": "int",
        "min": 1,
        "max": 131072
    },
    "max_seq_len_to_capture": {
        "type": "int",
        "min": 1,
        "max": 131072
    },
    "gpu_memory_utilization": {
        "type": "float",
        "min": 0.0,
        "max": 1.0
    },
    "block_size": {
        "type": "int",
        "valid_values": [16, 32, 64, 128]
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
        "valid_values": ["fcfs", "priority"]
    },
    "num_scheduler_steps": {
        "type": "int",
        "min": 1,
        "max": 1024
    },
    "enable_chunked_prefill": {
        "type": "bool",
        "valid_values": [False]
    },
    "enable_prefix_caching": {
        "type": "bool",
        "valid_values": [True, False]
    },
    "disable_async_output_proc": {
        "type": "bool",
        "valid_values": [True, False]
    },
    "multi_step_stream_outputs": {
        "type": "bool",
        "valid_values": [True, False]
    },
    "enforce_eager": {
        "type": "bool",
        "valid_values": [True, False]
    },
    "distributed_executor_backend": {
        "type": "str_in",
        "valid_values": ["ray", "mp"]
    },
    "quantization": {
        "type": "str_in",
        "valid_values": ["awq", "compressed-tensors", "ms-model-slim"]
    }
}


class AbsEngineConfigValidator(ABC):
    _engine_config_validation: Dict[str, Type["AbsEngineConfigValidator"]] = {}

    def __init__(self, config: Dict, checkers: Dict):
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
    def register(cls, engine_type: str):
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
        valid_config = {}
        for key, value in self.config_update.items():
            checker = self.checkers.get(key)

            is_valid = True
            if "valid_values" in checker:
                is_valid = ConfigChecker.is_value_in_enum(key, value, checker.get("valid_values"))
            elif "min" in checker and "max" in checker:
                is_valid = ConfigChecker.is_value_in_range(key, value, checker.get("min"), checker.get("max"))

            if is_valid:
                valid_config[key] = value

        return valid_config


@AbsEngineConfigValidator.register("vllm")
class VLLMEngineConfigValidator(AbsEngineConfigValidator):
    """
    VLLM engine configuration validator.
    """

    def __init__(self, config: Dict):
        """
        vLLM Engine configuration validator initialization.
        :param config: Configuration parameters.
        """
        super().__init__(config, CHECKER_VLLM)


@AbsEngineConfigValidator.register("mindie-service")
class VLLMEngineConfigValidator(AbsEngineConfigValidator):
    """
    MindIE-Service engine configuration validator.
    """

    def __init__(self, config: Dict):
        """
        MindIE-Service Engine configuration validator initialization.
        :param config: Configuration parameters.
        """
        super().__init__(config, CHECKER_VLLM)


class ConfigParser:
    def __init__(self, args: GlobalArgs):
        """
        Check all args are valid.
        :param args: global args
        """
        self.args = args
        self.args.engine_optimization_config = {}

        self._check_all_args_valid()

        self.model_type = self.args.model.split('/')[-1]
        self.engine_type = self.args.engine_type
        self.mis_config = self.args.mis_config

    @staticmethod
    def _config_yaml_file_loading(config_file_path: str) -> Dict:
        """
        Load config file.
        :params config_file_path: config path
        :return: Parsed configuration dictionary if successful, None otherwise.
        """
        try:
            with open(config_file_path, "r") as file:
                config = yaml.safe_load(file)
        except FileNotFoundError:
            logger.debug(f"Config file {config_file_path} not found. "
                           "The engine will be started with default parameters. ")
            config = None
        except yaml.YAMLError as e:
            logger.error(f"The configuration file {config_file_path} is invalid : {e}, "
                         f"please check the integrity of the file. ")
            raise e
        return config

    @staticmethod
    def _config_attr_update(selected_engine_type: str, selected_engine_config: Dict) -> Dict:
        """
        Update the attributes of the selected engine.
        :param selected_engine_type: The type of the selected engine.
        :param selected_engine_config: The configuration of the selected engine.
        :return: updated config dictionary. 
        """
        validator_class = AbsEngineConfigValidator.get_validator(selected_engine_type)
        validator = validator_class(selected_engine_config.get(selected_engine_type))
        return validator.filter_and_validate_config()

    def engine_config_loading(self) -> GlobalArgs:
        """
        Obtain the engine configuration. IF the parameters are successfully obtained, update the args.
        :return: Update global parameters
        """
        if self.mis_config is None:
            logger.warning("The environment variable MIS_CONFIG is missed. "
                           "Please check if the environment variables is valid. "
                           f"The engine will be started with the default parameters. ")
            return self.args

        model_folder_path = os.path.join(ROOT_DIR, self.model_type.lower())

        if not os.path.exists(model_folder_path):
            logger.debug(f"Model folder {model_folder_path} does not exist. "
                           f"The engine will be started with the default parameters. ")
            return self.args

        engine_optimization_config = None
        filename_list = os.listdir(model_folder_path)
        if self.mis_config + ".yaml" in filename_list:
            config_file_path = os.path.join(model_folder_path, self.mis_config + ".yaml")
            engine_optimization_config = self._config_yaml_file_loading(config_file_path)

        if not engine_optimization_config or not self._is_config_valid(engine_optimization_config):
            return self.args

        engine_type_selected = engine_optimization_config.get("engine_type")
        self.args.engine_optimization_config = self._config_attr_update(engine_type_selected,
                                                                        engine_optimization_config)

        self.args.model = engine_optimization_config.get("model")
        self.args.engine_type = engine_type_selected

        model_type = engine_optimization_config.get("model_type")
        if model_type is not None and model_type == "VLM":
            self.args.engine_optimization_config["allowed_local_media_path"] = self.args.allowed_local_media_path
            self.args.engine_optimization_config["limit_mm_per_prompt"] = {
                "image": self.args.limit_image_per_prompt,
                "video": self.args.limit_video_per_prompt,
                "audio": self.args.limit_audio_per_prompt
            }

        return self.args

    def _is_config_valid(self, config: Dict) -> bool:
        """
        Checks if the config is valid.
        :param config: Config to check.
        :return: True if the config is valid, False otherwise.
        """
        if config is None or not isinstance(config, dict):
            logger.debug(f"The YAML config file for {self.model_type} ({self.mis_config}) is invalid. "
                         f"The engine will be started with the default parameters. ")
            return False

        if config.get("engine_type") is None or config.get("model") is None:
            logger.debug(f"Please check if keywords engine_type and model in "
                         f"{self.model_type} ({self.mis_config}) YAML is complete. "
                         f"The engine will be started with the default parameters. ")
            return False

        if config.get(config.get("engine_type")) is None:
            logger.debug(f"Config of engine type {config.get('engine_type')} is required. "
                           f"The engine will be started with the default parameters. ")
            return False
        return True

    def _check_all_args_valid(self):
        """
        Check all args are valid. If not, raise ValueError
        """
        # Validate the input parameters type.
        if not isinstance(self.args, GlobalArgs):
            logger.error("args must be an instance of GlobalArgs")
            raise TypeError("args must be an instance of GlobalArgs")

        required_attributes = ["engine_type", "mis_config"]
        for attr in required_attributes:
            # Verify the attribute character string.
            args_attr = getattr(self.args, attr)
            if args_attr is not None:
                try:
                    ConfigChecker.check_string_input(attr, args_attr)
                except Exception as e:
                    raise Exception(f"{attr} in args is not a valid string: {e}") from e
