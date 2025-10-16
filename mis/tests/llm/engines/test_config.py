# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import unittest
from unittest.mock import patch, mock_open, MagicMock, Mock

import yaml

from mis.args import GlobalArgs
from mis.llm.engines.config_parser import ConfigParser

READ_DATA = """vllm:
  dtype: bfloat16
  block_size: 32
engine_type: vllm
model: test_model
"""


class TestAbsEngineConfigValidator(unittest.TestCase):
    def setUp(self):
        # Initialize test data
        self.config = {
            "dtype": "bfloat16",
            "tensor_parallel_size": 2,
            "pipeline_parallel_size": 1,
            "distributed_executor_backend": "mp",
            "max_num_seqs": 100,
            "max_model_len": 8192,
            "max_num_batched_tokens": 8192,
            "max_seq_len_to_capture": 8192,
            "gpu_memory_utilization": 0.8,
            "block_size": 32,
            "swap_space": 512,
            "cpu_offload_gb": 0,
            "scheduling_policy": "fcfs",
            "num_scheduler_steps": 10,
            "enable_chunked_prefill": True,
            "enable_prefix_caching": False,
            "multi_step_stream_outputs": False,
            "enforce_eager": False,
        }

    def test_filter_and_validate_config(self):
        from mis.llm.engines.config_validator import AbsEngineConfigValidator, CHECKER_VLLM
        validator = AbsEngineConfigValidator(self.config, CHECKER_VLLM)
        valid_config = validator.filter_and_validate_config()
        # Verify whether the returned configuration meets expectations.
        self.assertEqual(valid_config.get("dtype"), "bfloat16")
        self.assertEqual(valid_config.get("tensor_parallel_size"), 2)
        self.assertEqual(valid_config.get("pipeline_parallel_size"), 1)
        self.assertEqual(valid_config.get("max_num_seqs"), 100)

    def test_unsupported_keys(self):
        from mis.llm.engines.config_validator import AbsEngineConfigValidator, CHECKER_VLLM
        unsupported_config = self.config.copy()
        unsupported_config["unsupported_key"] = "value"
        with self.assertRaises(ValueError) as context:
            validator = AbsEngineConfigValidator(unsupported_config, CHECKER_VLLM)

    def test_out_of_range_values(self):
        from mis.llm.engines.config_validator import AbsEngineConfigValidator, CHECKER_VLLM
        invalid_config = self.config.copy()
        invalid_config["tensor_parallel_size"] = 16  # Exceeds the valid value range

        with self.assertRaises(ValueError) as context:
            validator = AbsEngineConfigValidator(invalid_config, CHECKER_VLLM)
            valid_config = validator.filter_and_validate_config()

    def test_invalid_string_values(self):
        from mis.llm.engines.config_validator import AbsEngineConfigValidator, CHECKER_VLLM
        invalid_config = self.config.copy()
        invalid_config["dtype"] = "invalid_dtype"
        with self.assertRaises(ValueError) as context:
            validator = AbsEngineConfigValidator(invalid_config, CHECKER_VLLM)
            valid_config = validator.filter_and_validate_config()


