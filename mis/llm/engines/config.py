# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
from abc import ABC, abstractmethod
from typing import Dict, Type

import yaml

from mis_llm.logger import init_logger
from mis.args import GlobalArgs
from mis.utils.env_checker import EnvChecker

logger = init_logger(__name__)

ROOT_DIR = "mis_llm/configs/"
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
        "max": 140000
    },
    "maxn_num_batched_tokens": {
        "type": "int",
        "min": 1,
        "max": 140000
    },
    "max_seq_len_to_capture": {
        "type": "int",
        "min": 1,
        "max": 140000
    },
    "gpu_memory_utilization": {
        "type": "float",
        "min": 0.0,
        "max": 1.0
    },
    "block_size": {
        "type": "int",
        "min": 1,
        "max": 256
    },
    "swap_space": {
        "type": "int",
        "min":0,
        "max": 1024,
    },
    "cpu_offload_gb": {
        "type": "int",
        "min": 0,
        "max": 1024
    },
    "scheduler_policy": {
        "type": "str_in",
        "valid_values": ["fcfs", "priority"]
    },
    "num_scheduler_steps": {
        "type": "int",
        "min": 1,
        "max": 1024
    },
    "enable_chunked_prefill": {
        "type": "bool"
    },
    "enable_prefix_caching": {
        "type": "bool"
    },
    "disable_async_output_proc": {
        "type": "bool"
    },
    "multi_step_stream_outputs": {
        "type": "bool"
    },
    "enforce_eager": {
        "type": "bool"
    }
}


class EngineConfigValidator(ABC):
    _engine_config_validation: Dict[str, Type["EngineConfigValidator"]] = {}

    def __init__(self, config):
        """
        Initialize the EngineConfigValidator class.
        """
        self.config = config
    
    @classmethod
    def register(cls, engine_type: str):
        """
        Register an engine configuration validator.
        :param engine_type: Engine type.
        :param validator_class: Engine configuration validator class.
        """
        def decorator(subclass):
            cls._engine_config_validation[engine_type] = subclass
            return subclass
        return decorator

    @classmethod
    def get_validator(cls, engine_type: str) -> Type["EngineConfigValidator"]:
        """
        Get the engine configuration validator.
        :param engine_type: Engine type.
        :return: Engine configuration validator class.
        """
        return cls._engine_config_validation.get(engine_type)

    @abstractmethod
    def validate_config(self):
        """
        Verify the configuration parameters of the engine.
        :return: Validation result.
        """
        raise NotImplementedError("Subclass must implement this method.")


@EngineConfigValidator.register("vllm")
class VLLMEngineConfigValidator(EngineConfigValidator):
    """
    VLLM engine configuration validator.
    """
    keys_list = [
        "dtype",
        "tensor_parallel_size",
        "pipeline_parallel_size",
        "distributed_executor_backend",
        "max_num_seqs",
        "max_model_len",
        "maxn_num_batched_tokens",
        "max_seq_len_to_capture",
        "gpu_memory_utilization",
        "block_size",
        "swap_space",
        "cpu_offload_gb",
        "scheduler_policy",
        "num_scheduler_steps",
        "enable_chunked_prefill",
        "enable_prefix_caching",
        "disable_async_output_proc",
        "multi_step_stream_outputs",
        "enforce_eager"
    ]

    def __init__(self, config):
        super().__init__(config)
        self.checkers = CHECKER_VLLM

    def validate_config(self) -> bool:
        """
        Verify the configuration is valid or not
        :return: Verify result
        """
        diff_config = set(self.config.keys()) - self(self.keys_list)
        if diff_config:
            logger.warning(f"Configuration keys {diff_config} are not supported.")
        config_update = {key: self.config[key] for key in self.keys_list if key in self.keys_list}
        for key in config_update:
            checker = self.checkers.get(key, None)
            if checker is None:
                continue

            value = self.config_update
            if checker["type"] == "str_in":
                EnvChecker.check_str_in(key, value, checker.get("valid_values"))
            elif checker["type"] == "int":
                if "valid_values" in checker:
                    EnvChecker.check_int(key, value, valid_values=checker.get("valid_values"))
                else:
                    EnvChecker.check_int(key, value, checker.get("min"), checker.get("max"))
            elif checker["type"] == "float":
                EnvChecker.check_float(key, value, checker.get("min"), checker.get("max"))
            elif checker["type"] == "bool":
                if not isinstance(value, bool):
                    logger.error(f"{key} must be a bool, but got {value}")
                    raise ValueError(f"{key} must be a bool, but got {value}")
        return True


