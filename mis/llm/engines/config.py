# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
from abc import ABC, abstractmethod
from typing import Dict, Type

import yaml

from mis.logger import init_logger
from mis.args import GlobalArgs
from mis.utils.utils import ConfigChecker

logger = init_logger(__name__)

ROOT_DIR = "mis/llm/configs/"
OPTIMAL_ENGINE_TYPE = "optimal_engine_type"

CONFIG_YAML_FILES_MAP = {"deepseek-r1-distill-qwen-1.5b": 
                        {"default": "deepseek-r1-distill-qwen-1.5b-default.yaml",
                        "latency": "deepseek-r1-distill-qwen-1.5b-latency.yaml",
                        "throughput": "deepseek-r1-distill-qwen-1.5b-throughput.yaml"},

                        "deepseek-r1-distill-qwen-7b": 
                        {"default": "deepseek-r1-distill-qwen-7b-default.yaml",
                        "latency": "deepseek-r1-distill-qwen-7b-latency.yaml",
                        "throughput": "deepseek-r1-distill-qwen-7b-throughput.yaml"},

                        "deepseek-r1-distill-qwen-14b": 
                        {"default": "deepseek-r1-distill-qwen-14b-default.yaml",
                        "latency": "deepseek-r1-distill-qwen-14b-latency.yaml",
                        "throughput": "deepseek-r1-distill-qwen-14b-throughput.yaml"},

                        "deepseek-r1-distill-qwen-32b":
                        {"default": "deepseek-r1-distill-qwen-32b-default.yaml",
                        "latency": "deepseek-r1-distill-qwen-32b-latency.yaml",
                        "throughput": "deepseek-r1-distill-qwen-32b-throughput.yaml"},

                        "deepseek-r1-distill-llama-8b":
                        {"default": "deepseek-r1-distill-llama-8b-default.yaml",
                        "latency": "deepseek-r1-distill-llama-8b-latency.yaml",
                        "throughput": "deepseek-r1-distill-llama-8b-throughput.yaml"},

                        "deepseek-r1-distill-llama-70b":
                        {"default": "deepseek-r1-distill-llama-70b-default.yaml",
                        "latency": "deepseek-r1-distill-llama-70b-latency.yaml",
                        "throughput": "deepseek-r1-distill-llama-70b-throughput.yaml"},
                        }

                        
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
        "min":0,
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
        "valid_values": [False]
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
    }
}


class AbsEngineConfigValidator(ABC):
    _engine_config_validation: Dict[str, Type["AbsEngineConfigValidator"]] = {}

    def __init__(self, config):
        """
        Initialize the AbsEngineConfigValidator class.
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
    def get_validator(cls, engine_type: str) -> Type["AbsEngineConfigValidator"]:
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
        super().__init__(config)
        self.checkers = CHECKER_VLLM

    def validate_config(self) -> bool:
        """
        Verify the configuration is valid or not.
        :return: Validation result
        """
        diff_config = set(self.config.keys()) - set(self.checkers.keys())
        if diff_config:
            logger.warning(f"Configuration keys {diff_config} are not supported.")

        config_update = {key: self.config[key] for key in self.config if key in self.checkers.keys()}

        for key in config_update:
            checker = self.checkers.get(key)
            value = config_update.get(key)
            if "valid_values" in checker:
                ConfigChecker.is_value_in_enum(key, value, checker.get("valid_values"))
            elif "min" in checker and "max" in checker:
                ConfigChecker.is_value_in_range(key, value, checker.get("min"), checker.get("max"))
        return True


class ConfigParser:
    def __init__(self, args: GlobalArgs):
        """
        Check all args are valid.
        :param args: global args
        """
        self.args = args
        self._check_all_args_valid()

    @staticmethod
    def _config_yaml_file_loading(config_file_path: str) -> Dict:
        """
        Load config file.
        :params config_file_path: config path
        :return: True if config file is loaded successfully, False otherwise.
        """
        try:
            with open(config_file_path, "r") as file:
                config = yaml.safe_load(file)
        except FileNotFoundError:
            logger.error(f"Config file {config_file_path} not found."
                         f" The engine will be started with default parameters.")
            config = None
        except yaml.YAMLError as e:
            logger.error(f"YAML error in file {config_file_path}: {e}")
            raise e
        return config
    
    @staticmethod
    def _is_config_valid(config: Dict) -> bool:
        """
        Checks if the config is valid.
        :param config: Config to check.
        :return: True if the config is valid, False otherwise.
        """
        if config is None:
            logger.warning("The configuration from YANL file is empty.")
            return False
        
        if not isinstance(config, dict):
            logger.warning("The configuration from YANL file is not dictionary.")
            return False
        
        engine_type_selected = config.get(OPTIMAL_ENGINE_TYPE, None)
        if engine_type_selected is not None:
            ConfigChecker.check_string_input("engine_type_selected", engine_type_selected)
        return True

    def engine_config_loading(self) -> GlobalArgs:
        """
        Obtain the engine configuration. IF the parameters are successfully obtained, update the args.
        :return: Update global parameters
        """
        self.args.engine_optimization_config = {}

        model_type = self.args.model.split('/')[-1]
        engine_type = self.args.engine_type
        optimization_config_type = self.args.optimization_config_type

        if optimization_config_type is None:
            logger.warning("Missing required arguments for the required configuration yaml file."
                    f"The engine will be started with the default parameters")
            return self.args

        yaml_file = CONFIG_YAML_FILES_MAP[model_type][optimization_config_type]
        config = self._config_yaml_file_loading(ROOT_DIR + yaml_file)

        if not self._is_config_valid(config):
            return self.args
        
        engine_type_selected = engine_type if engine_type is not None else config.get(OPTIMAL_ENGINE_TYPE)
        engine_optimization_config = config.get(engine_type_selected, None)

        if self._is_config_attr_valid(engine_type_selected, engine_optimization_config):
            self.args.engine_optimization_config = engine_optimization_config
        
        return self.args
    
    def _check_all_args_valid(self):
        """
        Check all args are valid. If not, raise ValueError
        """
        # Validate the input parameters type.
        if not isinstance(self.args, GlobalArgs):
            logger.error("args must be an instance of GlobalArgs")
            raise TypeError("args must be an instance of GlobalArgs")
    
        required_attributes = ["engine_type", "optimization_config_type"]
        for attr in required_attributes:
            # Verify the attribute character string.
            args_attr = getattr(self.args, attr)
            if args_attr is not None:
                ConfigChecker.check_string_input(attr, args_attr)

    def _is_config_attr_valid(self, selected_engine_type: str, selected_engine_config: Dict, ) -> bool:
        """
        Check if the config attribute is valid. 
        :param config: The config dictionary.
        :param engine_type_selected: The engine type selected.
        :return: True if the config attribute is valid, False otherwise.
        """
        if selected_engine_config is None:
            logger.error(f"Configuration of engine {selected_engine_type} is empty.")
            return False
        
        validator_class = AbsEngineConfigValidator.get_validator(selected_engine_type)
        if validator_class is None:
            logger.error(f"{selected_engine_type} engine config validator not implemented")
            return False
        
        validator = validator_class(selected_engine_config)
        return validator.validate_config()
