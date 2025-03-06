#!/bin/bash

# 模型本地缓存路径
readonly LOCAL_CACHE_PATH=~/mis/models
# NPU挂载
readonly ASCEND_VISIBLE_DEVICES=0

# 推理微服务信息
readonly MIS_IMAGE_NAME=swr.cn-south-1.myhuaweicloud.com/ascendhub/deepseek-r1-distill-qwen-7b
readonly MIS_IMAGE_TAG=0.1-arm64
readonly MIS_CONTAINER_NAME=deepseek-r1-distill-qwen-7b
readonly MIS_PORT=9000

# WebUI信息
readonly OPENWEBUI_IMAGE_NAME=ghcr.io/open-webui/open-webui
readonly OPENWEBUI_IMAGE_TAG=main
readonly OPENWEBUI_CONTAINER_NAME=open-webui
readonly OPENWEBUI_PORT=8080

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# 检查Docker环境
check_docker_env() {
    echo -n "Checking Docker environment... "
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}FAILED${NC}" && echo "[ERROR] Docker is not installed. Please install Docker first."
        exit 1
    fi
    if ! systemctl is-active --quiet docker; then
        echo -e "${RED}FAILED${NC}" && echo "[ERROR] Docker service is not running."
        exit 1
    fi
    
    local runtime=$(docker info --format '{{.DefaultRuntime}}' 2>/dev/null)
    if [ "$runtime" != "ascend" ]; then
        echo -e "${RED}FAILED${NC}" && echo "[ERROR] Default Docker runtime is '$runtime'. Please install Ascend Docker Runtime."
        exit 1
    fi
    echo -e "${GREEN}SUCCESS${NC}"
}

# 检查缓存目录
check_local_cache_path() {
    echo -n "Checking local cache directory... "
    if [ ! -d $LOCAL_CACHE_PATH ]; then
        mkdir -p "$LOCAL_CACHE_PATH" || { echo -e "${RED}FAILED${NC}" && echo "[ERROR] Failed to create directory: $LOCAL_CACHE_PATH"; exit 1; }
    fi
    echo -e "${GREEN}SUCCESS${NC}"
}

# 检查端口占用情况
check_port_availability() {
    local port=$1
    if lsof -i :$port > /dev/null; then
        echo -e "${RED}FAILED${NC}" && echo "[ERROR] Port $port is already in use."
        exit 1
    fi
}

# 启动微服务
start() {
    check_docker_env
    check_local_cache_path
    
    echo -n "Checking Docker images... "
    local mis_pull=false
    local openwebui_pull=false
    if ! docker images -q "$MIS_IMAGE_NAME:$MIS_IMAGE_TAG" > /dev/null 2>&1; then mis_pull=true; fi
    if ! docker images -q "$OPENWEBUI_IMAGE_NAME:$OPENWEBUI_IMAGE_TAG" > /dev/null 2>&1; then openwebui_pull=true; fi
    echo -e "${GREEN}SUCCESS${NC}"
    
    if $mis_pull || $openwebui_pull; then
        echo "Pulling missing images..."
        $mis_pull && docker pull "$MIS_IMAGE_NAME:$MIS_IMAGE_TAG" &
        $openwebui_pull && docker pull "$OPENWEBUI_IMAGE_NAME:$OPENWEBUI_IMAGE_TAG" &
        wait
    fi
    
    echo -n "Checking existing containers... "
    for container in "$MIS_CONTAINER_NAME" "$OPENWEBUI_CONTAINER_NAME"; do
        if docker ps -a --format '{{.Names}}' | grep -qw "$container"; then
            echo -e "${RED}FAILED${NC}" && echo "[ERROR] Container '$container' already exists. Remove it before starting."
            exit 1
        fi
    done
    echo -e "${GREEN}SUCCESS${NC}"
    
    echo -n "Checking port availability... "
    check_port_availability "$MIS_PORT"
    check_port_availability "$OPENWEBUI_PORT"
    echo -e "${GREEN}SUCCESS${NC}"
    
    echo "Starting containers..."
    docker run -itd --name="$MIS_CONTAINER_NAME" -e ASCEND_VISIBLE_DEVICES=$ASCEND_VISIBLE_DEVICES \
        -v "$LOCAL_CACHE_PATH:/opt/mis/.cache" -p "$MIS_PORT:8000" \
        "$MIS_IMAGE_NAME:$MIS_IMAGE_TAG"
    
    mis_docker_ip=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$MIS_CONTAINER_NAME" 2>/dev/null)
    
    docker run -itd --name="$OPENWEBUI_CONTAINER_NAME" -p "$OPENWEBUI_PORT:8080" \
        -e OPENAI_API_BASE_URL="http://$mis_docker_ip:8000/openai/v1" -e OPENAI_API_KEY=test \
        "$OPENWEBUI_IMAGE_NAME:$OPENWEBUI_IMAGE_TAG"
    
    echo "=== INFO ==="
    echo "MIS service running on http://localhost:$MIS_PORT"
    echo "OpenWebUI running on http://localhost:$OPENWEBUI_PORT"
}

# 停止微服务
stop() {
    echo "Stopping and removing containers..."
    docker rm -f "$MIS_CONTAINER_NAME" "$OPENWEBUI_CONTAINER_NAME"
    echo "All containers removed."
}

# 检查微服务状态
status() {
    local mis_status=$(docker inspect --format '{{.State.Running}}' "$MIS_CONTAINER_NAME" 2>/dev/null || echo "false")
    local openwebui_status=$(docker inspect --format '{{.State.Running}}' "$OPENWEBUI_CONTAINER_NAME" 2>/dev/null || echo "false")
    local mis_http_status=$(curl -o /dev/null -s -w "%{http_code}" "http://localhost:$MIS_PORT/openai/v1/models" || echo "000")
    local openwebui_http_status=$(curl -o /dev/null -s -w "%{http_code}" "http://localhost:$OPENWEBUI_PORT" || echo "000")
    
    echo "Inference Microservice[$MIS_CONTAINER_NAME]:"
    echo "  - Container: $( [ "$mis_status" = "true" ] && echo -e ${GREEN}"Running"${NC} || echo -e ${YELLOW}"Not Found"${NC})"
    echo "  - Service: $( [ "$mis_http_status" -eq 200 ] && echo -e ${GREEN}"Available"${NC} || echo -e ${YELLOW}"Unavailable"${NC})"
    
    echo "WebUI[$OPENWEBUI_CONTAINER_NAME]:"
    echo "  - Container: $( [ "$openwebui_status" = "true" ] && echo -e ${GREEN}"Running"${NC} || echo -e ${YELLOW}"Not Found"${NC})"
    echo "  - Service: $( [ "$openwebui_http_status" -eq 200 ] && echo -e ${GREEN}"Available"${NC} || echo -e ${YELLOW}"Unavailable"${NC})"
}

case "$1" in
    start) start ;;
    stop) stop ;;
    status) status ;;
    *)
        echo -e "${RED}Invalid argument: $1${NC}"
        echo "Usage: $0 {start|stop|status}"
        exit 1
        ;;
esac
