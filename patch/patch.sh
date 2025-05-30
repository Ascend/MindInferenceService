#!/bin/bash

set -e

workdir=$(
  cd $(dirname $0) || exit
  pwd
)

apply_patch() {
  local file="$1"
  local patch_file="$2"

  if patch -R --dry-run -f "$file" < "$patch_file" > /dev/null 2>&1; then
    echo "Patch $patch_file is already applied to $file. Skip"
  else
    echo "Applying patch $patch_file to $file..."
    patch "$file" < "$patch_file"
  fi
}

sed -i 's/\r$//' $workdir/__init__.patch
apply_patch "/opt/vllm-ascend/vllm/vllm/model_executor/layers/quantization/__init__.py" "$workdir/__init__.patch"

sed -i 's/\r$//' $workdir/vllm_ascend_attention.patch
apply_patch "/usr/local/lib/python3.10/dist-packages/vllm_ascend/attention/attention.py" "$workdir/vllm_ascend_attention.patch"

sed -i 's/\r$//' $workdir/awq.patch
apply_patch "/opt/vllm-ascend/vllm/vllm/model_executor/layers/quantization/awq.py" "$workdir/awq.patch"

sed -i 's/\r$//' $workdir/compressed_tensors.patch
apply_patch "/opt/vllm-ascend/vllm/vllm/model_executor/layers/quantization/compressed_tensors/compressed_tensors.py" "$workdir/compressed_tensors.patch"

sed -i 's/\r$//' $workdir/compressed_tensors_w8a8_int8.patch
apply_patch "/opt/vllm-ascend/vllm/vllm/model_executor/layers/quantization/compressed_tensors/schemes/compressed_tensors_w8a8_int8.py" "$workdir/compressed_tensors_w8a8_int8.patch"

sed -i 's/\r$//' $workdir/config.patch
apply_patch "/opt/vllm-ascend/vllm/vllm/config.py" "$workdir/config.patch"

sed -i 's/\r$//' $workdir/loader.patch
apply_patch "/opt/vllm-ascend/vllm/vllm/model_executor/model_loader/loader.py" "$workdir/loader.patch"

sed -i 's/\r$//' $workdir/platform.patch
apply_patch "/usr/local/lib/python3.10/dist-packages/vllm_ascend/platform.py" "$workdir/platform.patch"

sed -i 's/\r$//' $workdir/weight_utils.patch
apply_patch "/opt/vllm-ascend/vllm/vllm/model_executor/model_loader/weight_utils.py" "$workdir/weight_utils.patch"

sed -i 's/\r$//' $workdir/kv_cache.patch
apply_patch "/opt/vllm-ascend/vllm/vllm/model_executor/layers/quantization/kv_cache.py" "$workdir/kv_cache.patch"

sed -i 's/\r$//' $workdir/mindie_turbo_attention.patch
apply_patch "/usr/local/lib/python3.10/dist-packages/mindie_turbo/adaptor/vllm/attention.py" "$workdir/mindie_turbo_attention.patch"


