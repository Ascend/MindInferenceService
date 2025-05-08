#!/bin/bash
# Copyright 2025 Huawei Technologies Co., Ltd.

workdir=$(
  cd $(dirname $0) || exit
  pwd
)

function build_cann_image() {
  cann_image=$2

  if [ -z "$cann_image" ]; then
    cann_image="mis-cann:0.1"
  fi

  echo "build cann image with name [$cann_image]"

  if docker images --format "{{.Repository}}{{.Tag}}" | grep -q "^${cann_image}&"; then
    echo "cann image: ${cann_image} exist"
  else
    echo "building cann image: ${cann_image}"
    cd "$workdir"/dockerfiles/cann || exit
    docker build -t $cann_image . || exit
  fi
}

function build_llm_base_image() {
  cann_image=$2
  if [ -z "$cann_image" ]; then
    cann_image="mis-cann:0.1"
  fi

  llm_base_image=$3
  if [ -z "$llm_base_image" ]; then
    llm_base_image="mis-llm-base:0.1"
  fi

  echo "from [$cann_image] build llm-base image with name [$llm_base_image]"

  if docker images --format "{{.Repository}}{{.Tag}}" | grep -q "^${llm_base_image}&"; then
    echo "llm-base image: ${llm_base_image} exist"
  else
    echo "building llm-base image: ${llm_base_image}"
    cd "$workdir"/dockerfiles/llm/base || exit
    docker build --build-arg BASE_IMAGE=$cann_image -t $llm_base_image . || exit
  fi
}

function build_model_image() {
  llm_base_image=$2
  model_name=$3
  version=$4

  if [ -z "$llm_base_image" ]; then
    llm_base_image="mis-llm-base:0.1"
  fi

  if [ -z "$model_name" ]; then
    model_name="DeepSeek-R1-Distill-Qwen-7B"
  fi

  if [ -z "$version" ]; then
    version="0.1"
  fi

  typeset -l model_name_lower
  model_name_lower=$model_name

  echo "from [$llm_base_image] build model image with name [$model_name_lower:$version]"

  cd $workdir || exit
  docker_build_dir=$workdir/dockerfiles/llm/model/build
  mkdir -p "$docker_build_dir"
  rm -rf "$docker_build_dir"/*

  cp -r "$workdir"/mis*.whl "$docker_build_dir"
  cp -r "$workdir"/configs "$docker_build_dir"
  cp -r "$workdir"/patch "$docker_build_dir"

  cd $workdir/dockerfiles/llm/model || exit

  docker build --build-arg BASE_IMAGE=$llm_base_image --build-arg MODEL="$model_name" -t "$model_name_lower":"$version" . || exit
}

stage=$1
case $stage in
  "cann")
    build_cann_image "$1" "$2"
    ;;
  "llm-base")
    build_llm_base_image "$1" "$2" "$3"
    ;;
  "model")
    build_model_image "$1" "$2" "$3" "$4"
    ;;
  *) echo "Invalid stage, we only support [cann, llm-base, model]"
esac
