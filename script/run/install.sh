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

# 自定义变量
install_path="${USER_PWD}"

current_user=$(whoami)
install_info_path=/etc/Ascend/ascend_mis_install.info
install_info_dir=/etc/Ascend

if [ "$current_user" != "root" ]; then
    home_dir=$(getent passwd "$current_user" | cut -d: -f6)
    install_info_path=$home_dir/Ascend/ascend_mis_install.info
    install_info_dir=$home_dir/Ascend
fi

PACKAGE_LOG_NAME=MIS
LOG_SIZE_THRESHOLD=$((10*1024*1024))
declare -A param_dict=()               # 参数个数统计
version_number=""
arch_name="aarch64"

info_record_path="${HOME}/log/mis"
info_record_file="deployment.log"

#标识符
install_flag=n
print_version_flag=n
install_path_flag=n
uninstall_flag=n
quiet_flag=n

ms_deployment_log_rotate() {
  if [ -L "${info_record_path}" ]; then
    echo "The directory path of deployment.log cannot be a symlink." >&2
    exit 1
  fi
  if [[ ! -d "${info_record_path}" ]];then
    install -d -m 750 "${info_record_path}"
  fi
  record_file_path="${info_record_path}"/"${info_record_file}"
  if [ -L "${record_file_path}" ]; then
    echo "The deployment.log cannot be a symlink." >&2
    exit 1
  fi
  if [[ ! -f "${record_file_path}" ]];then
    install -m 600 /dev/null "${record_file_path}"
  fi
  record_file_path_bk="${info_record_path}"/"${info_record_file}".bk
  if [ -L "${record_file_path_bk}" ]; then
    echo "The deployment.log.bk cannot be a symlink." >&2
    exit 1
  fi
  log_size=$(find "${record_file_path}" -exec ls -l {} \; | awk '{ print $5 }')
  if [[ "${log_size}" -ge "${LOG_SIZE_THRESHOLD}" ]];then
    mv -f "${record_file_path}" "${record_file_path_bk}"
    install -m 600 /dev/null "${record_file_path}"
    chmod 400 "${record_file_path_bk}"
  fi
  chmod 600 "${record_file_path}"
}

ms_log()
{
  ms_deployment_log_rotate
  record_file_path="${info_record_path}/${info_record_file}"
  chmod 640 "${record_file_path}"
  user_ip=$(who am i | awk '{print $NF}' | sed 's/[()]//g')
  [[ -z "${user_ip}" ]] && user_ip="localhost"
  user_name=$(whoami)
  host_name=$(hostname)
  timestamp=$(date "+%Y-%m-%d %H:%M:%S")

  log_line="[${timestamp}][${user_ip}][${user_name}][${host_name}]: $1"
  echo "${log_line}" >> "${record_file_path}"
  chmod 440 "${record_file_path}"
  echo "$1"
}

###  公用函数
function print_usage() {
  ms_log "Please input this command for more help: --help"
}

