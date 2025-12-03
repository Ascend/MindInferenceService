#!/usr/bin/env python
# coding=utf-8
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import math
from typing import Any, ClassVar, Dict, Optional, Union

from fastapi import HTTPException
from vllm.entrypoints.openai.protocol import ChatCompletionRequest
from vllm.entrypoints.openai.serving_chat import OpenAIServingChat

from mis.logger import init_logger, LogType
from mis.utils.utils import ConfigChecker

logger = init_logger(__name__, log_type=LogType.SERVICE)

# MIS chat completion supported fields
MIS_CHAT_COMPLETION_WHITELIST = {
    # openai params
    "frequency_penalty",
    "max_tokens",
    "messages",
    "min_tokens",
    "model",
    "presence_penalty",
    "seed",
    "stream",
    "temperature",
    "top_p",

    # vLLM params
    "max_completion_tokens",  # backward compatibility
}

# MIS chat completion field validators
MIS_CHAT_COMPLETION_FIELD_VALIDATORS: Dict[str, Dict[str, Any]] = {
    "frequency_penalty": {
        "type": float,
        "min": -2.0,
        "max": 2.0
    },
    "max_tokens": {
        "type": int,
        "min": 1,
        "max": 64000
    },
    "min_tokens": {
        "type": int,
        "min": 0,
        "max": 64000
    },
    "presence_penalty": {
        "type": float,
        "min": -2.0,
        "max": 2.0
    },
    "seed": {
        "type": int,
        "min": -65535,
        "max": 65535
    },
    "stream": {
        "type": bool
    },
    "temperature": {
        "type": float,
        "min": 0.0,
        "max": 2.0
    },
    "top_p": {
        "type": float,
        "min": 1e-8,
        "max": 1.0
    },
    "max_completion_tokens": {
        "type": int,
        "min": 1,
        "max": 64000
    },
}


