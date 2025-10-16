# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import os
import ssl
from typing import Optional

import mis.constants as constants
from mis.args import GlobalArgs
from mis.llm.engines.config_parser import ConfigParser
from mis.logger import init_logger, LogType
from mis.utils.utils import ContainerIPDetector, get_model_path

logger = init_logger(__name__, log_type=LogType.SERVICE)


def _source_components_envs() -> None:
    for components_env in constants.SOURCE_COMPONENTS_ENVS:
        if components_env not in os.environ:
            os.environ[components_env] = "1"
            logger.debug(f"Set environment variable {components_env} to 1")


def _is_private_key_encrypted(key_file_path: str) -> bool:
    """Check if a PEM formatted private key file is encrypted

    Args:
        key_file_path (str): Path to the private key file

    Returns:
        bool: True if encrypted, False if not encrypted
    """
    if not os.path.isfile(key_file_path):
        logger.warning(f"SSL key file not found")
        return False

    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.serialization import load_pem_private_key

        with open(key_file_path, 'rb') as key_file:
            key_data = key_file.read()

        try:
            load_pem_private_key(key_data, password=None)
            return False  # Successfully loaded, indicating it is not encrypted
        except TypeError:
            return True  # Requires a password, indicating it is encrypted

    except Exception as e:
        logger.warning(f"Failed to parse SSL key file: {e}")
        return False


def _check_ssl_config(ssl_keyfile: Optional[str], ssl_certfile: Optional[str],
                      ssl_ca_certs: Optional[str], enable_https: bool) -> None:
    """Check SSL configuration to ensure that the necessary files are provided and
    that the private key is properly encrypted.
    Args:
        ssl_keyfile (Optional[str]): Path to the SSL private key file.
        ssl_certfile (Optional[str]): Path to the SSL certificate file.
        ssl_ca_certs (Optional[str]): Path to the CA certificate file used to verify client certificates.
        enable_https (bool): Whether to enable HTTPS. If True, a valid SSL certificate and private key must be provided.
    Returns:
        None
    """
    if not ssl_keyfile or not ssl_certfile:
        if enable_https:
            logger.error(f"SSL key and certificate files are required by "
                         f"MIS_SSL_KEYFILE and MIS_SSL_CERTFILE when HTTPS is enabled.")
            raise RuntimeError("SSL key and certificate files are required by "
                               f"MIS_SSL_KEYFILE and MIS_SSL_CERTFILE when HTTPS is enabled.")
        else:
            logger.warning("SSL not configured. To ensure security, "
                           "you must provide a certificate and encrypted private key.")
        return

    if _is_private_key_encrypted(ssl_keyfile):
        logger.info(f"SSL private key is encrypted!. You may need to provide a password for startup")
    else:
        if enable_https:
            logger.error(f"SSL private key is not encrypted!.")
            raise RuntimeError("SSL private key is not encrypted!.")
        else:
            logger.warning(f"SSL private key is not encrypted. "
                           f"The private key will be mounted in plain text, "
                           f"which poses a serious security risk. It is suggest to encrypt the private key.")

    if ssl_ca_certs:
        if not os.path.exists(ssl_ca_certs):
            logger.error(f"CA certificate file does not exist")
            raise RuntimeError(f"CA certificate file does not exist")
        try:
            with open(ssl_ca_certs, 'rb') as f:
                cert_data = f.read()
            cert_data_str = cert_data.decode('utf-8')
            ssl.PEM_cert_to_DER_cert(cert_data_str)
            logger.info(f"CA certificate file is valid")
        except Exception as e:
            logger.error(f"Invalid CA certificate file, error: {e}")
            raise RuntimeError(f"Invalid CA certificate file, error: {e}") from e
    else:
        logger.warning(f"CA certificate file not provided")


def environment_preparation(args: GlobalArgs) -> GlobalArgs:
    """Do some preparations for mis
        include:
            - model-preferred-config-resolve
            - set environment variables if needed
    """
    logger.info("Starting environment preparation")

    _source_components_envs()
    logger.info("Loaded component environment variables")

    ip_update = ContainerIPDetector.get_ip(args.host)
    if ip_update is None:
        logger.error(f"Unable to automatically detect Host IP. "
                     f"Please manually set the Host IP via the environment variable MIS_HOST.")
        raise RuntimeError("Host IP could not be detected automatically.")
    else:
        args.host = ip_update

    # preferred config
    configparser = ConfigParser(args)
    args = configparser.engine_config_loading()
    logger.debug("Loaded engine configuration")

    if args.served_model_name is None:
        args.served_model_name = args.model
        logger.info(f"Set served_model_name to {args.model}")

    args.model = get_model_path(args.model)
    logger.debug(f"Resolved model path")

    _check_ssl_config(args.ssl_keyfile, args.ssl_certfile, args.ssl_ca_certs, args.enable_https)
    logger.debug("Checked SSL configuration")

    logger.info("Environment preparation completed")
    return args