### 脚本入参的相关处理函数
function check_script_args() {
  ######################  check params confilct ###################
  if [ $# -lt 3 ]; then
    print_usage
  fi
  # 重复参数检查
  for key in "${!param_dict[@]}";do
    if [ "${param_dict[${key}]}" -gt 1 ]; then
      ms_log "ERROR: parameter error! ${key} is repeat."
      exit 1
    fi
  done

  if [ "${print_version_flag}" = y ]; then
    if [ "${install_flag}" = y ] || [ "${uninstall_flag}" = y ]; then
      ms_log "ERROR: --version param cannot config with install and uninstall param."
      exit 1
    fi
  fi

  if [ "${install_path_flag}" = y ]; then
    # path只支持绝对路径
    if [[ ! "${install_path}" =~ ^/.* ]]; then
      ms_log "ERROR: parameter error ${install_path}, must absolute path."
      exit 1
    fi
  fi

  if [ "${uninstall_flag}" = y ]; then
    if [ "${install_flag}" = y ] || [ "${print_version_flag}" = y ]; then
      ms_log "ERROR: Unsupported parameters, operation failed."
      exit 1
    fi
  fi
  if [ "${install_flag}" = y ]; then
    if [ "${uninstall_flag}" = y ] || [ "${print_version_flag}" = y ]; then
      ms_log "ERROR: Unsupported parameters, operation failed."
      exit 1
    fi
  fi
  if [ "${install_path_flag}" = y ]; then
    if [ "${install_flag}" = n ] && [ "${uninstall_flag}" = n ]; then
      ms_log "ERROR: Unsupported separate 'install-path' used independently."
      exit 1
    fi
    if [ -f "${install_info_path}" ]; then
      ms_log "ERROR: Because the ${install_info_path} exists, '--install-path' can't be config. Please uninstall MIS or do not use '--install-path'."
      exit 1
    fi
  fi
}

check_target_dir()
{
  if [[ "${install_path}" =~ [^a-zA-Z0-9_./-] ]]; then
    ms_log "MIS dir contains invalid char, please check path."
    exit 1
  fi
}

function check_sha256sum()
{
  if [ ! -e "/usr/bin/sha256sum" ] && [ ! -e "/usr/bin/shasum" ]; then
    ms_log "ERROR: Sha256 check Failed."
    exit 1
  fi
}

# 解析脚本自身的参数
function parse_script_args() {
  local all_para_len="$*"
  if [[ ${#all_para_len} -gt 1024 ]]; then
    ms_log "The total length of the parameter is too long"
    exit 1
  fi
  local num=0
  while true; do
    if [[ "$1" == "" ]]; then
      break
    fi
    if [[ "${1: 0: 2}" == "--" ]]; then
      num=$((num + 1))
    fi
    if [[ ${num} -gt 2 ]]; then
      break
    fi
    shift 1
  done
  while true; do
    case "$1" in
    --check)
      check_sha256sum
      exit 0
      ;;
    --version)
      print_version_flag=y
      shift
      ;;
    --install)
      check_platform
      install_flag=y
      ((param_dict["install"]++)) || true
      shift
      ;;
    --install-path=*)
      check_platform
      # 去除指定安装目录后所有的 "/"
      install_path=$(echo "$1" | cut -d"=" -f2 | sed "s/\/*$//g")
      check_target_dir
      if [[ "${install_path}" != /* ]]; then
        install_path="${USER_PWD}/${install_path}"
      fi
      existing_dir="${install_path}"
      while [[ ! -d "${existing_dir}" && "${existing_dir}" != "/" ]]; do
        existing_dir=$(dirname "${existing_dir}")
      done
      abs_existing_dir=$(readlink -f "${existing_dir}")
      nonexistent_suffix="${install_path#"$existing_dir"}"
      install_path="${abs_existing_dir}${nonexistent_suffix}"
      install_path_flag=y
      ((param_dict["install-path"]++)) || true
      shift
      ;;
    --uninstall)
      check_platform
      uninstall_flag=y
      ((param_dict["uninstall"]++)) || true
      shift
      ;;
    --quiet | -q)
      quiet_flag=y
      ((param_dict["quiet"]++)) || true
      shift
      ;;
    -*)
      ms_log "WARNING: Unsupported parameters: $1"
      print_usage
      shift
      ;;
    *)
      if [ "x$1" != "x" ]; then
        ms_log "WARNING: Unsupported parameters: $1"
        print_usage
      fi
      break
      ;;
    esac
  done
}

ms_save_uninstall_info()
{
  path="$1"
  user_ip=$(who am i | awk '{print $NF}' | sed 's/(//g' | sed 's/)//g')
  if [[ -z "${user_ip}" ]]; then
    user_ip=localhost
  fi
  user_name=$(whoami)
  host_name=$(hostname)
  append_text="[$(date "+%Y-%m-%d %H:%M:%S")][${user_ip}][${user_name}][${host_name}]:"
  echo "$append_text${append_text} Uninstall MIS successfully." >> "${path}"
}

ms_save_install_info()
{
  path="$1"
  user_ip=$(who am i | awk '{print $NF}' | sed 's/(//g' | sed 's/)//g')
  if [[ -z "${user_ip}" ]]; then
    user_ip=localhost
  fi
  user_name=$(whoami)
  host_name=$(hostname)
  append_text="[$(date "+%Y-%m-%d %H:%M:%S")][${user_ip}][${user_name}][${host_name}]:"
  echo "$append_text${new_version_info:+ $new_version_info} Install MIS successfully." >> "${path}"
}

ms_record_operator_info()
{
  ms_deployment_log_rotate

  find "${record_file_path}" -type f -exec chmod 750 {} \;

  if test "${install_flag}" = y; then
    ms_save_install_info "${record_file_path}"
    ms_log "INFO: Successfully installed MIS."
  fi

  if test "${uninstall_flag}" = y; then
    ms_save_uninstall_info "${record_file_path}"
    ms_log "INFO: Successfully uninstall MIS."
  fi

  find "${record_file_path}" -type f -exec chmod 440 {} \;
}

function handle_eula() {
  local action=$1
  if [ "${quiet_flag}" = y ]; then
    ms_log "INFO: using quiet option implies acceptance of the EULA, start to ${action}"
    return
  fi
  if echo "${LANG}" | grep -q "zh_CN.UTF-8"; then
    ms_log "INFO: How the EULA is displayed depends on the value of environment variable LANG: 'zh_CN.UTF-8' for Chinese"
    eula_file=./eula_cn.conf
  else
    ms_log "INFO: How the EULA is displayed depends on the value of environment variable LANG: '${LANG}' for English"
    eula_file=./eula_en.conf
  fi
  cat "${eula_file}" 1>&2
  read -n1 -re -p "Do you accept the EULA to ${action} MIS ?[Y/N]" answer
  case "${answer}" in
    Y|y)
      ms_log "INFO: accept EULA, start to ${action}"
      ;;
    *)
      ms_log "ERROR: reject EULA, quit to ${action}"
      exit 1
      ;;
  esac
}

function check_platform()
{
  plat="$(uname -m)"
  result="$(echo "${arch_name}" | grep "${plat}")"
  if test "${result}" = ""; then
    ms_print_warning "Warning: Platform(${plat}) mismatch for ${arch_name}, please check it."
    ms_log "Warning: Platform(${plat}) mismatch for ${arch_name}, please check it."
  fi
}

function check_owner()
{
  _local_path=$1

  owner=$(stat -c "%U" "$_local_path")

  if [ "$owner" != "$(whoami)" ]; then
    ms_log "Error: Current user is not owner at $_local_path"
    exit 1
  fi
}

function untar_file() {
  if [ "${print_version_flag}" = y ]; then
    SELF_DIR="$(cd "$(dirname "$0")"; pwd)"
    files=$(ls "$SELF_DIR"/Ascend-mis*.tar.gz 2>/dev/null)
    if [[ -z "$files" ]]; then
        ms_log "ERROR: Can't find Ascend-mis*.tar.gz in $SELF_DIR"
        exit 1
    fi
    file_count=$(echo "$files" | wc -l)
    if [[ "$file_count" -gt 1 ]]; then
        ms_log "ERROR: There are more than one file match Ascend-mis*.tar.gz in $SELF_DIR"
        exit 1
    fi
    tar -xzf "${files}" -O "./version.info"
  elif [ "${install_flag}" = y ]; then
    ms_log "INFO: install start"

    if [ -L "${install_info_dir}" ]; then
      ms_log "Error: ${install_info_dir} cannot be a symlink"
      exit 1
    fi
    if [ -L "${install_info_path}" ]; then
      ms_log "Error: ${install_info_path} cannot be a symlink"
      exit 1
    fi
    if [ ! -d "${install_info_dir}" ]; then
      install -d -m 750 "${install_info_dir}"
    fi
    last_install_path="Not Found"

    if [ -f "${install_info_path}" ]; then
      while IFS="=" read -r key value; do
        if [ "$key" == "Install_Path" ]; then
          last_install_path=$value
          break
        fi
      done < "$install_info_path"
      if [ "$last_install_path" == "Not Found" ]; then
        ms_log "ERROR: Can't parse 'Install_Path' from $install_info_path, please remove it and reinstall."
        exit 1
      else
        install_path=$last_install_path
      fi
    fi
    ms_log "INFO: The installation path is ${install_path}."

    SELF_DIR="$(cd "$(dirname "$0")"; pwd)"
    files=$(ls "$SELF_DIR"/Ascend-mis*.tar.gz 2>/dev/null)
    if [[ -z "$files" ]]; then
        ms_log "ERROR: Can't find Ascend-mis*.tar.gz in $SELF_DIR"
        exit 1
    fi
    file_count=$(echo "$files" | wc -l)
    if [[ "$file_count" -gt 1 ]]; then
        ms_log "ERROR: There are more than one file match Ascend-mis*.tar.gz in $SELF_DIR"
        exit 1
    fi
    mis_name="mis"
    version_number=$(tar -xzf "${files}" -O "./version.info" | cut -d ':' -f2 | tr -d '[:space:]')
    new_version_info=$version_number
    if [ -L "${install_path}" ]; then
      ms_log "Error: ${install_path} cannot be a symlink"
      exit 1
    fi
    if [ ! -d "${install_path}" ]; then
      if ! install -d -m 750 "${install_path}"; then
        ms_log "Error: Create ${install_path} failed"
        exit 1
      fi
    fi
    check_owner "${install_path}"

    if test "${install_flag}" = y; then
      handle_eula "install"
      if \
        [[ -d "${install_path}/${mis_name}/${new_version_info}/configs" ]] && \
        [[ -f "${install_path}/${mis_name}/${new_version_info}/mis.pyz" ]] && \
        [[ -f "${install_path}/${mis_name}/${new_version_info}/version.info" ]]; then

        ms_log "WARNING: There is already installation at $install_path, please check it."
        exit 1
      fi
    fi
    if ! install -d -m 750 "${install_path}/${mis_name}/${new_version_info}"; then
      ms_log "ERROR: Create path at ${install_path}/${mis_name}/${new_version_info} failed"
      exit 1
    fi
    check_owner "${install_path}/${mis_name}/${new_version_info}"

    if ! tar -xzf "${files}" -C "${install_path}/${mis_name}/${new_version_info}" --no-same-owner; then
      ms_log "ERROR: Failed to extract files to ${install_path}/${mis_name}/${new_version_info}"
      # If the tar command fails to execute, it may leave behind residual files,
      # so should delete any files that might have been extracted
      rm -rf "${install_path}/${mis_name}/${new_version_info}/configs"
      rm -f "${install_path}/${mis_name}/${new_version_info}/mis.pyz"
      rm -f "${install_path}/${mis_name}/${new_version_info}/uninstall.sh"
      rm -f "${install_path}/${mis_name}/${new_version_info}/version.info"
      rmdir --ignore-fail-on-non-empty "${install_path}/${mis_name}/${new_version_info}"
      rmdir --ignore-fail-on-non-empty "${install_path}/${mis_name}"
      exit 1
    fi
    cp "$SELF_DIR"/uninstall.sh "${install_path}/${mis_name}/${new_version_info}"
    chmod 750 "${install_path}/${mis_name}"
    chmod 550 "${install_path}/${mis_name}/${new_version_info}"
    chmod 500 "${install_path}/${mis_name}/${new_version_info}/uninstall.sh"

    if [ ! -f "${install_info_path}" ]; then
      install -m 640 /dev/null "${install_info_path}"
      echo "Install_Path=${install_path}" > "$install_info_path"
      ms_log "INFO: Save install info in ${install_info_path}"
    fi

    cd - > /dev/null || exit
    ms_record_operator_info
    echo -e "\n"
    echo -e "==========="
    echo -e "= Summary ="
    echo -e "===========\n"
    local fixed_begin_len=6
    if [ ${#PACKAGE_LOG_NAME} -gt $fixed_begin_len ]; then
        fixed_begin_len=${#PACKAGE_LOG_NAME}
    fi
    (( fixed_begin_len += 3 ))
    printf "%-${fixed_begin_len}s" "MIS:"
    echo -e "Install MIS successfully, installed in ${install_path}/${mis_name}/${new_version_info}"
    echo -e "To start the MIS server, execute the command 'python ${install_path}/${mis_name}/${new_version_info}/mis.pyz'"
  elif [ "${uninstall_flag}" = y ]; then
    ms_log "INFO: Uninstall start"
    mis_name="mis"
    last_install_path="Not Found"
    if [ -f "${install_info_path}" ]; then
      while IFS="=" read -r key value; do
        if [ "$key" == "Install_Path" ]; then
          last_install_path=$value
          break
        fi
      done < "$install_info_path"
      if [ "$last_install_path" == "Not Found" ]; then
        ms_log "ERROR: Can't parse 'Install_Path' from $install_info_path, please remove it and manually uninstall MIS."
        exit 1
      fi
    else
      ms_log "ERROR: Can't find ${install_info_path} file, uninstall MIS failed."
      exit 1
    fi
    if [ ! -d "${last_install_path}/${mis_name}" ]; then
      ms_log "ERROR: Can't find ${last_install_path}/${mis_name}, uninstall MIS failed."
      exit 1
    fi

    check_owner "${last_install_path}"

    find "${last_install_path}/${mis_name}" -type d -exec chmod 750 {} \;
    if ! rm -rf "${last_install_path:?}/${mis_name}"; then
      ms_log "Error: Failed to remove MIS at ${last_install_path}/${mis_name}"
      exit 1
    else
      ms_log "Info: Remove MIS success!"
    fi
    if ! rm -rf "${install_info_path}"; then
      ms_log "Error: Failed to remove MIS install info file at ${install_info_path}"
      exit 1
    else
      ms_log "Info: Remove MIS install info file success!"
    fi
    ms_record_operator_info
  else
    ms_log "Info: Do not proceed with installation or uninstall and exit."
  fi
}

# 程序开始
function main() {
  parse_script_args "$@"
  check_script_args "$@"
  untar_file
}

main "$@"