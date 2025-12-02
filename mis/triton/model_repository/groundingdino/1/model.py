#!/usr/bin/env python
# coding=utf-8
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import os
from typing import Dict, Any

# Since the model_repository/{model_name} is treated as a separate component in the Triton service,
# an absolute reference method is used.
from mis.envs import MIS_CACHE_PATH
from mis.triton.model_backends.model import BaseTritonPythonModel
from mis.logger import init_logger, LogType

logger = init_logger(__name__, log_type=LogType.SERVICE)
CUSTOM_SIZES = 10 << 20  # 10 * 1024 * 1024


class TritonPythonModel(BaseTritonPythonModel):
    """Triton Python Backend Model for GroundingDino"""

    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def _get_default_parameters() -> Dict[str, Any]:
        """
        Get default parameters for the GroundingDino model.
        Returns: Dict containing default parameters
        """
        return {
            "backend_type": {"string_value": "ascend_om"},
            "modal_type_list": {"string_value": ["image", "text"]},
            "backend_config": {"string_value": {"device_id": 0}},
            "infer_config": {"string_value": {"infer_mode": "dymshape", "custom_sizes": CUSTOM_SIZES}},
            "processor_config": {"string_value":
                {
                    "tokenizer_path": f"{os.path.join(MIS_CACHE_PATH, 'bert-base-uncased')}",
                    "target_size": [800, 800],
                    "max_length": 20,
                    "padding": "max_length",
                    "truncation": True
                }
            }
        }

    def initialize(self, args: Dict[str, Any]) -> None:
        """
        Initialize the model by loading the model file
        Args: args (dict): The arguments passed to the model
        """
        if not isinstance(args, dict):
            logger.error("Invalid arguments")
            raise ValueError("Invalid arguments")
        if args.get("model_config") is None:
            logger.error("Model config is required")
            raise ValueError("Model config is required")

        args = self._get_model_config(args)
        super().initialize(args)

    def execute(self, requests: list) -> Any:
        """
        Process inference requests.
        Args: requests (list): A list of inference requests
        """
        return super().execute(requests)

    def finalize(self) -> None:
        """
        Clean up the model
        """
        super().finalize()
