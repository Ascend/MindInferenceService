# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import os
import unittest
from unittest import mock

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

import mis.envs as envs
from mis.hub.envpreparation import environment_preparation, _is_private_key_encrypted

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
    @mock.patch('os.stat')
    def test_environment_preparation(self, mock_stat, mock_getuid, mock_getsize, mock_open, mock_isdir, mock_exists):
        mock_stat_result = mock.MagicMock()
        mock_stat_result.st_mode = 0o100644
        mock_stat_result.st_uid = 1000
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
        args.enable_https = False
        args.mis_config = "mis_config"
        with mock.patch('mis.utils.utils.Path.exists', return_value=True), \
                mock.patch('mis.utils.utils.Path.is_dir', return_value=True), \
                mock.patch('mis.utils.utils.os.access', return_value=True):
            prepared_args = environment_preparation(args)
        self.assertEqual(prepared_args.served_model_name, MIS_MODEL)


class TestIsPrivateKeyEncrypted(unittest.TestCase):
    def setUp(self):
        # Create temporary unencrypted and encrypted PEM files
        self.unencrypted_key_path = 'test_unencrypted.pem'
        self.encrypted_key_path = 'test_encrypted.pem'

        # Generate an RSA private key
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        # Save the unencrypted private key
        with open(self.unencrypted_key_path, 'wb') as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))

        # Save the encrypted private key
        password = b"password"
        with open(self.encrypted_key_path, 'wb') as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.BestAvailableEncryption(password)
            ))

    def tearDown(self):
        os.remove(self.unencrypted_key_path)
        os.remove(self.encrypted_key_path)

    def test_unencrypted_key(self):
        # Testing an Unencrypted Private Key File
        self.assertFalse(_is_private_key_encrypted(self.unencrypted_key_path))

    def test_encrypted_key(self):
        # Test the encrypted private key file
        self.assertTrue(_is_private_key_encrypted(self.encrypted_key_path))

    def test_nonexistent_file(self):
        # Test non-existent files.
        self.assertFalse(_is_private_key_encrypted('nonexistent_file.pem'))

    @mock.patch('os.path.isfile', return_value=True)
    def test_file_read_error(self, mock_isfile):
        # Test file read error
        self.assertFalse(_is_private_key_encrypted('invalid_file.pem'))


if __name__ == '__main__':
    unittest.main()
