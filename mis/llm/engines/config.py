# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
from abc import ABC
import os
from typing import Any, Dict, Optional, Type, Union

import yaml

from mis.logger import init_logger
from mis.args import GlobalArgs
from mis.constants import HW_310P, HW_910B
from mis.utils.utils import ConfigChecker, get_soc_name

logger = init_logger(__name__)

OPTIMAL_ENGINE_TYPE = "optimal_engine_type"
MIS_CONFIG_DEFAULT = {
    "deepseek-r1-distill-llama-8b": {HW_310P: "ascend310p-2x24gb-bf16-mindie-service-default",
                                     HW_910B: "atlas800ia2-1x32gb-bf16-vllm-default"},
    "deepseek-r1-distill-llama-70b": {HW_910B: "atlas800ia2-8x32gb-bf16-vllm-default"},
    "deepseek-r1-distill-qwen-1.5b": {HW_310P: "ascend310p-1x24gb-bf16-mindie-service-default",
                                      HW_910B: "atlas800ia2-1x32gb-bf16-vllm-default"},
    "deepseek-r1-distill-qwen-7b": {HW_310P: "ascend310p-2x24gb-bf16-mindie-service-default",
                                    HW_910B: "atlas800ia2-1x32gb-bf16-vllm-default"},
    "deepseek-r1-distill-qwen-14b": {HW_310P: "ascend310p-4x24gb-bf16-mindie-service-default",
                                     HW_910B: "atlas800ia2-2x32gb-bf16-vllm-default"},
    "deepseek-r1-distill-qwen-32b": {HW_910B: "atlas800ia2-4x32gb-bf16-vllm-default"},
    "llama-3.2-1b-instruct": {HW_910B: "atlas800ia2-1x32gb-bf16-vllm-default"},
    "llama-3.2-3b-instruct": {HW_910B: "atlas800ia2-1x32gb-bf16-vllm-default"},
    "llama-3.3-70b-instruct": {HW_910B: "atlas800ia2-8x32gb-bf16-vllm-default"},
    "minicpm-v-2_6": {HW_310P: "ascend310p-2x24gb-bf16-mindie-service-default",
                      HW_910B: "atlas800ia2-2x32gb-bf16-mindie-service-default"},
    "qwen2.5-0.5b-instruct": {HW_910B: "atlas800ia2-1x32gb-bf16-vllm-default"},
    "qwen2.5-1.5b-instruct": {HW_910B: "atlas800ia2-1x32gb-bf16-vllm-default"},
    "qwen2.5-3b-instruct": {HW_910B: "atlas800ia2-1x32gb-bf16-vllm-default"},
    "qwen2.5-7b-instruct": {HW_310P: "ascend310p-2x24gb-bf16-mindie-service-default",
                            HW_910B: "atlas800ia2-1x32gb-bf16-vllm-default"},
    "qwen2.5-14b-instruct": {HW_310P: "ascend310p-4x24gb-bf16-mindie-service-default",
                             HW_910B: "atlas800ia2-2x32gb-bf16-vllm-default"},
    "qwen2.5-7b-instruct-1m": {HW_910B: "atlas800ia2-4x32gb-bf16-vllm-default"},
    "qwen2.5-14b-instruct-1m": {HW_910B: "atlas800ia2-8x32gb-bf16-vllm-default"},
    "qwen2.5-32b-instruct": {HW_910B: "atlas800ia2-4x32gb-bf16-vllm-default"},
    "qwen2.5-72b-instruct": {HW_910B: "atlas800ia2-8x32gb-bf16-vllm-default"},
    "qwen2.5-vl-3b-instruct": {HW_910B: "atlas800ia2-1x32gb-bf16-vllm-default"},
    "qwen2.5-vl-7b-instruct": {HW_910B: "atlas800ia2-2x32gb-bf16-vllm-default"},
    "qwen2.5-vl-32b-instruct": {HW_910B: "atlas800ia2-4x32gb-bf16-vllm-default"},
    "qwen2.5-vl-72b-instruct": {HW_910B: "atlas800ia2-8x32gb-bf16-vllm-default"},
    "qwen3-0.6b": {HW_910B: "atlas800ia2-1x32gb-bf16-vllm-default"},
    "qwen3-1.7b": {HW_910B: "atlas800ia2-1x32gb-bf16-vllm-default"},
    "qwen3-4b": {HW_910B: "atlas800ia2-1x32gb-bf16-vllm-default"},
    "qwen3-8b": {HW_910B: "atlas800ia2-1x32gb-bf16-vllm-default"},
    "qwen3-14b": {HW_910B: "atlas800ia2-2x32gb-bf16-vllm-default"},
    "qwen3-32b": {HW_910B: "atlas800ia2-4x32gb-bf16-vllm-default"},
    "qwen3-30b-a3b": {HW_910B: "atlas800ia2-4x32gb-bf16-vllm-default"},
    "qwen3-235b-a22b": {HW_910B: "atlas800ia2-16x64gb-bf16-vllm-default"},
    "qwq-32b": {HW_910B: "atlas800ia2-4x32gb-bf16-vllm-default"},
    "qwen2.5-omni-3b": {HW_910B: "atlas800ia2-1x32gb-bf16-vllm-default"},
    "qwen2.5-omni-7b": {HW_910B: "atlas800ia2-2x32gb-bf16-vllm-default"},
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
        "valid_values": (1, 2, 4, 8)
    },
    "distributed_exector_size": {
        "type": "str_in",
        "valid_values": ("ray", "mp")
    },
    "max_num_seqs": {
        "type": "int",
        "min": 1,
        "max": 1024
    },
    "max_model_len": {
        "type": "int",
        "min": 1,
        "max": 1010000
    },
    "max_num_batched_tokens": {
        "type": "int",
        "min": 1,
        "max": 1010000
    },
    "max_seq_len_to_capture": {
        "type": "int",
        "min": 1,
        "max": 1010000
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
    "disable_async_output_proc": {
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
    "distributed_executor_backend": {
        "type": "str_in",
        "valid_values": ("ray", "mp")
    },
    "quantization": {
        "type": "str_in",
        "valid_values": ("awq", "compressed-tensors", "ms-model-slim")
    },
    "npu_memory_fraction": {
        "type": "float",
        "min": 0.5,
        "max": 0.97,
    },
    "vllm_allow_long_max_model_len": {
        "type": "bool",
        "valid_values": (True, False)
    },
    "vllm_use_v1": {
        "type": "int",
        "valid_values": (0, 1)
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
        self.model_folder_path = os.path.join(args.configs_path, self.model_type.lower())
        self.engine_type = self.args.engine_type
        self.mis_config = self.args.mis_config

    @staticmethod
    def _get_range_str(config: Dict[str, Any]):
        """
        Get the range string for a configuration parameter based on its type and specified range or valid values.

        :param config: A dictionary containing the configuration details of a parameter.
        :return: A tuple containing the parameter type and the range string.
                 The range string describes the valid range or values for the parameter.
        """
        param_type = config.get("type", "unknown")
        range_str = "No range specified"

        if param_type in ["int", "float"]:
            valid_values = config.get("valid_values", None)
            if valid_values is not None:
                range_str = f"Valid values: {valid_values}"
            else:
                min_val = config.get("min", None)
                max_val = config.get("max", None)
                if min_val is not None and max_val is not None:
                    range_str = f"Range: [{min_val}, {max_val}]"
        elif param_type in ["bool", "str_in"]:
            valid_values = config.get("valid_values", None)
            if valid_values is not None:
                range_str = f"Valid values: {valid_values}"
            else:
                range_str = "No valid values specified"
        else:
            range_str = "Unknown type"
        return param_type, range_str

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
                         "please check the integrity of the file. ")
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

    def print_config_ranges(self, checker_dict: Dict[str, Dict[str, Any]] = None) -> None:
        """
        Print the configuration parameter range.
        :param checker_dict: Configuring the Parameter Dictionary
        """
        if checker_dict is None:
            checker_dict = CHECKER_VLLM
        try:
            for param, config in checker_dict.items():
                param_type, range_str = self._get_range_str(config)
                logger.info(f"Parameter: {param}, Type: {param_type}, {range_str}")
        except Exception as e:
            logger.error(f"Error processing in print config ranges: {e}")

    def load_config_from_file(self) -> Optional[Dict]:
        """
        Loading the configuration from a specified YAML file.
        If the specified configuration file does not exist or the environment variable `MIS_CONFIG` is not set,
        the method will use the default configuration.

        :returns: A dictionary containing the configuration loaded from the YAML file,
        or `None` if no valid configuration is found.
        """
        if self.mis_config is None:
            logger.warning("The environment variable MIS_CONFIG is missed. "
                           "Please check if the environment variables is valid. "
                           "The engine will be started with the default parameters. ")
            self.mis_config = self._get_default_config()

        elif not os.path.exists(os.path.join(self.model_folder_path, self.mis_config + ".yaml")):
            logger.debug(f"Selected config {self.mis_config} does not exist. "
                         f"The engine will be started with the default config. ")
            self.mis_config = self._get_default_config()

        if self.mis_config is None:
            return None

        config_file_path = os.path.join(self.model_folder_path, self.mis_config + ".yaml")
        engine_optimization_config = self._config_yaml_file_loading(config_file_path)
        return engine_optimization_config

    def engine_config_loading(self) -> GlobalArgs:
        """
        Obtain the engine configuration. If the parameters are successfully obtained, update the args.
        :return: Update global parameters
        """
        engine_optimization_config = self.load_config_from_file()
        if not engine_optimization_config or not self._is_config_valid(engine_optimization_config):
            return self.args

        engine_type_selected = engine_optimization_config.get("engine_type")
        self.args.engine_optimization_config = self._config_attr_update(engine_type_selected,
                                                                        engine_optimization_config)

        self.args.model = engine_optimization_config.get("model")
        self.args.engine_type = engine_type_selected
        if engine_optimization_config.get("trust_remote_code") is not None:
            self.args.trust_remote_code = engine_optimization_config.get("trust_remote_code")

        model_type = engine_optimization_config.get("model_type")
        if model_type is not None and model_type == "VLM":
            self.args.engine_optimization_config["allowed_local_media_path"] = self.args.allowed_local_media_path
            self.args.engine_optimization_config["limit_mm_per_prompt"] = {
                "image": self.args.limit_image_per_prompt,
                "video": self.args.limit_video_per_prompt,
                "audio": self.args.limit_audio_per_prompt
            }
            self.args.engine_optimization_config["mm_processor_kwargs"] = {
                "total_pixels": self.args.total_pixels,
                "max_pixels": self.args.total_pixels  # The `max_pixels` applies to a single image and
                # is less or equal than `total_pixels`. However, during the initialization of vLLM,
                # no such restriction is enforced, which may lead to an excessive number of initial multimodal tokens
                # and result in an Out-Of-Memory (OOM) error.
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

        engine_type = config.get("engine_type")
        if engine_type not in ["vllm", "mindie-service"]:
            logger.error(f"engine_type in YAML config file must in ['vllm', 'mindie-service']")

        if config.get(engine_type) is None:
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

    def _get_default_config(self) -> Union[str, None]:
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
        return model_config_default
