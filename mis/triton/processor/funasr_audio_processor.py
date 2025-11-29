#!/usr/bin/env python
# coding=utf-8
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
from typing import Dict, Any, Tuple, Union

import numpy as np
import torch
import torchaudio
from funasr.frontends.wav_frontend import WavFrontend

from ...logger import init_logger, LogType
from ..model_backends.model_factory import register_data_processor
from ..processor import BaseDataProcessor


logger = init_logger(__name__, log_type=LogType.SERVICE)

DEFAULT_SAMPLE_RATE = 16000  # Default sample rate in Hz
DEFAULT_WINDOW_TYPE = "hamming"  # Default window type for audio processing
DEFAULT_FRAME_SHIFT = 10  # Default frame shift in milliseconds
DEFAULT_FRAME_LENGTH = 25  # Default frame length in milliseconds
DEFAULT_N_MELS = 560  # Default number of Mel frequency bins
DEFAULT_USE_DITHER = False  # Default flag for using dithering in audio processing
BATCH_SIZE_INFO = 1  # Batch size shown in the get_output_info


@register_data_processor("funasr_audio")
class FunasrAudioProcessor(BaseDataProcessor):
    """FunASR Audio Processor for SenseVoice model"""

    def __init__(self, processor_config: Dict[str, Any]):
        """
        Initialize the audio processor
        Args: processor_config (dict): Configuration for the audio processor
        """
        super().__init__(processor_config)
        self.fs = processor_config.get("fs", DEFAULT_SAMPLE_RATE)
        self.frontend = WavFrontend(
            cmvn_file=processor_config.get("cmvn_file"),
            fs=processor_config.get("fs", DEFAULT_SAMPLE_RATE),
            window=processor_config.get("window", DEFAULT_WINDOW_TYPE),
            frame_shift=processor_config.get("frame_shift", DEFAULT_FRAME_SHIFT),
            frame_length=processor_config.get("frame_length", DEFAULT_FRAME_LENGTH),
            n_mels=processor_config.get("n_mels", DEFAULT_N_MELS),
            use_dither=processor_config.get("use_dither", DEFAULT_USE_DITHER)
        )

    def process(self, input_data: Union[str, bytes], **kwargs) -> Dict[str, np.ndarray]:
        """
        Process audio data and extract features
        Args: input_data (Union[str, bytes]): Path to the audio file
        Returns: Dict containing speech features and lengths
        """
        if not isinstance(input_data, str):
            logger.error("Funasr audio processing currently only supports the str input parameter type (path).")
            raise ValueError("Funasr audio processing currently only supports the str input parameter type (path).")

        try:
            waveform, sample_rate = torchaudio.load(input_data, normalize=True)
            waveform = torchaudio.functional.resample(waveform, sample_rate, self.fs)
            wave_data = waveform[0].numpy().astype(np.float32).flatten()
            waveform = torch.tensor(wave_data).unsqueeze(0)
            wav_length = torch.tensor([len(wave_data)])

            speech, speech_lengths = self.frontend(waveform, wav_length)
            if len(speech.shape) == 2:
                speech = speech.unsqueeze(0)
            return {
                "speech": speech.numpy().astype(np.float32),
                "speech_lengths": speech_lengths.numpy().astype(np.int32)
            }
        except Exception as e:
            logger.error(f"Feature extraction failed: {str(e)}")
            raise

    def get_output_info(self) -> Dict[str, Tuple]:
        """
        Get output information for the audio processor
        Returns: Dict containing output information
        """
        return {
            "speech": ("speech", np.float32, (BATCH_SIZE_INFO, None, DEFAULT_N_MELS)),
            "speech_lengths": ("speech_lengths", np.int32, (BATCH_SIZE_INFO,))
        }