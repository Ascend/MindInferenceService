#!/usr/bin/env python
# coding=utf-8
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import importlib

from ...logger import init_logger, LogType
from ..model_backends import BaseModelLoader, BaseModelInferer
from ..processor import BaseDataProcessor


logger = init_logger(__name__, log_type=LogType.SERVICE)


ALLOWED_MODULES = {
    "mis.triton.model_backends.model_backend.ascend_om",
    "mis.triton.processor.funasr_audio_processor",
    "mis.triton.processor.image_processor",
    "mis.triton.processor.text_processor",
}

MODEL_LOADERS = {}
MODEL_INFERERS = {}
DATA_PROCESSORS = {}


def register_model_loader(backend_type: str):
    def decorator(cls):
        if backend_type in MODEL_LOADERS:
            logger.warning(f"Overwriting existing model loader for type: {backend_type}")
        MODEL_LOADERS[backend_type] = cls
        return cls
    return decorator


def register_model_inferer(backend_type: str):
    def decorator(cls):
        if backend_type in MODEL_INFERERS:
            logger.warning(f"Overwriting existing model inferer for type: {backend_type}")
        MODEL_INFERERS[backend_type] = cls
        return cls
    return decorator


def register_data_processor(modal_type: str):
    def decorator(cls):
        if modal_type in DATA_PROCESSORS:
            logger.warning(f"Overwriting existing data processor for type: {modal_type}")
        DATA_PROCESSORS[modal_type] = cls
        return cls
    return decorator


class ModelFactory:
    """Factory for creating model loaders and inferers."""
    @staticmethod
    def create_model_loader(backend_type: str, **config) -> BaseModelLoader:
        """
        Create a model loader based on the backend type.
        Args: backend_type (str): The backend type.
        Returns: BaseModelLoader: The created model loader.
        """
        if backend_type not in MODEL_LOADERS:
            ModelFactory._import_module(f"mis.triton.model_backends.model_backend.{backend_type}")
        loader_class = MODEL_LOADERS.get(backend_type)
        if not loader_class:
            logger.error(f"Unsupported backend type: {backend_type}")
            raise ValueError(f"Unsupported backend type: {backend_type}")
        return loader_class(**config)

    @staticmethod
    def create_model_inferer(backend_type: str, model_loader: BaseModelLoader, **config) -> BaseModelInferer:
        """
        Create a model inferer based on the backend type.
        Args: backend_type (str): The backend type.
              model_loader (BaseModelLoader): The model loader.
        Returns: BaseModelInferer: The created model inferer.
        """
        if backend_type not in MODEL_INFERERS:
            ModelFactory._import_module(f"mis.triton.model_backends.model_backend.{backend_type}")
        inferer_class = MODEL_INFERERS.get(backend_type)
        if not inferer_class:
            logger.error(f"Unsupported backend type: {backend_type}")
            raise ValueError(f"Unsupported backend type: {backend_type}")
        return inferer_class(model_loader, **config)

    @staticmethod
    def create_data_processor(modal_type: str, **config) -> BaseDataProcessor:
        """
        Create a data processor based on the data type.
        Args: modal_type (str): The data type.
              **config (dict): The configuration for the data processor.
        Returns: BaseDataProcessor: The created data processor.
        """
        if modal_type not in DATA_PROCESSORS:
            ModelFactory._import_module(f"mis.triton.processor.{modal_type}_processor")
        processor_class = DATA_PROCESSORS.get(modal_type)
        if not processor_class:
            logger.error(f"Unsupported data type: {modal_type}")
            raise ValueError(f"Unsupported data type: {modal_type}")
        return processor_class(config)

    @staticmethod
    def _import_module(module_name):
        if module_name not in ALLOWED_MODULES:
            raise ValueError(f"Module {module_name} is not allowed to be imported.")
        try:
            importlib.import_module(module_name)
        except ImportError as e:
            logger.error(f"Failed to import module {module_name}: {e}")
            raise ImportError(f"Failed to import module {module_name}: {e}") from e
