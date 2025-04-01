#
#
from typing import Any, Dict, List, Optional

import torch

from vllm import _custom_ops as ops
from vllm.model_executor.layers.linear import (LinearBase, LinearMethodBase,
                                               UnquantizedLinearMethod)
from vllm.model_executor.layers.quantization import register_quantization_config
from vllm.model_executor.layers.quantization.base_config import (
    QuantizationConfig)
from vllm.model_executor.parameter import (GroupQuantScaleParameter,
                                           PackedvLLMParameter)


STORAGE_BITS_NPU = 8
STORAGE_BITS_GPU = 32
REVERSE_SWQ_PACK_ORDER = [0,4,1,5,2,6,3,7]
QUANTIZATION_TYPE = "ascend"
INT4_LENGTH = 4
INT8_LENGTH = 8
INT32_LENGTH = 32


@register_quantization_config(QUANTIZATION_TYPE)
class AWQConfig(QuantizationConfig):
    """Config class for AWQ.

    Reference: https://arxiv.org/abs/2306.00978
    """

    def __init__(
        self,
        weight_bits: int,
        group_size: int,
        zero_point: bool,
        modules_to_not_convert: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.weight_bits = weight_bits
        self.group_size = group_size
        self.zero_point = zero_point
        self.modules_to_not_convert = modules_to_not_convert or []

        if self.weight_bits != 4:
            raise ValueError(
                "Currently, only 4-bit weight quantization is supported for "
                f"AWQ, but got {self.weight_bits} bits.")
        if self.group_size <= 0:
            raise ValueError("group_size should be greater than 0")
        
        self.pack_factor =  STORAGE_BITS_NPU // self.weight_bits
        
    def __repr__(self) -> str:
        return (f"AscendAWQConfig(weight_bits={self.weight_bits}, "
                f"group_size={self.group_size}, "
                f"zero_point={self.zero_point}, "
                f"modules_to_not_convert={self.modules_to_not_convert})")

    @staticmethod
    def get_name() -> str:
        return QUANTIZATION_TYPE

    @staticmethod
    def get_supported_act_dtypes() -> List[torch.dtype]:
        return [torch.float16, torch.bfloat16]

    @classmethod
    def get_min_capability(cls) -> int:
        # The AWQ kernel only supports Turing or newer GPUs.
        return 75

    @staticmethod
    def get_config_filenames() -> List[str]:
        return [
            "quant_config.json",  # E.g., casperhansen/vicuna-7b-v1.5-awq
            # E.g., abhinavkulkarni/mosaicml-mpt-7b-instruct-w4-g128-awq
            "quantize_config.json",
        ]

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "AWQConfig":
        weight_bits = cls.get_from_keys(config, ["w_bit", "bits"])
        group_size = cls.get_from_keys(config, ["q_group_size", "group_size"])
        zero_point = cls.get_from_keys(config, ["zero_point"])
        return cls(weight_bits, group_size, zero_point)

    @classmethod
    def override_quantization_method(cls, hf_quant_cfg, user_quant) -> Optional[str]:
        if torch_npu.is_available():
            return QUANTIZATION_TYPE
        return None

    def get_quant_method(self, layer: torch.nn.Module,
                         prefix: str) -> Optional["LinearMethodBase"]:
        if isinstance(layer, LinearBase):
            if is_layer_skipped_awq(prefix, self.modules_to_not_convert):
                return UnquantizedLinearMethod()
            return AWQLinearMethod(self)
        return None


def is_layer_skipped_awq(prefix: str, modules_to_not_convert: List[str]):
    return any(module_name in prefix for module_name in modules_to_not_convert)


class AWQLinearMethod(LinearMethodBase):
    """Linear method for AWQ.

    Args:
        quant_config: The AWQ quantization config.
    """

    def __init__(self, quant_config: AWQConfig):
        self.quant_config = quant_config
        self.group_size = self.quant_config.group_size if self.quant.group_size != -1 else 0
        self.shifts_unpack = torch.arange(0, STORAGE_BITS_GPU, self.quant_config.weight_bits)[None, None, :]
        self.gpu_pack_factor = STORAGE_BITS_GPU // self.quant_config.weight_bits
        self.npu_pack_factor = STORAGE_BITS_NPU // self.quant_config.weight_bits
        self.real_weight_loader = None

    def create_weights(self, layer: torch.nn.Module,
                       input_size_per_partition: int,
                       output_partition_sizes: List[int], input_size: int,
                       output_size: int, params_dtype: torch.dtype,
                       **extra_weight_attrs):
        if input_size_per_partition % self.quant_config.group_size != 0:
            raise ValueError(
                "The input size is not aligned with the quantized "
                "weight shape. This can be caused by too large "
                "tensor parallel size.")

        output_size_per_partition = sum(output_partition_sizes)
        if output_size_per_partition % self.quant_config.pack_factor != 0:
            raise ValueError(
                "The output size is not aligned with the quantized "
                "weight shape. This can be caused by too large "
                "tensor parallel size.")

        self.weight_loader = extra_weight_attrs.get("weight_loader")

        if self.quant_config.group_size != -1:
            scale_abd_zero_size = input_size_per_partition // self.quant_config.group_size
        else:
            scale_abd_zero_size = 1

        qweight = PackedvLLMParameter(
            data=torch.empty(
                input_size_per_partition,
                output_size_per_partition // self.quant_config.pack_factor,
                dtype=torch.int8,
            ),
            input_dim=0,
            output_dim=1,
            packed_dim=1,
            packed_factor=self.quant_config.pack_factor,
            weight_loader=self._qweight_weight_loader)

        qzeros = PackedvLLMParameter(
            data=torch.empty(
                scale_abd_zero_size,
                output_size_per_partition,
                dtype=params_dtype,
            ),
            input_dim=0,
            output_dim=1,
            packed_dim=0,
            packed_factor=self.quant_config.pack_factor,
            weight_loader=self._qzeros_weight_loader)

        scales = GroupQuantScaleParameter(data=torch.empty(
            scale_abd_zero_size,
            output_size_per_partition,
            dtype=params_dtype,
        ),
            input_dim=0,
            output_dim=1,
            weight_loader=self.weight_loader)

        layer.register_parameter("qweight", qweight)
        layer.register_parameter("qzeros", qzeros)
        layer.register_parameter("scales", scales)

    def _unpack_int8(self, qmatrix: torch.Tensor):
        shifts_unpack = torch.arange(0, INT8_LENGTH, self.quant_config.weight_bits)[None, None, :]
        if shifts_unpack.device != qmatrix.device:
            shifts_unpack = shifts_unpack.to(qmatrix.device)

        imatrix = torch.bitwise_right_shift(qmatrix[:, :, None],
                                            shifts_unpack).view(qmatrix.shape[0], -1)
        imatrix = imatrix.to(torch.int32) & 0x0F
        return imatrix

    def _unpack(self, qmatrix: torch.Tensor):
        if self.shifts_unpack.device != qmatrix.device:
            self.shifts_unpack = self.shifts_unpack.to(qmatrix.device)

        imatrix = torch.bitwise_right_shift(qmatrix[:, :, None],
                                            self.shifts_unpack).view(qmatrix.shape[0], -1)

        imatrix = imatrix.to(torch.int32) & 0x0F
        return imatrix

    def _repack_to_npu_weight(self, qweight):
        qweight = torch.bitwise_xor(qweight, 0x88888888)

        iweights = self._unpack(qweight)

        iweights = iweights.view(-1, self.gpu_pack_factor)[:, REVERSE_SWQ_PACK_ORDER].view(iweights.shape)
        iweights = iweights.view(-1, iweights.shape[1] // self.npu_pack_factor, self.npu_pack_factor)

        if self.shifts_pack.device != qweight.device:
            self.shifts_unpack = self.shifts_pack.to(iweights.device)
        qweight = torch.bitwise_left_shift(iweights, self.shifts_pack).sum(dim=-1)
        qweight = qweight.to(torch.int8)
        return qweight

    def _repack_to_npu_zeros(self, qzeros):
        izeros = self._unpack(qzeros)
        izeros = izeros.view(-1, self.gpu_pack_factor)[:, REVERSE_SWQ_PACK_ORDER].view(izeros.shape)
        return -(izeros.to(torch.float16) - 8)

    def _qweight_weight_loader(self, *args, **kwargs) -> None:
        args_list = list(args)
        weight_loader = self.real_weight_loader
        if args_list[1].dtype == torch.int32:
            args_list[1] = self._repack_to_npu_weight(args_list[1])
        weight_loader(*args_list, **kwargs)

    def _qzeros_weight_loader(self, *args, **kwargs) -> None:
        args_list = list(args)
        weight_loader = self.real_weight_loader
        if args_list[1].dtype == torch.int32:
            args_list[1] = self._repack_to_npu_zeros(args_list[1])
        weight_loader(*args_list, **kwargs)
