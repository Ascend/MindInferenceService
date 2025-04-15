# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import abc
import os
from pathlib import Path

import mis.envs as envs
from mis.logger import init_logger
from mis.utils.utils import _set_config_perm

logger = init_logger(__name__)


class Downloader(abc.ABC):
    @classmethod
    def get_model_path(cls, raw_model: str) -> str:
        """Get model path from raw_model.
                given raw_model a `MindSDK/Deepseek-R1-Distill-Qwen-1.5B` style str, this function will find
                    absolute path of exist model or download model to that path.
                return this absolute path.
        """
        abs_model_path = Path(envs.MIS_CACHE_PATH).joinpath(raw_model)
        logger.info(f"Local model path is {abs_model_path}")

        if not abs_model_path.exists():
            try:
                abs_model_path.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                raise OSError(f"Failed to create cache path {abs_model_path},"
                              f"please check if the path and the parent path is valid.") from e

        if not abs_model_path.is_dir():
            raise NotADirectoryError(f"Local model path {abs_model_path} is not a directory.")

        # if no file in this dir or force download model
        if not any(abs_model_path.iterdir()) or envs.MIS_FORCE_DOWNLOAD_MODEL:
            cls._download(raw_model, str(abs_model_path))
            _set_config_perm(str(abs_model_path), mode=0o750)
        else:
            logger.info(f"Found model weight cached in path {abs_model_path}, local model weight will be used")

        return str(abs_model_path)

    @classmethod
    @abc.abstractmethod
    def _download(cls, raw_model: str, cache_dir: str):
        raise NotImplementedError(f"{cls.__name__} method `download` not implement.")


class ModelerDownloader(Downloader):
    @classmethod
    def _download(cls, raw_model: str, cache_dir: str):
        logger.info("Downloading model from modeler, please waiting...")
        os.environ["HUB_WHITE_LIST_PATHS"] = envs.MIS_CACHE_PATH
        try:
            from openmind_hub import snapshot_download

            snapshot_download(
                repo_id=raw_model,
                repo_type=None,
                local_dir=cache_dir,
                local_dir_use_symlinks="False",
                force_download=envs.MIS_FORCE_DOWNLOAD_MODEL,
            )

            logger.info(f"Downloading model finished, use model weight from {cache_dir}")
            return cache_dir
        except ImportError as e:
            raise ImportError("Please install openmind_hub for model download.") from e
        except Exception as e:
            raise Exception(f"Download model failed.") from e
