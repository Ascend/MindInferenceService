#!/usr/bin/env python
# coding=utf-8
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
from abc import ABC, abstractmethod
from typing import Any, Dict, List
import numpy as np


class BaseModelLoader(ABC):
    """Abstract base class for model loaders."""

    @abstractmethod
    def load_model(self, model_path: str, **kwargs) -> Any:
        """
        Load a model from the given path.
        Args:
            model_path (str): The path to the model.
        Returns: Any: The loaded model.
        """
        pass

    @abstractmethod
    def unload_model(self) -> None:
        """Unload the loaded model."""
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        pass


class BaseModelInferer(ABC):
    """Abstract base class for model inferers."""

    @abstractmethod
    def __init__(self, model_loader: BaseModelLoader, **kwargs) -> None:
        """
        Initialize the model inferer with a model loader.
        Args: model_loader (BaseModelLoader): The model loader.
        """
        self.model_loader = model_loader

    @abstractmethod
    def infer(self, inputs: List[np.ndarray], **kwargs) -> List[np.ndarray]:
        """
        Model inference operation
        Args: inputs (List[np.ndarray]): The input data.
        Returns: List[np.ndarray]: The output data.
        """
        pass
