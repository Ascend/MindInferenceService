#!/usr/bin/env python
# coding=utf-8
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
from abc import ABC, abstractmethod
from typing import Any, Dict, Union

import numpy as np


class BaseDataProcessor(ABC):
    """Abstract base class for data processors."""
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the data processor with a configuration.
        Args: config (Dict[str, Any]): The configuration.
        """
        self.config = config

    @abstractmethod
    def process(self, input_data: Union[str, bytes], **kwargs):
        """
        Process input data
        Args: input_data (Union[str, bytes]): The input data.
        """
        pass

    @abstractmethod
    def get_output_info(self) -> Dict[str, Any]:
        """
        Get information about the processed data
        Returns: Dict[str, Any]: The output information.
        """
        pass
