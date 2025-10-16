# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
from abc import ABC
from typing import Callable, Dict, Type, Union

from mis.logger import init_logger
from mis.utils.utils import ConfigChecker

logger = init_logger(__name__)

TYPE_MAPPING = {
    "int": int,
    "float": float,
    "bool": bool,
    "str_in": str,
    "str": str
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
    """Abstract engine configuration validator."""
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
            logger.error(f"Configuration keys {diff_config} are not supported.")
            raise ValueError(f"Configuration keys {diff_config} are not supported.")
        self.config_update: Dict = {key: self.config[key] for key in self.config if key in self.checkers.keys()}

    @staticmethod
    def _check_type(key: str, value: Union[int, float, bool, str], expected_type: Type) -> bool:
        """
        Check the type of the value.
        :param key: Configuration key
        :param value: Configuration value
        :param expected_type: Expected type as string
        :return: True if type matches, False otherwise
        """
        if expected_type is None:
            logger.error(f"Unknown expected type '{expected_type}' for key '{key}'")
            raise Exception(f"Unknown expected type '{expected_type}' for key '{key}'")
        return isinstance(value, expected_type)

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
            expected_type = checker.get("type")
            if expected_type and expected_type in TYPE_MAPPING:
                expected_type = TYPE_MAPPING.get(expected_type)
                type_check_passed = self._check_type(key, value, expected_type)
                if not type_check_passed:
                    logger.error(f"Configuration key '{key}' expects type '{expected_type.__name__}' "
                                 f"but got '{type(value).__name__}'")
                    raise TypeError(f"Configuration key '{key}' expects type '{expected_type.__name__}' "
                                    f"but got '{type(value).__name__}'")
            else:
                logger.error(f"Checker for {key} does not specify the expected type.")
                raise Exception(f"Checker for {key} does not specify the expected type.")

            if "valid_values" in checker:
                is_valid = ConfigChecker.is_value_in_enum(key, value, checker.get("valid_values"))
                valid_range_str = f"Valid in {checker.get('valid_values')}"
            elif "min" in checker and "max" in checker:
                is_valid = ConfigChecker.is_value_in_range(key, value, checker.get("min"), checker.get("max"))
                valid_range_str = f"Valid in range {checker.get('min')} - {checker.get('max')}"
            else:
                valid_range_str = "Valid values or range not specified"
                logger.error(f"Checker for {key} must specify either 'valid_values' or both 'min' and 'max'.")
                raise Exception(f"Checker for {key} must specify either 'valid_values' or both 'min' and 'max'.")
            if not is_valid:
                logger.error(f"Configuration value for key '{key}' is invalid. {valid_range_str}")
                raise ValueError(f"Configuration value for key '{key}' is invalid. {valid_range_str}")
            valid_config[key] = value
        logger.debug("Configuration filtered and validated successfully.")
        return valid_config


@AbsEngineConfigValidator.register("vllm")
class VLLMEngineConfigValidator(AbsEngineConfigValidator):
    """VLLM engine configuration validator."""
    def __init__(self, config: Dict) -> None:
        """
        vLLM Engine configuration validator initialization.
        :param config: Configuration parameters.
        """
        super().__init__(config, CHECKER_VLLM)
