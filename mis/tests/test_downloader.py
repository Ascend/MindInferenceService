# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import unittest
from unittest.mock import patch
from pathlib import Path

from mis.envs import MIS_CACHE_PATH, MIS_FORCE_DOWNLOAD_MODEL
from mis.hub.downloader import ModelerDownloader


class TestDownloader(unittest.TestCase):
    def setUp(self):
        self.raw_model = "MindSDK/Deepseek-R1-Distill-Qwen-1.5B"
        self.abs_model_path = Path(MIS_CACHE_PATH).joinpath(self.raw_model)

    def tearDown(self):
        if self.abs_model_path.exists():
            for file in self.abs_model_path.iterdir():
                file.unlink()
            self.abs_model_path.rmdir()

    @patch("mis.hub.downloader.logger")
    def test_get_model_path_exists(self, mock_logger):
        # The simulated directory already exists and contains files
        self.abs_model_path.mkdir(parents=True, exist_ok=True)
        with open(self.abs_model_path / "dummy_file", "w") as f:
            f.write("dummy")

        path = ModelerDownloader.get_model_path(self.raw_model)
        self.assertEqual(path, str(self.abs_model_path))
        mock_logger.info.assert_called_with(f"Found model weight cached in path {self.abs_model_path}, "
                                            f"local model weight will be used")

    @patch("openmind_hub.snapshot_download")
    def test_get_model_path_force_download(self, mock_snapshot_download):
        # Simulate forced download, but cannot authorize config.json file
        mock_snapshot_download.return_value = None
        self.abs_model_path.mkdir(parents=True, exist_ok=True)
        with self.assertRaises(Exception):
            path = ModelerDownloader.get_model_path(self.raw_model)


class TestModelerDownloader(unittest.TestCase):
    @patch("mis.hub.downloader.logger")
    @patch("openmind_hub.snapshot_download")
    def test_download_success(self, mock_snapshot_download, mock_logger):
        raw_model = "MindSDK/Deepseek-R1-Distill-Qwen-1.5B"
        cache_dir = "/path/to/cache"

        ModelerDownloader._download(raw_model, cache_dir)
        mock_snapshot_download.assert_called_once_with(
            repo_id=raw_model,
            repo_type=None,
            local_dir=cache_dir,
            local_dir_use_symlinks="False",
            force_download=MIS_FORCE_DOWNLOAD_MODEL,
        )
        mock_logger.info.assert_called_with(f"Downloading model finished, use model weight from {cache_dir}")

    def test_download_import_error(self):
        raw_model = "MindSDK/Deepseek-R1-Distill-Qwen-1.5B"
        cache_dir = "/path/to/cache"
        with patch.dict('sys.modules', {'openmind_hub': None}):
            with self.assertRaises(ImportError):
                ModelerDownloader._download(raw_model, cache_dir)

    @patch("openmind_hub.snapshot_download")
    def test_download_exception(self, mock_snapshot_download):
        raw_model = "MindSDK/Deepseek-R1-Distill-Qwen-1.5B"
        cache_dir = "/path/to/cache"
        mock_snapshot_download.side_effect = Exception("Download failed")

        with self.assertRaises(Exception):
            ModelerDownloader._download(raw_model, cache_dir)


if __name__ == "__main__":
    unittest.main()
