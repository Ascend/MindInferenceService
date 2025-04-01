# SPDX-License-Identifier: Apache-2.0

from typing import Callable, List, Optional, Set

import torch
import torch_npu
from torch.nn import Parameter
from compressed_tensors.quantization import QuantizationStrategy

from vllm.logger import init_logger
from vllm.model_executor.layers.quantization.compressed_tensors.schemes import (
    CompressedTensorsScheme)
from vllm.model_executor.layers.quantization.kernels.scaled_mm import (
    ScaledMMLinearLayerConfig, choose_scaled_mm_linear_kernel)
from vllm.model_executor.parameter import (BasevLLMParameter,
                                           ChannelQuantScaleParameter,
                                           ModelWeightParameter,
                                           PerTensorScaleParameter)
from vllm.model_executor.layers.quantization.utils.w8a8_utils import convert_to_channelwise

logger = init_logger(__name__)


class CompressedTensorsW8A8Int8(CompressedTensorsScheme):
    _kernel_backends_being_used: Set[str] = set()

    def __init__(self, strategy: str, is_static_input_scheme: bool,
                 input_symmetric: bool):
        self.strategy = strategy
        self.is_static_input_scheme = is_static_input_scheme
        self.input_symmetric = input_symmetric
        self.logical_widths = None

    @classmethod
    def get_min_capability(cls) -> int:
        # turing and up
        return 75

    @staticmethod
    def apply_weights(layer: torch.nn.Module, x: torch.Tensor,
                      bias: Optional[torch.Tensor]) -> torch.Tensor:

        act_dtype = x.dtype
        ori_shape = x.shape
        x = x.view(-1, x.shape[-1])

        x, pertoken_scale = torch_npu.npu_dynamic_quant(x)

        output = torch_npu.npu_quant_matmul(x, layer.weight, layer.weight_scale.view(-1), offset=None,
                                            pertoken_scale=pertoken_scale.view(-1), bias=None, output_dtype=act_dtype)
        output = output if len(ori_shape) == 2 else output.view(ori_shape[0], ori_shape[1], output.shape[-1])
        if bias is not None:
            output += bias
        return output

    def create_weights(self, layer: torch.nn.Module,
                       output_partition_sizes: List[int],
                       input_size_per_partition: int,
                       params_dtype: torch.dtype, weight_loader: Callable,
                       **kwargs):
        self.logical_widths = output_partition_sizes

        # WEIGHT
        weight = ModelWeightParameter(data=torch.empty(
            sum(output_partition_sizes),
            input_size_per_partition,
            dtype=torch.int8),
                                      input_dim=1,
                                      output_dim=0,
                                      weight_loader=weight_loader)

        layer.register_parameter("weight", weight)

        # WEIGHT SCALE
        if self.strategy == QuantizationStrategy.CHANNEL:
            weight_scale = ChannelQuantScaleParameter(
                data=torch.empty((sum(output_partition_sizes), 1),
                                 dtype=torch.float32 if params_dtype == torch.float16 else torch.bfloat16),
                output_dim=0,
                weight_loader=weight_loader)
        else:
            assert self.strategy == QuantizationStrategy.TENSOR
            weight_scale = PerTensorScaleParameter(data=torch.empty(
                len(output_partition_sizes),
                dtype=torch.float32 if params_dtype == torch.float16 else torch.bfloat16),
                                                   weight_loader=weight_loader)
        layer.register_parameter("weight_scale", weight_scale)

        # INPUT SCALE
        if self.is_static_input_scheme:
            input_scale = BasevLLMParameter(data=torch.empty(
                1, dtype=torch.float32 if params_dtype == torch.float16 else torch.bfloat16),
                                            weight_loader=weight_loader)
            layer.register_parameter("input_scale", input_scale)

    def process_weights_after_loading(self, layer: torch.nn.Module) -> None:

        weight = layer.weight
        layer.weight = Parameter(weight.t().contiguous(), requires_grad=False)

        is_fused = len(self.logical_widths) > 1
        if is_fused and self.strategy == QuantizationStrategy.TENSOR:
            ws_channel = convert_to_channelwise(layer.weight_scale, self.logical_widths)
            layer.weight_scale = Parameter(ws_channel, requires_grad=False)
        else:
            layer.weight_scale = Parameter(layer.weight_scale.data, requires_grad=False)

        if self.is_static_input_scheme:
            layer.input_scale = Parameter(layer.input_scale.max(), requires_grad=False)
        else:
            layer.input_scale = None
