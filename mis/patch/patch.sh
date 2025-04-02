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

sed -i 's/\r$//' /opt/mis/mis/patch/register_patch.py
diff -u /opt/vllm-ascend/vllm-ascend/vllm_ascend/__init__.py /opt/mis/mis/patch/register_patch.py > /opt/mis/mis/patch/register_patch.patch
apply_patch "/opt/vllm-ascend/vllm-ascend/vllm_ascend/__init__.py" "/opt/mis/mis/patch/register_patch.patch"

sed -i 's/\r$//' /opt/mis/mis/patch/attention_forward_patch.py
diff -u  /opt/vllm-ascend/vllm-ascend/vllm_ascend/attention.py /opt/mis/mis/patch/attention_forward_patch.py > /opt/mis/mis/patch/attention_forward_patch.patch
apply_patch "/opt/vllm-ascend/vllm-ascend/vllm_ascend/attention.py" "/opt/mis/mis/patch/attention_forward_patch.patch"

sed -i 's/\r$//' /opt/mis/mis/patch/compressed_tensors_patch.py
diff -u /opt/vllm-ascend/vllm/vllm/model_executor/layers/quantization/compressed_tensors/compressed_tensors.py /opt/mis/mis/patch/compressed_tensors_patch.py > /opt/mis/mis/patch/compressed_tensors_patch.patch
apply_patch "/opt/vllm-ascend/vllm/vllm/model_executor/layers/quantization/compressed_tensors/compressed_tensors.py" "/opt/mis/mis/patch/compressed_tensors_patch.patch"

sed -i 's/\r$//' /opt/mis/mis/patch/quantization_init_patch.py
diff -u /opt/vllm-ascend/vllm/vllm/model_executor/layers/quantization/__init__.py /opt/mis/mis/patch/quantization_init_patch.py > /opt/mis/mis/patch/quantization_init_patch.patch
apply_patch "/opt/vllm-ascend/vllm/vllm/model_executor/layers/quantization/__init__.py" "/opt/mis/mis/patch/quantization_init_patch.patch"

sed -i 's/\r$//' /opt/mis/mis/patch/awq_patch.py
diff -u /opt/vllm-ascend/vllm/vllm/model_executor/layers/quantization/awq.py /opt/mis/mis/patch/awq_patch.py > /opt/mis/mis/patch/awq_patch.patch
apply_patch "/opt/vllm-ascend/vllm/vllm/model_executor/layers/quantization/awq.py" "/opt/mis/mis/patch/awq_patch.patch"

sed -i 's/\r$//' /opt/mis/mis/patch/compressed_tensors_w8a8_int8_patch.py
diff -u /opt/vllm-ascend/vllm/vllm/model_executor/layers/quantization/compressed_tensors/schemes/compressed_tensors_w8a8_int8.py /opt/mis/mis/patch/compressed_tensors_w8a8_int8_patch.py > /opt/mis/mis/patch/compressed_tensors_w8a8_int8_patch.patch
apply_patch "/opt/vllm-ascend/vllm/vllm/model_executor/layers/quantization/compressed_tensors/schemes/compressed_tensors_w8a8_int8.py" "/opt/mis/mis/patch/compressed_tensors_w8a8_int8_patch.patch"