class TestConfigParser(unittest.TestCase):

    @patch('os.path.exists', return_value=True)
    @patch('os.path.getsize', return_value=512)
    @patch('os.getuid', return_value=1000)
    @patch('os.path.isfile', return_value=True)
    @patch('os.path.isdir', return_value=False)
    @patch('os.stat')
    def test_engine_config_loading_valid_config(self, mock_stat, mock_isdir, mock_isfile, mock_getuid,
                                                mock_getsize, mock_exists):
        mock_stat.return_value = MagicMock(st_uid=1000)
        args = GlobalArgs()
        args.engine_type = 'vllm'
        args.mis_config = 'test_config'
        args.model = 'test_model'

        parser = ConfigParser(args)
        updated_args = parser.engine_config_loading()

        self.assertEqual(updated_args.engine_type, 'vllm')
        self.assertEqual(updated_args.model, 'test_model')

    @patch('os.path.exists', return_value=False)
    def test_engine_config_loading_invalid_config_path(self, mock_exists):
        args = GlobalArgs()
        args.engine_type = 'vllm'
        args.mis_config = 'non_existent_config'
        args.model = 'test_model'

        parser = ConfigParser(args)
        updated_args = parser.engine_config_loading()

        self.assertEqual(updated_args.engine_type, 'vllm')
        self.assertEqual(updated_args.model, 'test_model')

    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data='engine_type: invalid_engine\nmodel: test_model\n')
    @patch('os.path.getsize', return_value=512)
    @patch('os.getuid', return_value=1000)
    @patch('os.path.isfile', return_value=True)
    @patch('os.path.isdir', return_value=False)
    @patch('os.stat')
    def test_engine_config_loading_invalid_engine_type(self, mock_stat, mock_isdir, mock_isfile, mock_getuid,
                                                       mock_getsize, mock_file, mock_exists):
        mock_stat.return_value = MagicMock(st_uid=1000)
        args = GlobalArgs()
        args.engine_type = 'invalid_engine'
        args.mis_config = 'test_config'
        args.model = 'test_model'

        parser = ConfigParser(args)
        updated_args = parser.engine_config_loading()

        self.assertEqual(updated_args.engine_type, 'invalid_engine')
        self.assertEqual(updated_args.model, 'test_model')

    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data='model: test_model\n')
    @patch('os.path.getsize', return_value=512)
    @patch('os.getuid', return_value=1000)
    @patch('os.path.isfile', return_value=True)
    @patch('os.path.isdir', return_value=False)
    @patch('os.stat')
    def test_engine_config_loading_missing_engine_type(self, mock_stat, mock_isdir, mock_isfile, mock_getuid,
                                                       mock_getsize, mock_file, mock_exists):
        mock_stat.return_value = MagicMock(st_uid=1000)
        args = GlobalArgs()
        args.engine_type = None
        args.mis_config = 'test_config'
        args.model = 'test_model'

        parser = ConfigParser(args)
        updated_args = parser.engine_config_loading()

        self.assertIsNone(updated_args.engine_type)
        self.assertEqual(updated_args.model, 'test_model')

    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data='engine_type: vllm\n')
    @patch('os.path.getsize', return_value=512)
    @patch('os.getuid', return_value=1000)
    @patch('os.path.isfile', return_value=True)
    @patch('os.path.isdir', return_value=False)
    @patch('os.stat')
    def test_engine_config_loading_missing_model(self, mock_stat, mock_isdir, mock_isfile, mock_getuid,
                                                 mock_getsize, mock_file, mock_exists):
        mock_stat.return_value = MagicMock(st_uid=1000)
        args = GlobalArgs()
        args.engine_type = 'vllm'
        args.mis_config = 'test_config'
        args.model = ''

        parser = ConfigParser(args)
        updated_args = parser.engine_config_loading()

        self.assertEqual(updated_args.engine_type, 'vllm')
        self.assertEqual(updated_args.model, '')

    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data='engine_type: vllm\nmodel: invalid_model\n')
    @patch('os.path.getsize', return_value=512)
    @patch('os.getuid', return_value=1000)
    @patch('os.path.isfile', return_value=True)
    @patch('os.path.isdir', return_value=False)
    @patch('os.stat')
    def test_engine_config_loading_invalid_model(self, mock_stat, mock_isdir, mock_isfile, mock_getuid,
                                                 mock_getsize, mock_file, mock_exists):
        mock_stat.return_value = MagicMock(st_uid=1000)
        args = GlobalArgs()
        args.engine_type = 'vllm'
        args.mis_config = 'test_config'
        args.model = 'invalid_model'

        parser = ConfigParser(args)
        updated_args = parser.engine_config_loading()

        self.assertEqual(updated_args.engine_type, 'vllm')
        self.assertEqual(updated_args.model, 'invalid_model')

    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data='engine_type: vllm\nmodel: test_model\n')
    @patch('os.path.getsize', return_value=512)
    @patch('os.getuid', return_value=1000)
    @patch('os.path.isfile', return_value=True)
    @patch('os.path.isdir', return_value=False)
    @patch('os.stat')
    def test_engine_config_loading_valid_model(self, mock_stat, mock_isdir, mock_isfile, mock_getuid,
                                               mock_getsize, mock_file, mock_exists):
        mock_stat.return_value = MagicMock(st_uid=1000)
        args = GlobalArgs()
        args.engine_type = 'vllm'
        args.mis_config = 'test_config'
        args.model = 'test_model'
        parser = ConfigParser(args)
        updated_args = parser.engine_config_loading()

        self.assertEqual(updated_args.engine_type, 'vllm')
        self.assertEqual(updated_args.model, 'test_model')

    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data='key: value: invalid')
    @patch('os.path.getsize', return_value=512)
    @patch('os.getuid', return_value=1000)
    @patch('os.path.isfile', return_value=True)
    @patch('os.path.isdir', return_value=False)
    @patch('os.stat')
    def test_config_yaml_file_loading_yaml_error(self, mock_stat, mock_isdir, mock_isfile, mock_getuid,
                                                 mock_getsize, mock_file, mock_exists):
        mock_stat.return_value = Mock(st_uid=1000)
        config_file_path = 'invalid_config.yaml'
        args = GlobalArgs()
        args.engine_type = None
        args.model = 'test_model'
        args.mis_config = 'atlas800ia2-1x32gb-bf16-vllm-latency'
        parser = ConfigParser(args)
        with self.assertRaises(yaml.YAMLError):
            parser._config_yaml_file_loading(config_file_path)

    @patch('os.path.exists', return_value=True)
    @patch('os.path.islink', return_value=True)
    @patch('os.getuid', return_value=1000)
    @patch('os.path.isfile', return_value=True)
    @patch('os.stat')
    @patch('os.path.isfile', return_value=False)
    def test_config_yaml_file_loading_symbolic_link(self, mock_isfile, mock_stat, mock_isfile2, mock_getuid,
                                                    mock_islink, mock_exists):
        mock_stat.return_value = Mock(st_uid=1000)
        config_file_path = 'atlas800ia2-1x32gb-bf16-vllm-latency'
        args = GlobalArgs()
        args.engine_type = "vllm"
        args.model = 'test_model'
        args.mis_config = 'atlas800ia2-1x32gb-bf16-vllm-latency'
        parser = ConfigParser(args)

        with self.assertRaises(Exception) as context:
            parser._config_yaml_file_loading(config_file_path)
        self.assertEqual(str(context.exception), "The configuration file is a symbolic link.")


if __name__ == '__main__':
    unittest.main()
