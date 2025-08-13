# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.

import argparse
import os
import sys
import unittest
from unittest.mock import patch, call

from mis.args import ARGS
from mis.llm.engines.config import ConfigParser
from mis.mis_config_export import _parse_arguments, _create_export_path, _export_yaml_files
from mis import mis_config_export

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


class TestMain(unittest.TestCase):

    @patch('argparse.ArgumentParser.parse_args')
    def test_parse_arguments(self, mock_parse_args):
        # Mock the command line arguments
        mock_parse_args.return_value = argparse.Namespace(disable_print_config_ranges=False)
        args = _parse_arguments()
        self.assertFalse(args.disable_print_config_ranges)

    @patch('os.path.exists')
    @patch('os.makedirs')
    def test_create_export_path(self, mock_makedirs, mock_exists):
        # Mock the existence of the export path
        mock_exists.return_value = True
        export_path = _create_export_path('model_type')
        self.assertEqual(export_path, os.path.join('/opt/mis/.cache/configs', 'model_type'))
        mock_makedirs.assert_not_called()

        # Test when the export path does not exist
        mock_exists.return_value = False
        with self.assertRaises(OSError):
            _create_export_path('model_type')
        mock_makedirs.assert_not_called()

    @patch('shutil.copy')
    @patch('os.path.exists')
    @patch('os.listdir')
    def test_export_yaml_files(self, mock_listdir, mock_exists, mock_copy):
        # Mock the list of files in the model folder
        mock_listdir.return_value = ['file1.yaml', 'file2.yaml', 'file3.yaml']

        # Mock the existence of the destination files
        mock_exists.side_effect = [False, True, False]

        # Call the function
        model_folder_path = '/path/to/model_folder'
        export_path = '/path/to/export_path'
        _export_yaml_files(model_folder_path, export_path)

        # Assert the expected behavior
        expected_calls = [
            call(os.path.join(model_folder_path, 'file1.yaml'), os.path.join(export_path, 'file1.yaml')),
            call(os.path.join(model_folder_path, 'file3.yaml'), os.path.join(export_path, 'file3.yaml'))
        ]
        mock_copy.assert_has_calls(expected_calls, any_order=True)
        self.assertEqual(mock_copy.call_count, 2)
        self.assertEqual(mock_exists.call_count, 3)

    @patch('mis.mis_config_export._parse_arguments')
    @patch('mis.mis_config_export.ConfigParser')
    @patch('mis.mis_config_export._create_export_path')
    @patch('mis.mis_config_export._export_yaml_files')
    def test_main(self, mock_export_yaml_files, mock_create_export_path, mock_configparser, mock_parse_arguments):
        # Mock the arguments and ConfigParser
        mock_parse_arguments.return_value = argparse.Namespace(disable_print_config_ranges=False)
        mock_configparser.return_value = ConfigParser(ARGS)
        mock_configparser.return_value.model_type = 'model_type'
        mock_configparser.return_value.model_folder_path = '/path/to/model_folder'
        mock_create_export_path.return_value = '/path/to/export_path'

        mis_config_export.main()

        # Check that the functions are called with the correct arguments
        mock_configparser.assert_called_once_with(ARGS)
        mock_create_export_path.assert_called_once_with('model_type')
        mock_export_yaml_files.assert_called_once_with('/path/to/model_folder', '/path/to/export_path')


if __name__ == "__main__":
    unittest.main()
