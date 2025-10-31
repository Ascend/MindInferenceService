#!/usr/bin/env python
# coding=utf-8
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import os
import unittest
from unittest import mock

import mis.envs as envs
from mis.hub.envpreparation import environment_preparation

MIS_MODEL = "Qwen3-8B"


class TestEnvPreparation(unittest.TestCase):

    def setUp(self):
        # Save the original environment variables
        self.original_envs = {key: os.environ.get(key) for key in os.environ}

    def tearDown(self):
        # Restore the original environment variables
        for key, value in self.original_envs.items():
            if value is not None:
                os.environ[key] = value
            else:
                os.environ.pop(key, None)

    @mock.patch('os.path.exists')
    @mock.patch('os.path.isdir')
    @mock.patch('builtins.open', new_callable=mock.mock_open, read_data='mocked data')
    @mock.patch('os.path.getsize', return_value=512)
    @mock.patch('os.getuid', return_value=1000)
    @mock.patch('os.getgid', return_value=1000)
    @mock.patch('os.stat')
    @mock.patch('grp.getgrgid', return_value=mock.MagicMock(gr_name='user_group'))
    def test_environment_preparation(self, mock_getgrgid, mock_stat, mock_getgid, mock_getuid, mock_getsize,
                                     mock_open, mock_isdir, mock_exists):
        mock_stat_result = mock.MagicMock()
        mock_stat_result.st_mode = 0o100600
        mock_stat_result.st_uid = 1000
        mock_stat_result.st_gid = 1000
        mock_stat.return_value = mock_stat_result

        from mis.args import GlobalArgs
        mock_exists.return_value = True
        mock_isdir.return_value = True
        envs.MIS_CACHE_PATH = "/mnt/nfs/data/models"
        args = GlobalArgs()
        args.engine_type = "vllm"
        args.model = MIS_MODEL
        args.served_model_name = None
        args.engine_optimization_config = {}
        args.mis_config = "mis_config"
        with mock.patch('mis.utils.utils.Path.exists', return_value=True), \
                mock.patch('mis.utils.utils.Path.is_dir', return_value=True), \
                mock.patch('mis.utils.utils.os.access', return_value=True):
            prepared_args = environment_preparation(args)
        self.assertEqual(prepared_args.served_model_name, MIS_MODEL)

    @mock.patch('os.path.exists')
    @mock.patch('os.path.isdir')
    @mock.patch('builtins.open', new_callable=mock.mock_open, read_data='mocked data')
    @mock.patch('os.path.getsize', return_value=512)
    @mock.patch('os.getuid', return_value=1000)
    @mock.patch('os.stat')
    def test_environment_preparation_without_none(self, mock_stat, mock_getuid, mock_getsize, mock_open, mock_isdir, mock_exists):
        mock_stat_result = mock.MagicMock()
        mock_stat_result.st_mode = 0o100600
        mock_stat_result.st_uid = 1000
        mock_stat.return_value = mock_stat_result

        mock_exists.return_value = True
        mock_isdir.return_value = True
        envs.MIS_CACHE_PATH = "/mnt/nfs/data/models"
        with mock.patch('mis.utils.utils.Path.exists', return_value=True), \
                mock.patch('mis.utils.utils.Path.is_dir', return_value=True), \
                mock.patch('mis.utils.utils.os.access', return_value=True):
            with self.assertRaises(TypeError) as context:
                environment_preparation(None)
                self.assertIn('Environment preparation failed, args must be a GlobalArgs object', str(context.exception))

    @mock.patch('os.path.exists')
    @mock.patch('os.path.isdir')
    @mock.patch('builtins.open', new_callable=mock.mock_open, read_data='mocked data')
    @mock.patch('os.path.getsize', return_value=512)
    @mock.patch('os.getuid', return_value=1000)
    @mock.patch('os.stat')
    def test_environment_preparation_not_instance_of_global_args(self, mock_stat, mock_getuid, mock_getsize, mock_open, mock_isdir,
                                                  mock_exists):
        mock_stat_result = mock.MagicMock()
        mock_stat_result.st_mode = 0o100600
        mock_stat_result.st_uid = 1000
        mock_stat.return_value = mock_stat_result

        mock_exists.return_value = True
        mock_isdir.return_value = True
        envs.MIS_CACHE_PATH = "/mnt/nfs/data/models"
        with mock.patch('mis.utils.utils.Path.exists', return_value=True), \
                mock.patch('mis.utils.utils.Path.is_dir', return_value=True), \
                mock.patch('mis.utils.utils.os.access', return_value=True):
            with self.assertRaises(TypeError) as context:
                environment_preparation("Invalid_args")
                self.assertIn('Environment preparation failed, args must be a GlobalArgs object', str(context.exception))


if __name__ == '__main__':
    unittest.main()
