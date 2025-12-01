#!/bin/bash
# Copyright © Huawei Technologies Co., Ltd. 2025-2025. All rights reserved.

set -e

MIS_HTTP_HOST="127.0.0.1"
MIS_GRPC_HOST="127.0.0.1"
MIS_METRIC_HOST="127.0.0.1"

DEFAULT_MIS_HTTP_PORT=8000
DEFAULT_MODEL_NAME="unknown"
DEFAULT_LOG_INFO_FLAG=true
DEFAULT_LOG_VERBOSE="1"

MIS_HTTP_PORT="${MIS_PORT:-$DEFAULT_MIS_HTTP_PORT}"
MIS_GRPC_PORT="$((MIS_HTTP_PORT + 1))"
MIS_METRIC_PORT="$((MIS_HTTP_PORT + 2))"
MIS_MODEL_NAME="${MIS_MODEL:-$DEFAULT_MODEL_NAME}"
LOG_INFO_FLAG="${LOG_INFO_FLAG:-$DEFAULT_LOG_INFO_FLAG}"
LOG_VERBOSE="${LOG_VERBOSE:-$DEFAULT_LOG_VERBOSE}"

# Verify port number
function validate_port() {
  local port=$1
  if ! [[ "$port" =~ ^[0-9]+$ ]] || [ "$port" -lt 1 ] || [ "$port" -gt 65535 ]; then
    echo "Error: Invalid port number. Port must be a number between 1 and 65535."
    exit 1
  fi
}

validate_port "$MIS_HTTP_PORT"
validate_port "$MIS_GRPC_PORT"
validate_port "$MIS_METRIC_PORT"

# Verify LOG_INFO_FLAG
if [[ "$LOG_INFO_FLAG" != "true" && "$LOG_INFO_FLAG" != "false" ]]; then
  echo "Error: Invalid LOG_INFO_FLAG. Valid values are: true, false"
  exit 1
fi

# Verify LOG_VERBOSE
if [[ "$LOG_VERBOSE" != "0" && "$LOG_VERBOSE" != "1" ]]; then
  echo "Error: Invalid LOG_VERBOSE. Valid values are: 0, 1"
  exit 1
fi

# Set Env
if ! source /usr/local/Ascend/ascend-toolkit/set_env.sh; then
  echo "Warning: Failed to source /usr/local/Ascend/ascend-toolkit/set_env.sh"
fi

if ! source /usr/local/Ascend/nnal/atb/set_env.sh; then
  echo "Warning: Failed to source /usr/local/Ascend/nnal/atb/set_env.sh"
fi

if ! export LD_LIBRARY_PATH=/usr/local/Ascend/driver/lib64/common:/usr/local/Ascend/driver/lib64/driver:${LD_LIBRARY_PATH}; then
  echo "Warning: Failed to set LD_LIBRARY_PATH"
fi

CURRENT_DIR=$(basename "$(pwd)")
PARENT_DIR=$(basename "$(dirname "$(pwd)")")

if [ "$CURRENT_DIR" != "mis" ]; then
  echo "Error: Current directory must be 'mis'."
  exit 1
fi

# Check triton is a subdirectory of mis
if [ ! -d "triton" ]; then
  echo "Error: 'triton' subdirectory does not exist in the current directory."
  exit 1
fi

cd triton

# Launch Triton server
tritonserver --model-repository=model_repository \
             --model-control-mode=explicit \
             --http-address="${MIS_HTTP_HOST}" \
             --grpc-address="${MIS_GRPC_HOST}" \
             --metrics-address="${MIS_METRIC_HOST}" \
             --http-port="${MIS_HTTP_PORT}" \
             --grpc-port="${MIS_GRPC_PORT}" \
             --metrics-port="${MIS_METRIC_PORT}" \
             --load-model="${MIS_MODEL_NAME}" \
             --log-info="${LOG_INFO_FLAG}" \
             --log-verbose="${LOG_VERBOSE}"
