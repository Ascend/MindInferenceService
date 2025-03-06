# Simple Chatbot使用说明

## 目录

- [概述](#概述)
- [环境依赖](#环境依赖)
- [使用方法](#使用方法)
  - [1. 下载昇腾推理微服务镜像](#1-下载昇腾推理微服务镜像)
  - [2. 启动服务](#2-启动服务)
  - [3. 停止服务](#3-停止服务)
  - [4. 查询服务状态](#4-查询服务状态)
- [注意事项](#注意事项)
- [微服务版本信息](#微服务版本信息)

## 概述

基于昇腾推理微服务与 OpenWebUI 框架构建了一个功能丰富的对话机器人应用。该应用集成了用户管理、对话管理、RAG等核心功能，旨在为用户提供高效、智能的对话交互体验。通过昇腾推理微服务，系统能够利用大语言模型（LLM）的强大逻辑推导与自然语言处理能力，实现高质量的对话生成与响应。

本项目主要包含以下两个核心服务：

1. **推理微服务**：负责大语言模型的加载与推理，处理用户输入的对话请求，并生成相应的回复。
2. **WebUI 微服务**：基于 OpenWebUI 框架，提供用户交互界面，支持对话记录查看、模型切换、用户管理等功能。

## 环境依赖

在运行 `app.sh` 之前，请确保系统已安装并正确配置以下组件：

- **Docker**：用于运行微服务容器。
- **[Ascend Docker Runtime](https://www.hiascend.com/document/detail/zh/mindx-dl/600/clusterscheduling/clusterschedulingig/clusterschedulingig/dlug_installation_017.html)**：支持容器挂载 Ascend 硬件。
- **[Ascend NPU 驱动与固件](https://support.huawei.com/enterprise/zh/doc/EDOC1100438838/b1977c97)**：支持 Ascend 硬件。
- **Linux 操作系统**。

## 使用方法

**使用前注意**：本脚本使用 `~/mis/models` 作为本地缓存路径。若该路径不存在，脚本会自动创建。

### 1. 下载昇腾推理微服务镜像

 - **手动下载：** 登录昇腾镜像仓库，找到 [deepseek-r1-distill-qwen-7b
](https://www.hiascend.com/developer/ascendhub/detail/5c613bed40a24bb88bbf352ed9924e88) 推理微服务，选择 **镜像版本** 页签，下载 **0.1-arm64** 版本的镜像。

 - **脚本自动下载（不推荐）：** `app.sh` 脚本支持自动下载推理微服务镜像，但需要用户通过 `docker login` 命令手动登录昇腾镜像仓库。为确保下载过程稳定可靠，建议用户手动拉取推理微服务镜像后，再执行 `app.sh` 启动服务。

### 2. 启动服务

执行以下命令启动推理微服务和 WebUI 微服务：

```bash
bash app.sh start
```

### 3. 停止服务

执行以下命令停止并删除微服务容器：

```bash
bash app.sh stop
```

### 4. 查询服务状态

执行以下命令检查推理微服务和 WebUI 微服务的运行状态：

```bash
bash app.sh status
```

## 注意事项

- 若启动失败，请检查 Docker 与 Ascend Docker Runtime 是否正确安装并运行。
- 若容器已存在，请先执行 `bash app.sh stop` 后再尝试重新启动。
- 若端口已被占用，请修改 `MIS_PORT` 或 `OPENWEBUI_PORT` 变量后重新启动。

## 微服务版本信息

- **推理微服务镜像**：`swr.cn-south-1.myhuaweicloud.com/ascendhub/deepseek-r1-distill-qwen-7b:0.1-arm64`
- **WebUI 微服务镜像**：`ghcr.io/open-webui/open-webui:main`
