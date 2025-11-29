#!/usr/bin/env python
# coding=utf-8
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import os
from typing import Any, Dict, Union

import numpy as np
try:
    from transformers import AutoTokenizer, BertModel
    import torch
except ImportError as ie:
    raise ImportError("transformers or torch not available, install with: pip install transformers torch") from ie

from ...envs import MIS_CACHE_PATH, MIS_MODEL
from ...logger import init_logger, LogType
from ..model_backends.model_factory import register_data_processor
from ..processor import BaseDataProcessor

logger = init_logger(__name__, log_type=LogType.SERVICE)


DEFAULT_MODEL_PATH = os.path.join(MIS_CACHE_PATH, MIS_MODEL, "bert-base-uncased")  # Default path for the BERT tokenizer
DEFAULT_MAX_LENGTH = 256  # Default maximum length for text sequences
DEFAULT_PADDING = "max_length"  # Default padding strategy for text sequences
DEFAULT_TRUNCATION = True  # Default truncation strategy for text sequences
BATCH_SIZE_INFO = 1  # Batch size shown in the get_output_info


@register_data_processor("text")
class TextProcessor(BaseDataProcessor):
    """Text Processor for BERT text embedding"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the text processor.
        Args: config (Dict[str, Any]): The configuration for the processor.
        """
        super().__init__(config)
        self.model_path = config.get("tokenizer_path", DEFAULT_MODEL_PATH)
        self.max_length = config.get("max_length", DEFAULT_MAX_LENGTH)
        self.padding = config.get("padding", DEFAULT_PADDING)
        self.truncation = config.get("truncation", DEFAULT_TRUNCATION)

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        except Exception as e:
            logger.error(f"Failed to load BERT model or tokenizer: {e}")
            raise RuntimeError(f"Failed to load BERT model or tokenizer: {e}") from e

    def process(self, input_data: Union[str, bytes], **kwargs) -> Dict[str, np.ndarray]:
        """
        Process text data to generate input_ids and attention_mask.
        Args: input_data (Union[str, bytes]): The input text data.
        Returns: Dict[str, np.ndarray]: Dictionary containing input_ids and attention_mask as numpy arrays.
        """
        logger.debug("Processing text data")
        if isinstance(input_data, bytes):
            text = input_data.decode('utf-8')
        else:
            text = input_data
            
        if not isinstance(text, str):
            logger.error("Input text must be a string or bytes")
            raise TypeError("Input text must be a string or bytes")
            
        # Tokenize the text
        tokens = self.tokenizer(
            text,
            max_length=self.max_length,
            padding=self.padding,
            truncation=self.truncation,
            return_tensors="pt"
        )
        
        # Get BERT embeddings
        with torch.no_grad():
            # We'll return the tokens (input_ids and attention_mask) as numpy arrays
            # The actual embeddings will be computed in the model
            input_ids = tokens['input_ids'].numpy()
            attention_mask = tokens['attention_mask'].numpy()
            
        logger.debug("Text processed")
        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
        }

    def get_output_info(self) -> Dict[str, Any]:
        return {
            "input_ids_shape": [BATCH_SIZE_INFO, self.max_length],
            "attention_mask_shape": [BATCH_SIZE_INFO, self.max_length],
            "dtype": "int64",
            "type": "text_tensor"
        }