class ConfigParser:
    def __init__(self, args: GlobalArgs):
        self.args = args
        self._check_all_args_valid()

    @staticmethod
    def _config_yaml_file_loading(config_file_path: str) -> bool:
        try:
            with open(ROOT_DIR + config_file_path, "r") as file:
                config = yaml.safe_load(file)
        except yaml.YAMLError as e:
            logger.error(f"YAML error in file {ROOT_DIR + config_file_path}: {e}")
            raise e
        return config
    
    @staticmethod
    def _is_config_valid(self, config: Dict) -> bool:
        if config is None:
            logger.warning("Failed to load configuration from YANL file.")
            return False
        
        if not isinstance(config, dict):
            logger.warning("Failed to load configuration from YANL file.")
            return False
        
        engine_type_selected = config.get(OPTIMAL_ENGINE_TYPE, None)
        if engine_type_selected is not None:
            EnvChecker.check_string_input("engine_type_selected", engine_type_selected)
        return True

    def engine_config_loading(self) -> GlobalArgs:
        """
        Obtain the engine configuration. IF the parameters are successfully obtained, update the args.
        :return: Update global parameters
        :raises: AttributeError if the configuration file is not found or the configuration is not valid.
        :raises: ValueError if the configuration is not valid.
        :raises: TypeError if the configuration is not valid.
        :raises: KeyError if the configuration is not valid.
        """
        engine_optimization_config = None

        model_type = self.args.model.split('/')[-1]
        engine_type = self.args.engine_type
        optimization_config_type = self.args.optimization_config_type

        model_type = model_type.replace("-", "_")

        if optimization_config_type is not None:
            logger.warning("Missing required arguments for the required configuration yaml file."
                    f"The engine will be started with the default parameters")
            self.args.engine_optimization_config = {}
            return self.args

        yaml_file_path = f"{model_type.lower()}_{optimization_config_type}.yaml"
        config = self._config_yaml_file_loading(yaml_file_path)

        if not self._is_config_valid(config):
            self.args.engine_optimization_config = {}
            return self.args
        
        engine_type_selected = config.get(OPTIMAL_ENGINE_TYPE, None) if engine_type is None else engine_type
        engine_type_selected = engine_type_selected.lower()
        if self._is_config_attr_valid(config, engine_type_selected):
            engine_optimization_config = config.get(engine_type_selected, None)

        self.args.engine_optimization_config = engine_optimization_config if (
                engine_optimization_config is not None) else {}
        return self.args
    
    def _check_all_args_valid(self):
        """
        Check all args are valid. If not, raise ValueError
        param args: global args
        """
        # Validate the input parameters type.
        if not isinstance(self.args, GlobalArgs):
            logger.error("args must be an instance of GlobalArgs")
            raise("args must be an instance of GlobalArgs")
    
        # Verify the required attributes are present.
        required_attributes = ["model", "engine_type", "optimization_config_type"]
        for attr in required_attributes:
            if not hasattr(self.args, attr):
                logger.error(f"args does not contain the {attr} attribute")
                raise AttributeError(f"args does not contain the {attr} attribute")
            
            # Verify the attribute character string.
            args_attr = getattr(self.args, attr)
            if args_attr is None:
                EnvChecker.check_string_input(attr, args_attr)

    def _is_config_attr_valid(self, config: Dict, engine_type_selected: str) -> bool:
        if not self._is_config_valid(config.get(engine_type_selected, None)):
            logger.error(f"No valid configuration found for engine type: {engine_type_selected}.")
            return False
        
        validator_class = EngineConfigValidator.get_validator_class(engine_type_selected)
        if validator_class is None:
            logger.error(f"Engine type {engine_type_selected} is not supported")
            return False
        
        validator = validator_class(config)
        return validator.validate_config()
