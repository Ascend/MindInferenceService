#!/usr/bin/env python
# coding=utf-8
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import os
from typing import Any, Dict, List, Optional

import numpy as np
try:
    from ais_bench.infer.interface import InferSession
except ImportError as ie:
    raise ImportError(f"ais_bench not available: {ie}, please install ais-bench") from ie

from .....logger import init_logger, LogType
from ....model_backends import BaseModelLoader, BaseModelInferer
from ....model_backends.model_factory import register_model_loader, register_model_inferer


logger = init_logger(__name__, log_type=LogType.SERVICE)


MEMORY_CUSTOM_SIZES = 50 * 1024 * 1024


@register_model_loader("ascend_om")
class AscendOMModelLoader(BaseModelLoader):
    """OM Model Loader"""
    def __init__(self, **kwargs):
        """
        Initialize the OM model loader.
        """
        self.device_id = None
        self.model_session: Optional[InferSession] = None
        self.model_path: Optional[str] = None

    def load_model(self, model_path: str, device_id: int = 0, **kwargs) -> InferSession:
        """
        Load OM model
        Args:
            model_path (str): The path to the OM model Repository.
            device_id (int): The device ID to load the model on.
        Returns: InferSession: The loaded model session.
        """
        logger.debug(f"Loading model")
        device_id = int(device_id)
        model_path = os.path.join(model_path, "model.om")
        try:
            self.model_session = InferSession(
                device_id,
                model_path,
                **kwargs
            )
            self.device_id = device_id
            self.model_path = model_path
            logger.info(f"Successfully loaded OM model: {model_path}")
            return self.model_session
        except Exception as e:
            logger.error(f"Failed to load OM model {model_path}: {e}")
            raise RuntimeError("Failed to load OM model") from e

    def unload_model(self) -> None:
        """Unload the model."""
        logger.debug("Prepare to unloading model")
        if self.model_session:
            # ais_bench will release the model automatically
            self.model_session = None
            self.model_path = None
            logger.info("Model unloaded")

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get model information if the model is loaded.
        Returns: Dict[str, Any]: The model information.
        """
        if not self.model_session:
            logger.error("Model not loaded")
            raise RuntimeError("Model not loaded")

        info = {
            "model_path": self.model_path,
            "device_id": self.device_id,
            "inputs": [],
            "outputs": []
        }

        for idx, input_info in enumerate(self.model_session.get_inputs()):
            info["inputs"].append({
                "index": idx,
                "name": input_info.name,
                "shape": input_info.shape,
                "size": input_info.size,
                "realsize": input_info.realsize,
                "datatype": input_info.datatype,
                "format": input_info.format
            })

        for idx, output_info in enumerate(self.model_session.get_outputs()):
            info["outputs"].append({
                "index": idx,
                "name": output_info.name,
                "shape": output_info.shape,
                "size": output_info.size,
                "realsize": output_info.realsize,
                "dtype": output_info.datatype,
                "format": output_info.format
            })

        return info


@register_model_inferer("ascend_om")
class AscendOMModelInferer(BaseModelInferer):
    """AscendOM Model Inferer"""

    def __init__(self, model_loader: AscendOMModelLoader,
                 infer_mode: str = "static",
                 custom_sizes: int = MEMORY_CUSTOM_SIZES,
                 **kwargs) -> None:
        """
        Initialize the AscendOM model inferer.
        Args: model_loader (AscendOMModelLoader): The model loader.
        """
        super().__init__(model_loader, **kwargs)
        if not isinstance(model_loader, AscendOMModelLoader):
            logger.error("model_loader must be AscendOMModelLoader")
            raise TypeError("model_loader must be AscendOMModelLoader")
        self.infer_mode = infer_mode
        self.custom_sizes = custom_sizes

    def infer(self, inputs: List[np.ndarray], **kwargs) -> List[np.ndarray]:
        """
        Infer with the model.
        Args: inputs (List[np.ndarray]): The input data.
        Returns: List[np.ndarray]: The output data.
        """
        logger.debug("Prepare to infer")
        try:
            model_session = self.model_loader.model_session
            if not model_session:
                logger.error("Model not loaded")
                raise RuntimeError("Model not loaded")

            outputs = model_session.infer(
                inputs,
                mode=kwargs.get("infer_mode", self.infer_mode),
                custom_sizes=kwargs.get("custom_sizes", self.custom_sizes),
            )

            if isinstance(outputs, np.ndarray):
                outputs = [outputs]
            logger.debug("Infer done")
            return outputs
        except Exception as e:
            logger.error(f"Inference failed: {e}")
            raise RuntimeError(f"Inference failed: {e}") from e
