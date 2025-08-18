# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.

import argparse
import logging
import os
import shutil

from mis.args import ARGS
from mis.llm.engines.config import ConfigParser
from mis.logger import init_logger
from mis.utils.utils import check_files_number, check_file_size

logger = init_logger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
logger.addHandler(handler)

CONFIG_CACHE_PATH = '/opt/mis/.cache/configs'
MAX_CONFIG_FILE_COUNT = 100
MAX_CONFIG_FILE_SIZE = 1 * 1024 * 1024  # 1MB


def _parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(description="Export configuration files from the model folder to the cache path.")
    parser.add_argument('--disable-print-config-ranges', action='store_true',
                        help='Disable to print configuration ranges')
    return parser.parse_args()


def _create_export_path(model_type: str) -> str:
    """
    Ensure the export root path exists and create the export path and
    :param model_type: The type of the model
    :return: The export path
    """
    if not os.path.exists(CONFIG_CACHE_PATH):
        logger.error(f"Export path {CONFIG_CACHE_PATH} does not exist. "
                     f"please mount the export path: docker run ... -v /path/to/configs:{CONFIG_CACHE_PATH} ...")
        raise OSError(f"Export path {CONFIG_CACHE_PATH} does not exist. "
                      f"please mount the export path: docker run ... -v /path/to/configs:{CONFIG_CACHE_PATH} ...")
    export_path = os.path.join(CONFIG_CACHE_PATH, model_type)
    if not os.path.exists(export_path):
        try:
            os.mkdir(export_path)
        except OSError as e:
            logger.error(f"Error creating export path {export_path}: {e}")
            raise OSError(f"Error creating export path {export_path}: {e}") from e
    return export_path


def _export_yaml_files(model_folder_path: str, export_path: str) -> None:
    """
    Export YAML files from the model folder to the export path.
    :param model_folder_path: The path to the model folder
    :param export_path: The path to the export folder
    """
    yaml_files = [f for f in os.listdir(model_folder_path) if f.endswith('.yaml')]
    check_files_number(yaml_files, MAX_CONFIG_FILE_COUNT)
    for yaml_file in yaml_files:
        src_file = os.path.join(model_folder_path, yaml_file)
        dst_file = os.path.join(export_path, yaml_file)
        check_file_size(src_file, MAX_CONFIG_FILE_SIZE)
        if os.path.exists(dst_file):
            logger.info(f"File {yaml_file} already exists in {export_path}, skipping.")
            continue
        try:
            shutil.copy(src_file, dst_file)
            logger.info(f"Exported {yaml_file} to {export_path}")
        except IOError as e:
            logger.error(f"Error exporting {yaml_file}: {e}")
            raise IOError(f"Error exporting {yaml_file}: {e}") from e


def main() -> None:
    """
    Export configuration files from the model folder to the cache path.
    """

    args = _parse_arguments()

    configparser = ConfigParser(ARGS)
    if not args.disable_print_config_ranges:
        configparser.print_config_ranges()

    export_path = _create_export_path(configparser.model_type.lower())
    _export_yaml_files(configparser.model_folder_path, export_path)


if __name__ == "__main__":
    main()
