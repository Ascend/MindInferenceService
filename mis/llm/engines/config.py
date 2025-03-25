# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
from abc import ABC
from typing import Dict, Type

import yaml

from mis.logger import init_logger
from mis.args import GlobalArgs
from mis.utils.utils import ConfigChecker

logger = init_logger(__name__)

ROOT_DIR = "mis/llm/configs/"
OPTIMAL_ENGINE_TYPE = "optimal_engine_type"

CONFIG_YAML_FILES_MAP = {
    "DeepSeek-R1-Distill-Qwen-1.5B": {
        "default": "deepseek-r1-distill-qwen-1.5b-default.yaml",
        "latency": "deepseek-r1-distill-qwen-1.5b-latency.yaml",
        "throughput": "deepseek-r1-distill-qwen-1.5b-throughput.yaml"
    },
    "DeepSeek-R1-Distill-Qwen-7B": {
        "default": "deepseek-r1-distill-qwen-7b-default.yaml",
        "latency": "deepseek-r1-distill-qwen-7b-latency.yaml",
        "throughput": "deepseek-r1-distill-qwen-7b-throughput.yaml"
    },
    "DeepSeek-R1-Distill-Qwen-14B": {
        "default": "deepseek-r1-distill-qwen-14b-default.yaml",
        "latency": "deepseek-r1-distill-qwen-14b-latency.yaml",
        "throughput": "deepseek-r1-distill-qwen-14b-throughput.yaml"
    },
    "DeepSeek-R1-Distill-Qwen-32B": {
        "default": "deepseek-r1-distill-qwen-32b-default.yaml",
        "latency": "deepseek-r1-distill-qwen-32b-latency.yaml",
        "throughput": "deepseek-r1-distill-qwen-32b-throughput.yaml"
    },
    "DeepSeek-R1-Distill-Llama-8B": {
        "default": "deepseek-r1-distill-llama-8b-default.yaml",
        "latency": "deepseek-r1-distill-llama-8b-latency.yaml",
        "throughput": "deepseek-r1-distill-llama-8b-throughput.yaml"
    },
    "DeepSeek-R1-Distill-Llama-70B": {
        "default": "deepseek-r1-distill-llama-70b-default.yaml",
        "latency": "deepseek-r1-distill-llama-70b-latency.yaml",
        "throughput": "deepseek-r1-distill-llama-70b-throughput.yaml"
    },

    "Llama-3.2-1B-Instruct": {
        "default": "llama-3.2-1b-instruct-default.yaml",
        "latency": "llama-3.2-1b-instruct-latency.yaml",
        "throughput": "llama-3.2-1b-instruct-throughput.yaml"
    },
    "Llama-3.2-3B-Instruct": {
        "default": "llama-3.2-3b-instruct-default.yaml",
        "latency": "llama-3.2-3b-instruct-latency.yaml",
        "throughput": "llama-3.2-3b-instruct-throughput.yaml"
    },
    "Llama-3.3-70B-Instruct": {
        "default": "llama-3.3-70b-instruct-default.yaml",
        "latency": "llama-3.3-70b-instruct-latency.yaml",
        "throughput": "llama-3.3-70b-instruct-throughput.yaml"
    },

    "Qwen2.5-0.5B-Instruct": {
        "default": "qwen2.5-0.5b-instruct-default.yaml",
        "latency": "qwen2.5-0.5b-instruct-latency.yaml",
        "throughput": "qwen2.5-0.5b-instruct-throughput.yaml"
    },
    "Qwen2.5-1.5B-Instruct": {
        "default": "qwen2.5-1.5b-instruct-default.yaml",
        "latency": "qwen2.5-1.5b-instruct-latency.yaml",
        "throughput": "qwen2.5-1.5b-instruct-throughput.yaml"
    },
    "Qwen2.5-3B-Instruct": {
        "default": "qwen2.5-3b-instruct-default.yaml",
        "latency": "qwen2.5-3b-instruct-latency.yaml",
        "throughput": "qwen2.5-3b-instruct-throughput.yaml"
    },
    "Qwen2.5-7B-Instruct": {
        "default": "qwen2.5-7b-instruct-default.yaml",
        "latency": "qwen2.5-7b-instruct-latency.yaml",
        "throughput": "qwen2.5-7b-instruct-throughput.yaml"
    },
    "Qwen2.5-14B-Instruct": {
        "default": "qwen2.5-14b-instruct-default.yaml",
        "latency": "qwen2.5-14b-instruct-latency.yaml",
        "throughput": "qwen2.5-14b-instruct-throughput.yaml"
    },
    "Qwen2.5-32B-Instruct": {
        "default": "qwen2.5-32b-instruct-default.yaml",
        "latency": "qwen2.5-32b-instruct-latency.yaml",
        "throughput": "qwen2.5-32b-instruct-throughput.yaml"
    },
    "Qwen2.5-72B-Instruct": {
        "default": "qwen2.5-72b-instruct-default.yaml",
        "latency": "qwen2.5-72b-instruct-latency.yaml",
        "throughput": "qwen2.5-72b-instruct-throughput.yaml"
    },

    "QwQ-32B": {
        "default": "qwq-32b-default.yaml",
        "latency": "qwq-32b-latency.yaml",
        "throughput": "qwq-32b-throughput.yaml"
    },

"DeepSeek-R1-Distill-Qwen-14B-quantized.w8a8": {
        "default": "deepseek-r1-distill-qwen-14b-quantized.w8a8-default.yaml",
        "latency": "deepseek-r1-distill-qwen-14b-quantized.w8a8-latency.yaml",
        "throughput": "deepseek-r1-distill-qwen-14b-quantized.w8a8-throughput.yaml"
    },
    "DeepSeek-R1-Distill-Qwen-32B-quantized.w8a8": {
        "default": "deepseek-r1-distill-qwen-32b-quantized.w8a8-default.yaml",
        "latency": "deepseek-r1-distill-qwen-32b-quantized.w8a8-latency.yaml",
        "throughput": "deepseek-r1-distill-qwen-32b-quantized.w8a8-throughput.yaml"
    },
    "DeepSeek-R1-Distill-Llama-70B-quantized.w8a8": {
        "default": "deepseek-r1-distill-llama-70b-quantized.w8a8-default.yaml",
        "latency": "deepseek-r1-distill-llama-70b-quantized.w8a8-latency.yaml",
        "throughput": "deepseek-r1-distill-llama-70b-quantized.w8a8-throughput.yaml"
    },
    "Llama-3.3-70B-Instruct-quantized.w8a8": {
        "default": "llama-3.3-70b-instruct-quantized.w8a8-default.yaml",
        "latency": "llama-3.3-70b-instruct-quantized.w8a8-latency.yaml",
        "throughput": "llama-3.3-70b-instruct-quantized.w8a8-throughput.yaml"
    },
    "Qwen2.5-14B-Instruct-quantized.w8a8": {
        "default": "qwen2.5-14b-instruct-quantized.w8a8-default.yaml",
        "latency": "qwen2.5-14b-instruct-quantized.w8a8-latency.yaml",
        "throughput": "qwen2.5-14b-instruct-quantized.w8a8-throughput.yaml"
    },
    "Qwen2.5-32B-Instruct-quantized.w8a8": {
        "default": "qwen2.5-32b-instruct-quantized.w8a8-default.yaml",
        "latency": "qwen2.5-32b-instruct-quantized.w8a8-latency.yaml",
        "throughput": "qwen2.5-32b-instruct-quantized.w8a8-throughput.yaml"
    },
    "Qwen2.5-72B-Instruct-quantized.w8a8": {
        "default": "qwen2.5-72b-instruct-quantized.w8a8-default.yaml",
        "latency": "qwen2.5-72b-instruct-quantized.w8a8-latency.yaml",
        "throughput": "qwen2.5-72b-instruct-quantized.w8a8-throughput.yaml"
    },
    "QwQ-32B-quantized.w8a8": {
        "default": "qwq-32b-quantized.w8a8-default.yaml",
        "latency": "qwq-32b-quantized.w8a8-latency.yaml",
        "throughput": "qwq-32b-quantized.w8a8-throughput.yaml"
    },

    "DeepSeek-R1-Distill-Qwen-14B-AWQ": {
        "default": "deepseek-r1-distill-qwen-14b-awq-default.yaml",
        "latency": "deepseek-r1-distill-qwen-14b-awq-latency.yaml",
        "throughput": "deepseek-r1-distill-qwen-14b-awq-throughput.yaml"
    },
    "DeepSeek-R1-Distill-Qwen-32B-AWQ": {
        "default": "deepseek-r1-distill-qwen-32b-awq-default.yaml",
        "latency": "deepseek-r1-distill-qwen-32b-awq-latency.yaml",
        "throughput": "deepseek-r1-distill-qwen-32b-awq-throughput.yaml"
    },
    "DeepSeek-R1-Distill-Llama--AWQ": {
        "default": "deepseek-r1-distill-llama-70b-awq-default.yaml",
        "latency": "deepseek-r1-distill-llama-70b-awq-latency.yaml",
        "throughput": "deepseek-r1-distill-llama-70b-awq-throughput.yaml"
    },
    "Llama-3.3-70B-Instruct-AWQ": {
        "default": "llama-3.3-70b-instruct-awq-default.yaml",
        "latency": "llama-3.3-70b-instruct-awq-latency.yaml",
        "throughput": "llama-3.3-70b-instruct-awq-throughput.yaml"
    },
    "Qwen2.5-14B-Instruct-AWQ": {
        "default": "qwen2.5-14b-instruct-awq-default.yaml",
        "latency": "qwen2.5-14b-instruct-awq-latency.yaml",
        "throughput": "qwen2.5-14b-instruct-awq-throughput.yaml"
    },
    "Qwen2.5-32B-Instruct-AWQ": {
        "default": "qwen2.5-32b-instruct-awq-default.yaml",
        "latency": "qwen2.5-32b-instruct-awq-latency.yaml",
        "throughput": "qwen2.5-32b-instruct-awq-throughput.yaml"
    },
    "Qwen2.5-72B-Instruct-AWQ": {
        "default": "qwen2.5-72b-instruct-awq-default.yaml",
        "latency": "qwen2.5-72b-instruct-awq-latency.yaml",
        "throughput": "qwen2.5-72b-instruct-awq-throughput.yaml"
    },
    "QwQ-32B-AWQ": {
        "default": "qwq-32b-awq-default.yaml",
        "latency": "qwq-32b-awq-latency.yaml",
        "throughput": "qwq-32b-awq-throughput.yaml"
    },
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
            logger.warning(f"Configuration keys {diff_config} are not supported.")
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
        self.optimization_config_type = self.args.optimization_config_type

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
            logger.warning(f"Config file {config_file_path} not found."
                            " The engine will be started with default parameters.")
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
            logger.warning("The configuration from YAML file is empty.")
            return False

        if not isinstance(config, dict):
            logger.warning("The configuration from YAML file is not dictionary.")
            return False

        return True

    @staticmethod
    def _config_attr_update(selected_engine_type: str, selected_engine_config: Dict) -> Dict:
        """
        Update the attributes of the selected engine.
        :param selected_engine_type: The type of the selected engine.
        :param selected_engine_config: The configuration of the selected engine.
        :return: updated config dictionary. 
        """
        validator_class = AbsEngineConfigValidator.get_validator(selected_engine_type)
        validator = validator_class(selected_engine_config)
        return validator.filter_and_validate_config()

    def engine_config_loading(self) -> GlobalArgs:
        """
        Obtain the engine configuration. IF the parameters are successfully obtained, update the args.
        :return: Update global parameters
        """
        if self.optimization_config_type is None:
            logger.warning("Missing required arguments for the required configuration yaml file."
                    f"The engine will be started with the default parameters")
            return self.args

        yaml_file = CONFIG_YAML_FILES_MAP.get(self.model_type).get(self.optimization_config_type)
        config = self._config_yaml_file_loading(ROOT_DIR + yaml_file)

        if not self._is_config_valid(config):
            return self.args

        engine_type_selected = self.engine_type if self.engine_type is not None else \
              config.get(OPTIMAL_ENGINE_TYPE) # engine_type default="vllm"
        engine_optimization_config = config.get(engine_type_selected, None)

        if engine_optimization_config is None:
            logger.warning(f"Configuration of engine {engine_type_selected} is empty.")
            return self.args

        self.args.engine_optimization_config = self._config_attr_update(engine_type_selected,
                                                                        engine_optimization_config)
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
                try:
                    ConfigChecker.check_string_input(attr, args_attr)
                except Exception as e:
                    raise Exception(f"{attr} in args is not a valid string: {e}") from e