class MISChatCompletionRequest(ChatCompletionRequest):
    model_post_init: ClassVar[Any]

    def __init__(self, **kwargs: Any) -> None:
        logger.debug("Initializing MISChatCompletionRequest with parameters")
        used_kwargs = {}
        for key in kwargs:
            if key in MIS_CHAT_COMPLETION_WHITELIST:
                used_kwargs[key] = kwargs[key]
            else:
                logger.warning(f"MIS chat completion ignore invalid param: {key}.")
        self._remove_invalid_messages(used_kwargs)
        validated_kwargs = self._validate_parameters(used_kwargs)
        super().__init__(**validated_kwargs)
        logger.debug("MISChatCompletionRequest initialized successfully.")

    @staticmethod
    def _remove_invalid_messages(kwargs: Dict[str, Any]) -> None:
        """
        Service only accept role in [system, assistant, user]
        """
        logger.debug("Removing invalid messages from request.")
        roles = ("system", "assistant", "user")
        message_keys_keep = ("role", "content")
        if "messages" not in kwargs:
            logger.error("Can't find any message in request")
            raise HTTPException(
                status_code=400,
                detail="Can't find any message in request"
            )
        if not isinstance(kwargs["messages"], list):
            logger.error(f"Messages must be a list, but get {type(kwargs['messages'])}")
            raise HTTPException(status_code=400,
            detail=f"Messages must be a list, but get {type(kwargs['messages'])}")

        new_messages = []
        for message in kwargs["messages"]:
            if not isinstance(message, dict) or not isinstance(message.get("content"), str):
                continue
            if "role" in message and message["role"] in roles:
                message = {key: value for key, value in message.items() if key in message_keys_keep}
                new_messages.append(message)
            else:
                logger.warning("MIS chat completions only accept role in [system, assistant, user]")
        if not new_messages:
            logger.error("MIS chat completions require at least one valid message")
            raise HTTPException(status_code=400,
                                detail="MIS chat completions require at least one valid message"
                                )
        kwargs["messages"] = new_messages
        logger.debug("Invalid messages removed successfully.")

    @staticmethod
    def _validate_range(param_name: str, value: Union[int, float], validator: Dict[str, Any]) -> Optional[Any]:
        logger.debug(f"Validating range for parameter {param_name}.")
        # Range checking
        min_value = validator.get("min")
        max_value = validator.get("max")

        if isinstance(value, float) and math.isnan(value):
            logger.error(f"Invalid value for {param_name}: NaN (Not a Number) is not allowed")
            raise HTTPException(status_code=400,
                                detail=f"Invalid value for {param_name}: NaN (Not a Number) is not allowed"
                                )
        if min_value is not None and max_value is not None:
            if min_value > max_value:
                logger.error(f"Invalid range for {param_name}: min({min_value}) > max({max_value})")
                raise HTTPException(status_code=400,
                                    detail=f"Invalid range for {param_name}: min({min_value}) > max({max_value})"
                                    )
            if not ConfigChecker.is_value_in_range(param_name, value, min_value, max_value):
                logger.error(f"Invalid value for {param_name}: not in [{min_value}, {max_value}]")
                raise HTTPException(status_code=400,
                                    detail=f"Invalid value for {param_name}: not in [{min_value}, {max_value}]"
                                    )
        elif min_value is not None:
            if value < min_value:
                logger.error(f"Invalid value for {param_name}: less than min({min_value})")
                raise HTTPException(status_code=400,
                                    detail=f"Invalid value for {param_name}: less than min({min_value})"
                                    )
        elif max_value is not None:
            if value > max_value:
                logger.error(f"Invalid value for {param_name}: greater than max({max_value})")
                raise HTTPException(status_code=400,
                                    detail=f"Invalid value for {param_name}: greater than max({max_value})"
                                    )
        logger.debug(f"Parameter {param_name} validated range successfully.")
        return value

    @staticmethod
    def _validate_bool(param_name: str, value: Any) -> Union[bool, str, None]:
        logger.debug(f"Validating boolean parameter {param_name}.")
        if isinstance(value, bool) or (isinstance(value, str) and value.lower() in ['true', 'false']):
            logger.debug(f"Parameter {param_name} is valid.")
            return value
        logger.error(f"Invalid type for {param_name}: expected bool")
        raise HTTPException(status_code=400,
                            detail=f"Invalid type for {param_name}: expected bool"
                            )

    @staticmethod
    def _validate_enum(param_name: str, value: Any, validator: Dict[str, Any]) -> Optional[Any]:
        logger.debug(f"Validating enum parameter {param_name}.")
        valid_values = validator.get("valid_values", None)
        if valid_values is not None:
            if ConfigChecker.is_value_in_enum(param_name, value, valid_values):
                return value
        logger.error(f"Invalid value for {param_name}: not in {valid_values}")
        raise HTTPException(status_code=400,
                            detail=f"Invalid value for {param_name}: not in {valid_values}"
                            )

    def model_post_init(self, __context: Any) -> None:
        if getattr(self, "top_logprobs", None) == 0:
            setattr(self, "top_logprobs", None)

    def _validate_single_parameter(self, param_name: str, value: Any, validator: Dict[str, Any]) -> Optional[Any]:
        """
        Validate a single parameter

        Args:
            param_name: Parameter name
            value: Parameter value
            validator: Validation rules

        Returns:
            Validated value, None if validation fails
        """
        logger.debug(f"Validating single parameter {param_name}.")
        # Type conversion
        expected_type = validator.get("type")
        if expected_type == bool and isinstance(value, expected_type):
            value = self._validate_bool(param_name, value)
        elif expected_type in [int, float] and isinstance(value, expected_type) and not isinstance(value, bool):
            value = self._validate_range(param_name, value, validator)
        elif expected_type == str and isinstance(value, expected_type):
            value = self._validate_enum(param_name, value, validator)
        else:
            logger.error(f"Unsupported type for {param_name}, expected: {expected_type.__name__}")
            raise HTTPException(status_code=400,
                                detail=f"Unsupported type for {param_name}, expected: {expected_type.__name__}"
                                )
        logger.debug(f"Parameter {param_name} validated successfully.")
        return value

    def _validate_parameters(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate if parameters conform to specifications

        Args:
            kwargs: Parameter dictionary

        Returns:
            Validated parameter dictionary
        """
        logger.debug("Validating request parameters.")
        validated_kwargs = {}

        for key, value in kwargs.items():
            if value is None:
                logger.error(f"Invalid value for {key}: None")
                raise HTTPException(status_code=400,
                                    detail=f"Invalid value for {key}: None"
                                    )
            # If the parameter has validation rules, validate it
            if key in MIS_CHAT_COMPLETION_FIELD_VALIDATORS:
                validator = MIS_CHAT_COMPLETION_FIELD_VALIDATORS[key]
                validated_value = self._validate_single_parameter(key, value, validator)
                validated_kwargs[key] = validated_value
            else:
                # Parameters without validation rules are used directly
                validated_kwargs[key] = value
        logger.debug("Request parameters validated successfully.")
        return validated_kwargs


class MISOpenAIServingMixin:
    pass


class MISOpenAIServingChat(MISOpenAIServingMixin, OpenAIServingChat):
    pass
