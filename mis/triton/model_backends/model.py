#!/usr/bin/env python
# coding=utf-8
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import base64
import os
from typing import List, Dict, Any

import json
import triton_python_backend_utils as pb_utils

from ...envs import MIS_CACHE_PATH, MIS_MODEL
from ...logger import init_logger, LogType
from ...triton.model_backends.model_factory import ModelFactory
from ...utils.utils import convert_string_to_dict

logger = init_logger(__name__, log_type=LogType.SERVICE)


class BaseTritonPythonModel:
    """Triton Python Backend Model Base Class"""

    def __init__(self):
        self.model_loader = None
        self.model_inferer = None
        self.data_processors = {}

        self.model_config = None
        self.backend_type = None
        self.modal_type_list = []

        self.input_name_map = {}
        self.output_name_map = {}

    @staticmethod
    def _extract_model_config(converted_args: Dict[str, Any]) -> Dict[str, Any]:
        """Extract model config from converted args"""
        try:
            return converted_args["model_config"]
        except KeyError as e:
            logger.error(f"Invalid model config: {e}")
            raise KeyError(f"Invalid model config: {e}") from e

    @staticmethod
    def _get_default_parameters() -> Dict[str, Any]:
        """
        Get default parameters for the model.
        Subclasses should override this method to provide model-specific defaults.
        Returns: Dict containing default parameters
        """
        return {}

    @staticmethod
    def _serialize_config(config_data: dict, config_name: str) -> str:
        """
        Serialize the given configuration data to a JSON string.
        Args:
            config_data: Data to be serialized
            config_name: Config name
        Returns:
            str: Serialized JSON string
        """
        try:
            return json.dumps(config_data)
        except ValueError as e:
            logger.error(f"Failed to serialize {config_name}: {e}")
            raise ValueError(f"Failed to serialize {config_name}: {e}") from e
        except Exception as e:
            logger.error(f"Failed to serialize {config_name}: {e}")
            raise Exception(f"Failed to serialize {config_name}: {e}") from e

    @staticmethod
    def _extract_input_data(tensor):
        """Extract input data from tensor"""
        if tensor.ndim == 2 and tensor.shape[1] == 1:
            input_data = tensor[0][0]
        else:
            input_data = tensor[0]

        if isinstance(input_data, bytes):
            input_data = base64.b64decode(input_data).decode('utf-8')
        else:
            input_data = str(input_data)

        return input_data

    @staticmethod
    def _append_processed_result(processed_data, processed_result):
        """Append processed result to the processed data list"""
        if isinstance(processed_result, dict):
            if "speech" in processed_result and "speech_lengths" in processed_result:
                processed_data.append(processed_result["speech"])
                processed_data.append(processed_result["speech_lengths"])
            else:
                processed_data.append(processed_result["input_ids"])
                processed_data.append(processed_result["attention_mask"])
        else:
            processed_data.append(processed_result)

    @staticmethod
    def _get_client_ip(request):
        client_ip = request.get_request_property("client_ip")
        return client_ip

    def initialize(self, args: Dict[str, Any]) -> None:
        """
        Triton model initialize
        Args: args: Dict[str, Any]
        Returns: None
        """
        logger.debug("Initializing model")
        if not isinstance(args, dict):
            logger.error("Invalid args: args not dict")
            raise ValueError("Invalid args: args not dict")

        converted_args = convert_string_to_dict(args)
        self.model_config = self._extract_model_config(converted_args)
        
        parameters = self.model_config.get("parameters")
        if parameters is None:
            logger.error("Invalid model config: parameters not found")
            raise ValueError("Invalid model config: parameters not found")

        self.backend_type = parameters.get("backend_type").get("string_value")
        self.modal_type_list = parameters.get("modal_type_list").get("string_value", [])
        
        backend_config = parameters.get("backend_config").get("string_value", {}) \
            if parameters.get("backend_config") else {}
        processor_config = parameters.get("processor_config").get("string_value", {}) \
            if parameters.get("processor_config") else {}
        infer_config = parameters.get("infer_config").get("string_value", {}) \
            if parameters.get("infer_config") else {}

        self._load_model(backend_config)
        self._create_inferer(infer_config)
        self._create_data_processor(processor_config)
        self._setup_io_map()

        logger.info(f"Model {args['model_name']} initialized successfully")

    def execute(self, requests: list) -> list:
        """
        Execute inference on the model of requests
        Args: requests: List of inference requests
        Returns: List of inference responses
        """
        logger.debug("Model execute")
        if requests is None or len(requests) == 0:
            logger.error("No requests provided")
            raise ValueError("No requests provided")
        responses = []
        for request in requests:
            response = self._process_request(request)
            responses.append(response)
        logger.debug("Model execute done")
        return responses

    def finalize(self):
        """Cleanup any state or resources created by the model."""
        logger.debug("Prepare to finalize")
        if self.model_loader:
            self.model_loader.unload_model()
        logger.info("Model resources released")

    def _get_model_config(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process and validate model configuration.
        Args: args: Arguments passed to the model
        Returns: Processed arguments
        """
        model_config = args["model_config"]
        try:
            model_config = json.loads(model_config)
        except ValueError as e:
            logger.error(f"Failed to parse model config: {e}")
            raise ValueError(f"Failed to parse model config: {e}") from e
        except Exception as e:
            logger.error(f"Failed to parse model config: {e}")
            raise Exception(f"Failed to parse model config: {e}") from e

        parameters = model_config.setdefault("parameters", {})

        default_params = self._get_default_parameters()

        if parameters.get("backend_type") is None and "backend_type" in default_params:
            parameters["backend_type"] = default_params["backend_type"]
        if parameters.get("modal_type_list") is None and "modal_type_list" in default_params:
            parameters["modal_type_list"] = default_params["modal_type_list"]
        if parameters.get("backend_config") is None and "backend_config" in default_params:
            parameters["backend_config"] = self._serialize_config(default_params["backend_config"], "backend_config")
        if parameters.get("processor_config") is None and "processor_config" in default_params:
            parameters["processor_config"] = self._serialize_config(default_params["processor_config"],
                                                                    "processor_config")

        model_config["parameters"] = parameters
        args["model_config"] = self._serialize_config(model_config, "model_config")
        return args

    def _load_model(self, backend_config: Dict[str, Any]) -> None:
        """Load model from file"""
        logger.debug("Load model")
        self.model_loader = ModelFactory.create_model_loader(
            self.backend_type,
            **backend_config
        )

        model_path = os.path.join(MIS_CACHE_PATH, MIS_MODEL)
        self.model_loader.load_model(model_path, **backend_config)

        model_info = self.model_loader.get_model_info()
        logger.info(f"Model loaded: {model_info}")

    def _create_inferer(self, infer_config: Dict[str, Any]) -> None:
        """Create model inferer"""
        logger.debug("Create model inferer")
        self.model_inferer = ModelFactory.create_model_inferer(
            self.backend_type,
            self.model_loader,
            **infer_config
        )

    def _create_data_processor(self, processor_config: Dict[str, Any]) -> None:
        """Create data processor"""
        logger.debug("Create data processor")

        for modality in self.modal_type_list:
            processor = ModelFactory.create_data_processor(modality, **processor_config)
            self.data_processors[modality] = processor

    def _process_request(self, request: list) -> list:
        """Process a single inference request"""
        try:
            logger.debug("Get input tensors")
            input_tensors = self._get_input_tensors(request)
            
            logger.debug("Data processing")
            processed_data = self._process_input_data(input_tensors)

            logger.debug("Model inference")
            outputs = self.model_inferer.infer(processed_data)
            
            logger.debug("Response generation")
            return self._generate_response(outputs)
            
        except Exception as e:
            logger.error(f"Request processing failed: {e}")
            return pb_utils.InferenceResponse(
                error=pb_utils.TritonError(str(e))
            )

    def _get_input_tensors(self, request) -> List:
        """Extract input tensors from request"""
        input_tensors = []
        for name in self.input_name_map:
            tensor = pb_utils.get_input_tensor_by_name(request, name)
            if tensor is None:
                logger.error(f"Input tensor not found: {name}")
                raise ValueError(f"Missing input: {name}")
            input_tensors.append((name, tensor.as_numpy()))
        return input_tensors

    def _process_input_data(self, input_tensors: List) -> List:
        """Process input data"""
        processed_data = []

        for name, tensor in input_tensors:
            if tensor.dtype.kind in ('U', 'S', 'O'):
                input_data = self._extract_input_data(tensor)
            else:
                input_data = tensor
            if name in self.data_processors:
                processor = self.data_processors[name]
                processed_result = processor.process(input_data)
                self._append_processed_result(processed_data, processed_result)
            else:
                processed_data.append(input_data)

        return processed_data

    def _generate_response(self, outputs: list) -> list:
        """Generate response from model outputs"""
        output_tensors = []
        for idx, output_tensor in enumerate(outputs):
            triton_name = self.output_name_map.get(idx)
            output_tensors.append(
                pb_utils.Tensor(triton_name, output_tensor)
            )
        return pb_utils.InferenceResponse(output_tensors)

    def _setup_io_map(self):
        """Setup input/output name map"""
        # Triton input name -> Model input index
        for idx, inp in enumerate(self.model_config["input"]):
            self.input_name_map[inp["name"]] = idx

        # Triton output name -> Model output index
        for idx, outp in enumerate(self.model_config["output"]):
            self.output_name_map[idx] = outp["name"]
