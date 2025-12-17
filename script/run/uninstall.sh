#!/bin/bash
# -------------------------------------------------------------------------
# This file is part of the Mind Inference Service project.
# Copyright (c) 2025 Huawei Technologies Co.,Ltd.
#
# Mind Inference Service is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#
#          http://license.coscl.org.cn/MulanPSL2
#
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.
# -------------------------------------------------------------------------

# Simple log helper functions
CUR_PATH=$(cd "$(dirname "$0")" || { echo "Failed to enter current path" ; exit ; } ; pwd)

info_record_path="${HOME}/log/Mis"
info_record_file="deployment.log"
info_record_file_back="deployment.log.bak"
log_file=$info_record_path/$info_record_file
LOG_SIZE_THRESHOLD=1024000

readonly USER_N="$(whoami)"
readonly WHO_PATH="$(which who)"
readonly CUT_PATH="$(which cut)"
IP_N="$("${WHO_PATH}" -m | "${CUT_PATH}" -d '(' -f 2 | "${CUT_PATH}" -d ')' -f 1)"
if [ "${IP_N}" = "" ]; then
   IP_N="localhost"
fi

function check_owner()
{
  _local_path=$1

  owner=$(stat -c "%U" "$_local_path")

  if [ "$owner" != "$(whoami)" ]; then
    echo "Error: Current user is not owner at $_local_path"
    exit 1
  fi
}

function rotate_log() {
    check_path "$log_file"
    mv -f "$log_file" "$info_record_path/$info_record_file_back"
    touch "$log_file" 2>/dev/null
    check_path "$info_record_path/$info_record_file_back"
    chmod 440 "$info_record_path/$info_record_file_back"
    check_path "$log_file"
    chmod 640 "$log_file"
}

function check_path() {
    if [ "$1" != "$(realpath "$1")" ]; then
      echo "Log file is not support symlink, exiting!"
      exit 1
    fi
}

function log_check() {
    local log_size
    log_size="$(find "$log_file" -exec ls -l {} \; | awk '{ print $5 }')"
    if [[ "${log_size}" -ge "${LOG_SIZE_THRESHOLD}" ]];then
        rotate_log
    fi
}
function log() {
    # print log to log file
    if [ "$log_file" = "" ]; then
        echo "[$(date +%Y%m%d-%H:%M:%S)] [$USER_N] [$IP_N]: $1" >&2
    fi
    if [ -f "$log_file" ]; then
        log_check
        if ! echo "[$(date +%Y%m%d-%H:%M:%S)] [$USER_N] [$IP_N]: $1" >> "$log_file"; then
          echo "Can not write log, exiting!"
          exit 1
        fi
    else
        echo "Log file does not exist, exiting!"
        exit 1
    fi
}

get_run_path() {
  run_path=$(pwd)
  cd ..
  if [[ "$run_path" =~ /mis ]];then
    suffix='mis'
  else
    log "Error: Directory mis does not exist, exiting!"
    echo "Directory mis does not exist in path[$run_path], exiting!"
    exit 1
  fi
  del_path=$(pwd)/"$suffix"
}

real_delete() {
  cd "${CUR_PATH}/.." || {
    echo "Cannot locate Mis directory: ${CUR_PATH}/.."
    log "Error: Cannot locate Mis directory!"
    exit 255
  }
  get_run_path
  if [[ -f "${CUR_PATH}/version.info" ]];then
    version_info="${CUR_PATH}/version.info"
    if [ ! -d "$info_record_path" ];then
        mkdir -p "$info_record_path"
        chmod 750 "$info_record_path"
    fi

    if [[ ! -f "$log_file" ]];then
        touch "$log_file"
    fi
    find "$log_file" -type f -exec chmod 640 {} \;
    log "$(cat "${version_info}")"

    check_owner "${CUR_PATH}"
    find "${CUR_PATH}" -type d -exec chmod 750 {} \;

    # 删除特定文件和文件夹
    rm -rf "${CUR_PATH}/configs"
    rm -f "${CUR_PATH}/mis.pyz"
    rm -f "${CUR_PATH}/uninstall.sh"
    rm -f "${CUR_PATH}/version.info"

    # 检查并删除 CUR_PATH
    if [ -d "${CUR_PATH}" ] && [ -z "$(ls -A "${CUR_PATH}")" ]; then
      rmdir "${CUR_PATH}"
      if [ $? -eq 0 ]; then
        log "INFO: Successfully removed ${CUR_PATH}"
      else
        log "ERROR: Failed to remove ${CUR_PATH}"
      fi
    else
      log "WARNING: ${CUR_PATH} is not empty or does not exist"
    fi

    if [ -d "${del_path}" ] && [ -z "$(ls -A "${del_path}")" ]; then
      check_owner "${del_path}"
      rmdir "${del_path}"
      current_user=$(whoami)
      install_info_path=/etc/Ascend/ascend_mis_install.info
      if [ "$current_user" != "root" ]; then
          home_dir=$(getent passwd "$current_user" | cut -d: -f6)
          install_info_path=$home_dir/Ascend/ascend_mis_install.info
      fi
      if [ -f "${install_info_path}" ]; then
        rm -rf "${install_info_path}"
      fi
    fi

    log "Uninstall Mis package successfully."
    echo 'Uninstall Mis package successfully.'
  else
    log "Uninstall Mis package failed, version info is missed."
    echo 'Uninstall Mis package failed, version info is missed.'
  fi
}

real_delete