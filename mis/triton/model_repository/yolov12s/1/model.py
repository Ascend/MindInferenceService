#!/usr/bin/env python
# coding=utf-8
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
from typing import Any, Dict

# Since the model_repository/{model_name} is treated as a separate component in the Triton service,
# an absolute reference method is used.
from mis.logger import init_logger, LogType
from mis.triton.model_backends.model import BaseTritonPythonModel

logger = init_logger(__name__, log_type=LogType.SERVICE)


class TritonPythonModel(BaseTritonPythonModel):
    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def _get_default_parameters() -> Dict[str, Any]:
        """
        Get default parameters for the YoloV12 model.
        Returns: Dict containing default parameters
        """
        return {
            "backend_type": {"string_value": "ascend_om"},
            "modal_type_list": {"string_value": ["image"]},
            "backend_config": {"string_value": {"device_id": 0}},
            "infer_config": {"string_value": {"infer_mode": "static"}},
            "processor_config": {"string_value": {"target_size": [640, 640]}}
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
