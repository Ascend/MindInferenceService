# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import os
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from mis.utils.utils import get_model_path


class TestGetModelPath(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path("/mock/cache/path")
        self.raw_model = "test_model"

        if not self.temp_dir.exists():
            self.temp_dir.mkdir(parents=True, exist_ok=True)

        test_model_path = self.temp_dir.joinpath(self.raw_model)
        if not test_model_path.exists():
            test_model_path.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    @patch('mis.utils.utils.envs')
    def test_existing_model(self, mock_envs):
        mock_envs.MIS_CACHE_PATH = '/mock/cache/path'
        expected_path = str(self.temp_dir.joinpath(self.raw_model))
        result = get_model_path(self.raw_model)
        self.assertEqual(result, expected_path)

    def test_nonexistent_model(self):
        non_existent_model = "non_existent_model"
        with self.assertRaises(FileNotFoundError):
            get_model_path(non_existent_model)

    def test_symlink_model(self):
        symlink_path = self.temp_dir.joinpath("symlink")
        os.symlink(self.temp_dir, symlink_path)
        with self.assertRaises(FileNotFoundError):
            get_model_path(str(symlink_path))

    @patch('os.access')
    def test_unreadable_model(self, mock_access):
        unreadable_dir = self.temp_dir.joinpath("unreadable")
        unreadable_dir.mkdir()
        os.chmod(unreadable_dir, 0o000)

        # Mock os.access to return False, simulating a permission error
        mock_access.return_value = False

        with self.assertRaises(PermissionError):
            get_model_path(str(unreadable_dir))

    @patch('os.getuid')
    @patch('os.stat')
    def test_owner_check_success(self, mock_stat, mock_getuid):
        mock_getuid.return_value = 1000

        mock_stat.return_value = MagicMock(st_uid=1000)

        abs_model_path = "/mnt/nfs/data/models/Qwen3-8B"
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.is_dir', return_value=True), \
             patch('pathlib.Path.is_symlink', return_value=False), \
             patch('os.access', return_value=True), \
             patch('pathlib.Path.stat', return_value=MagicMock(st_mode=0o40755)):

            result = get_model_path("Qwen3-8B")
            self.assertEqual(result, abs_model_path)

    @patch('os.getuid')
    @patch('os.stat')
    def test_owner_check_failed(self, mock_stat, mock_getuid):
        mock_getuid.return_value = 1000

        mock_stat.return_value = MagicMock(st_uid=2000)

        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.is_dir', return_value=True), \
             patch('pathlib.Path.is_symlink', return_value=False), \
             patch('os.access', return_value=True), \
             patch('pathlib.Path.stat', return_value=MagicMock(st_mode=0o40755)):

            with self.assertRaises(OSError) as cm:
                get_model_path("Qwen3-8B")
            self.assertEqual(str(cm.exception), "Error checking ownership of file path.")

    @patch('os.getuid')
    @patch('os.stat')
    def test_owner_check_os_error(self, mock_stat, mock_getuid):
        mock_getuid.return_value = 1000

        mock_stat.side_effect = OSError("Cannot access file")

        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.is_dir', return_value=True), \
             patch('pathlib.Path.is_symlink', return_value=False), \
             patch('os.access', return_value=True), \
             patch('pathlib.Path.stat', return_value=MagicMock(st_mode=0o40755)):

            with self.assertRaises(OSError) as cm:
                get_model_path("Qwen3-8B")
            self.assertEqual(str(cm.exception), "Error checking ownership of file path.")


if __name__ == '__main__':
    unittest.main()
