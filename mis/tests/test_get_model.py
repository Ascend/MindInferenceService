# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import os
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch

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


if __name__ == '__main__':
    unittest.main()
