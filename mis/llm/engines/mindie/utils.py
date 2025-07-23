# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import os

from mis.constants import ASCEND_PATH, MIS_BASE_PATH
from mis.logger import init_logger
from mis.utils.utils import read_json, write_json, set_config_perm

logger = init_logger(__name__)

DST_PATH = f"{MIS_BASE_PATH}/.cache/MindIE"
ATB_MINICPM_QWEN2_PATH = f"{ASCEND_PATH}/atb/atb_llm/models/minicpm_qwen2_v2"


class ConfigTypeConverter:
    def __init__(self, model_path: str) -> None:
        """
        Initialize the config converter

        :param model_path: Path to model config file
        """
        model_name = os.path.basename(model_path)
        self.model_path = model_path
        self.link_dir = os.path.join(DST_PATH, model_name)
        self.config_path_raw = os.path.join(model_path, 'config.json')
        self.config_path_link = os.path.join(self.link_dir, 'config.json')
        self.config_data = None

    def safe_convert(self) -> str:
        """
        Safely convert data types with backup and error recovery
        """
        try:
            self.config_data = read_json(self.config_path_raw)
            if self._torch_dtype_convert():
                self._create_symbolic_link()
                write_json(self.config_path_link, self.config_data)
                set_config_perm(self.link_dir, mode=0o750)
                self.model_path = self.link_dir

        except Exception as e:
            logger.error(f"Data type conversion failed: {str(e)}")
            raise RuntimeError("Data type conversion failed") from e
        return self.model_path

    def _create_symbolic_link(self) -> None:
        os.makedirs(self.link_dir, exist_ok=True)
        for item in os.listdir(self.model_path):
            if item != 'config.json':
                src_file = os.path.join(self.model_path, item)
                dst_file = os.path.join(self.link_dir, item)
                if not os.path.islink(dst_file):
                    os.symlink(src_file, dst_file)

    def _torch_dtype_convert(self) -> bool:
        """
        Convert model config
        """
        if self.config_data is None:
            logger.error("No model config data loaded")
            raise RuntimeError("No model config data to convert")

        torch_dtype = self.config_data.get("torch_dtype")
        if torch_dtype is None:
            logger.error("Please check torch_dtype in model config, ")
            raise ValueError("Please check torch_dtype in model config, ")

        elif torch_dtype == "bfloat16":
            self.config_data["torch_dtype"] = "float16"
            logger.info("Converted dtype at key torch_dtype: bfloat16 → float16. "
                        "MindIE-Service Backend on 310P Platform only supports float16")
            return True
        return False


def atb_link_to_model_path(model_path: str) -> None:
    try:
        dst_file = os.path.join(ATB_MINICPM_QWEN2_PATH, "resampler.py")
        src_file = os.path.join(model_path, "resampler.py")
        if os.path.exists(src_file) and not os.path.exists(dst_file) and not os.path.islink(dst_file):
            os.symlink(src_file, dst_file)
            logger.info(f"Create symbolic link {dst_file} to {src_file}")
    except Exception as e:
        logger.error(f"Create symbolic link failed: {str(e)}. "
                     f"Please check whether the MiniCPM-V-2_6 model repository contains resampler.py. ")
        raise RuntimeError("Create symbolic link failed. "
                           "Please check whether the MiniCPM-V-2_6 model repository contains resampler.py. ") from e
