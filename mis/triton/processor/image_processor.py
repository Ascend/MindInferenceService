#!/usr/bin/env python
# coding=utf-8
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
from typing import Any, Dict, Union

import numpy as np
import torch
import torchvision.transforms as transforms
from io import BytesIO
from PIL import Image

from ...logger import init_logger, LogType
from ..model_backends.model_factory import register_data_processor
from ..processor import BaseDataProcessor


logger = init_logger(__name__, log_type=LogType.SERVICE)
DEFAULT_TARGET_SIZE = (224, 224)  # Default target size for image resizing
DEFAULT_NORMALIZE = True  # Default flag for image normalization
DEFAULT_MEAN = [0.485, 0.456, 0.406]  # Default mean values for image normalization of ImageNet
DEFAULT_STD = [0.229, 0.224, 0.225]  # Default standard deviation values for image normalization of ImageNet
DEFAULT_CHANNEL_ORDER = "RGB"  # Default channel order for image processing
DEFAULT_DTYPE = "float32"  # Default data type for image processing
BATCH_SIZE_INFO = 1  # Batch size shown in the get_output_info
CHANNEL_SIZE = 3  # Channel size for prcessed image


@register_data_processor("image")
class ImageProcessor(BaseDataProcessor):
    """Image Processor"""
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the audio processor.
        Args: config (Dict[str, Any]): The configuration for the processor.
        """
        super().__init__(config)
        self.target_size = config.get("target_size", DEFAULT_TARGET_SIZE)
        self.normalize = config.get("normalize", DEFAULT_NORMALIZE)
        self.mean = np.array(config.get("mean", DEFAULT_MEAN))
        self.std = np.array(config.get("std", DEFAULT_STD))
        self.channel_order = config.get("channel_order", DEFAULT_CHANNEL_ORDER)
        self.dtype = getattr(np, config.get("dtype", DEFAULT_DTYPE))

        transform_list = [transforms.Resize(self.target_size),]

        if self.channel_order == "RGB":
            transform_list.append(transforms.Lambda(lambda x: x.convert('RGB') if x.mode != 'RGB' else x))

        transform_list.extend([transforms.ToTensor(),])

        if self.normalize:
            transform_list.append(transforms.Normalize(mean=self.mean, std=self.std))

        self.transform = transforms.Compose(transform_list)

    def process(self, input_data: Union[str, bytes], **kwargs) -> torch.Tensor:
        """
        Process image data.
        Args: input_data (Union[str, bytes]): The input image data.
        Returns: np.ndarray: The processed image data.
        """
        logger.debug("Processing image data")
        if isinstance(input_data, str):
            # Load image from file path
            with Image.open(input_data) as image:
                processed_image = self.transform(image)
        elif isinstance(input_data, bytes):
            # Load image from bytes
            with BytesIO(input_data) as byte_stream:
                with Image.open(byte_stream) as image:
                    processed_image = self.transform(image)
        else:
            logger.error("Unsupported input type")
            raise TypeError("Unsupported input type")

        # Convert to target dtype and add batch dimension
        processed_image = processed_image.to(dtype=torch.from_numpy(np.array([0], dtype=self.dtype)).dtype)

        # Add batch dimension
        processed_image = processed_image.unsqueeze(0)
        return processed_image

    def get_output_info(self) -> Dict[str, Any]:
        return {
            "shape": [BATCH_SIZE_INFO, CHANNEL_SIZE, self.target_size[0], self.target_size[1]],
            "dtype": self.dtype.__name__,
            "type": "image_tensor"
        }
