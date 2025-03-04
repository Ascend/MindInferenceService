# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import re

import yaml

from mis_llm.logger import init_logger
from mis.args import GlobalArgs

logger = init_logger(__name__)

ROOT_DIR = "mis_llm/configs/"


def check_string_input(input_string: str, input_string_name:str):
    if not isinstance(input_string, str):
        logger.error(f"Invalid {input_string_name} type: {type(input_string)}, only str is supported.")
        raise ValueError(f"Invalid {input_string_name} type: {type(input_string)}, only str is supported.")
    if not input_string.strip():
        logger.error(f"Invalid {input_string_name} cannot be empty")
        raise ValueError(f"Invalid {input_string_name} cannot be empty")
    pattern_risk = '[\n\s]'
    compile_pattern = re.compile(pattern_risk)
    if compile_pattern.search(input_string):
        logger.error(f"The parameter args.{input_string_name} cannot contain newlines or spaces")
        raise ValueError(f"The parameter args.{input_string_name} cannot contain newlines or spaces")


def prepare_engine_config_loading(args: GlobalArgs):
    """ Obtain the engine config. IF the parameters are successfully obtained, update the args.
    :para args: Global parameters
    :return: Update global parameters
    :raises: AttributeError: If args is missing required attributes
    :raises: ValueError: If args.model is not a string.
    :raises: ValueError: If args.model is empty.
    :raises: ValueError: If args.model contain newline characters or spaces.
    """
    config = None
    engine_optimization_config = None

    if not isinstance(args, GlobalArgs):
        logger.error("args must be an instance of GlobalArgs")
        raise("args must be an instance of GlobalArgs")
    
    required_attributes = ["model", "engine_type", "optimization_config_type"]
    for attr in required_attributes:
        if not hasattr(args, attr):
            logger.error(f"args does not contain the {attr} attribute")
            raise AttributeError(f"args does not contain the {attr} attribute")

    if args.model is not None:
        check_string_input(args.model, "model")
        model_type = args.model.split('/')[-1]
    else:
        logger.error("args.model is None")
        raise AttributeError("args.model is None")

    engine_type = args.engine_type
    optimization_config_type = args.optimization_config_type

    if model_type is not None and optimization_config_type is not None:
        check_string_input(optimization_config_type, "optimization_config_type")
        model_type = model_type.replace("-", "_")
        yaml_file_path = f"{model_type.lower()}_{optimization_config_type}.yaml"
        try:
            with open(ROOT_DIR + yaml_file_path, "r") as file:
                config = yaml.safe_load(file)
        except FileNotFoundError:
            logger.warning(f"File {ROOT_DIR + yaml_file_path} not found. "
                           f" The engine will be started with the default parameters")
        except yaml.YAMLError as e:
            logger.error(f"YAML error in file {ROOT_DIR + yaml_file_path}: {e}")
            raise e
        
        if config is not None:
            if engine_type is None:
                engine_type_selected = config.get("optimal_engine_type", None)
            else:
                check_string_input(engine_type, "engine_type")
                engine_type_selected = engine_type

            if engine_type_selected is not None:
                engine_optimization_config = config.get(engine_type_selected)

    else:
        logger.warning("Missing required arguments for the required configuration yaml file."
                       f"The engine will be started with the default parameters")

    args.engine_optimization_config = engine_optimization_config if engine_optimization_config is not None else {}
    return args
