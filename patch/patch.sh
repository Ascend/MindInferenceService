#!/bin/bash

set -e

ENABLE_MINICPMV_PATCHES=false
ENABLE_OMNI_PATCHES=false
WORKDIR_SUBDIR=""
ASCEND_PATH="/usr/local/Ascend"
PYTHON_PATH="/usr/local/lib/python3.11/dist-packages"
VLLM_PATH="/opt/vllm-ascend/vllm"
VLLM_ASCEND_PATH="/opt/vllm-ascend"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --enable-minicpmv-patches)
      ENABLE_MINICPMV_PATCHES=true
      shift
      ;;
    --enable-omni-patches)
      ENABLE_OMNI_PATCHES=true
      shift
      ;;
    --workdir-subdir)
      WORKDIR_SUBDIR="$2"
      shift 2
      ;;
    --ascend-path)
      ASCEND_PATH="$2"
      shift 2
      ;;
    --python-path)
      PYTHON_PATH="$2"
      shift 2
      ;;
    --vllm-path)
      VLLM_PATH="$2"
      shift 2
      ;;
    --vllm-ascend-path)
      VLLM_ASCEND_PATH="$2"
      shift 2
      ;;
    *)
      echo "Unknown parameters: $1"
      exit 1
      ;;
  esac
done

workdir=$(
  cd $(dirname $0)/$WORKDIR_SUBDIR || exit
  pwd
)

apply_patch() {
  local file="$1"
  local patch_file="$2"

  if [[ ! -f "$file" ]]; then
    echo "Error: File does not exist: $file" >&2
    return
  fi

  if [[ ! -w "$file" ]]; then
    echo "Error: Insufficient permissions to write to the file: $file" >&2
    return
  fi

  if ! [[ -f "$patch_file" ]]; then
    echo "Error: Patch file does not exist: $patch_file" >&2
    return
  fi

  if patch -R --dry-run -f "$file" < "$patch_file" > /dev/null 2>&1; then
    echo "Patch $patch_file is already applied to $file. Skipping."
  else
    echo "Applying patch $patch_file to $file..."
    if patch "$file" < "$patch_file" > /dev/null 2>&1; then
      echo "Patch applied successfully."
    else
      echo "Error: Failed to apply patch $patch_file to $file" >&2
      return
    fi
  fi
}

sed -i 's/\r$//' $workdir/__init__.patch
apply_patch "${VLLM_PATH}/vllm/model_executor/layers/quantization/__init__.py" "$workdir/__init__.patch"

sed -i 's/\r$//' $workdir/vllm_ascend_attention.patch
apply_patch "${VLLM_ASCEND_PATH}/vllm_ascend/attention/attention.py" "$workdir/vllm_ascend_attention.patch"

sed -i 's/\r$//' $workdir/awq.patch
apply_patch "${VLLM_PATH}/vllm/model_executor/layers/quantization/awq.py" "$workdir/awq.patch"

sed -i 's/\r$//' $workdir/compressed_tensors.patch
apply_patch "${VLLM_PATH}/vllm/model_executor/layers/quantization/compressed_tensors/compressed_tensors.py" "$workdir/compressed_tensors.patch"

sed -i 's/\r$//' $workdir/compressed_tensors_w8a8_int8.patch
apply_patch "${VLLM_PATH}/vllm/model_executor/layers/quantization/compressed_tensors/schemes/compressed_tensors_w8a8_int8.py" "$workdir/compressed_tensors_w8a8_int8.patch"

sed -i 's/\r$//' $workdir/config.patch
apply_patch "${VLLM_PATH}/vllm/config.py" "$workdir/config.patch"

sed -i 's/\r$//' $workdir/loader.patch
apply_patch "${VLLM_PATH}/vllm/model_executor/model_loader/loader.py" "$workdir/loader.patch"

sed -i 's/\r$//' $workdir/platform.patch
apply_patch "${VLLM_ASCEND_PATH}/vllm_ascend/platform.py" "$workdir/platform.patch"

sed -i 's/\r$//' $workdir/weight_utils.patch
apply_patch "${VLLM_PATH}/vllm/model_executor/model_loader/weight_utils.py" "$workdir/weight_utils.patch"

sed -i 's/\r$//' $workdir/kv_cache.patch
apply_patch "${VLLM_PATH}/vllm/model_executor/layers/quantization/kv_cache.py" "$workdir/kv_cache.patch"

sed -i 's/\r$//' $workdir/mindie_turbo_attention.patch
apply_patch "${PYTHON_PATH}/mindie_turbo/adaptor/vllm/attention.py" "$workdir/mindie_turbo_attention.patch"

if [ "$ENABLE_MINICPMV_PATCHES" = true ]; then
  sed -i 's/\r$//' $workdir/atb_base_config.patch
  apply_patch "${ASCEND_PATH}/atb/atb_llm/models/base/config.py" "$workdir/atb_base_config.patch"

  sed -i 's/\r$//' $workdir/flash_causal_lm.patch
  apply_patch "${ASCEND_PATH}/atb/atb_llm/models/base/flash_causal_lm.py" "$workdir/flash_causal_lm.patch"
fi

if [ "$ENABLE_OMNI_PATCHES" = true ]; then
  sed -i 's/\r$//' $workdir/model_runner.patch
  apply_patch "${VLLM_ASCEND_PATH}/vllm_ascend/worker/model_runner.py" "$workdir/model_runner.patch"
fi