#!/usr/bin/env python
# coding=utf-8
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import os
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock

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
    @patch('pathlib.Path.is_dir', return_value=True)
    @patch('pathlib.Path.is_symlink', return_value=False)
    @patch('pathlib.Path.exists', return_value=True)
    @patch('os.access', return_value=True)
    @patch('os.getuid', return_value=1000)
    @patch('os.getgid', return_value=1000)
    @patch('os.stat')
    @patch('os.path.isdir', return_value=True)
    @patch('grp.getgrgid', return_value=MagicMock(gr_name='user_group'))
    def test_existing_model(self, mock_getgrgid, mock_isdir, mock_stat, mock_getgid, mock_getuid, mock_access,
                            mock_exists, mock_is_symlink, mock_is_dir, mock_envs):
        mock_stat.return_value = Mock(st_uid=1000, st_mode=0o700, st_gid=1000)
        mock_envs.MIS_CACHE_PATH = '/mock/cache/path'
        expected_path = str(self.temp_dir.joinpath(self.raw_model))
        result = get_model_path(self.raw_model)
        self.assertEqual(result, expected_path)

    def test_nonexistent_model(self):
        non_existent_model = "non_existent_model"
        with self.assertRaises(OSError):
            get_model_path(non_existent_model)

    def test_symlink_model(self):
        symlink_path = self.temp_dir.joinpath("symlink")
        os.symlink(self.temp_dir, symlink_path)
        with self.assertRaises(OSError):
            get_model_path(str(symlink_path))

    @patch('os.access')
    def test_unreadable_model(self, mock_access):
        unreadable_dir = self.temp_dir.joinpath("unreadable")
        unreadable_dir.mkdir()
        os.chmod(unreadable_dir, 0o000)

        # Mock os.access to return False, simulating a permission error
        mock_access.return_value = False

        with self.assertRaises(OSError):
            get_model_path(str(unreadable_dir))


if __name__ == '__main__':
    unittest.main()
