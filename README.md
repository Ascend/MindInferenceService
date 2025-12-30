# Mind Inference Service
- [最新消息](#最新消息)
- [简介](#简介)
- [目录结构](#目录结构)
- [版本说明](#版本说明)
- [环境部署](#环境部署)
  - [编译](#编译)
- [快速入门](#快速入门)
  - [简介](#简介-1)
  - [环境准备](#环境准备)
  - [启动MIS服务](#启动mis服务)
  - [发起请求](#发起请求)
- [特性介绍](#特性介绍)
- [安全声明](#安全声明)
- [License](#license)
- [建议与交流](#建议与交流)

# 最新消息

- [2025.12.30]: 🚀 Mind Inference Service支持Qwen3-8B模型

# 简介

    昇腾推理微服务MIS（Mind Inference Service）提供了模型推理服务，无需复杂的依赖安装，即可快速完成部署。针对昇腾硬件进行深度的性能优化，省去繁琐的调优过程。提供行业标准接口，便于集成到企业业务系统中，助力业务高效运行。

# 目录结构

``` 
├─ configs
|  └─ llm
|     └─ qwen3-8b
├─ mis
|  ├─ hub
|  ├─ llm
|  |  ├─ engines
|  |  ├─ entrypoints
|  |  └─ openai
|  ├─ tests
|  |  └─ llm
|  |     ├─ engines
|  |     └─ entrypoints
|  └─ utils
└─ script
   └─ run
```

# 版本说明

| 软件          | 版本        | 下载链接                                                                                                                    |
|-------------|-----------|-------------------------------------------------------------------------------------------------------------------------|
| CANN        | 8.3.RC1   | https://www.hiascend.com/developer/download/community/result?module=tf+cann&tf=8.3.RC1&cann=8.3.RC1                     |
| vllm        | 0.11.0    | https://github.com/vllm-project/vllm/tree/v0.11.0                                                                       |
| vllm-ascend | 0.11.0rc2 | https://github.com/vllm-project/vllm-ascend/tree/v0.11.0rc2                                                             |
| Driver      | 25.3.RC1  | https://www.hiascend.com/hardware/firmware-drivers/community?product=4&model=26&cann=8.3.RC1&driver=Ascend+HDK+25.3.RC1 |
| Firmware    | 25.3.RC1  | https://www.hiascend.com/hardware/firmware-drivers/community?product=4&model=26&cann=8.3.RC1&driver=Ascend+HDK+25.3.RC1 |

# 环境部署

介绍Mind Inference Service的编译及安装方式。

## 编译

编译环境依赖：
- Python 3.11.4

编译流程：

1.  拉取mis整体源码，例如放在/home目录下。
2.  执行以下命令，进入/home/MIS目录，选择构建脚本执行：
    **cd /home/MIS**

        python compile.py
3.  执行完成后，在/home/MIS/dist目录下生成可直接执行的mis.pyz文件。
4.  将MIS/configs目录复制到mis.pyz文件所在目录，即可通过mis.pyz文件运行mis服务：
    **cp -r /home/MIS/configs /home/MIS/dist**

        cd /home/MIS/dist
        python3 mis.pyz

- 请注意，mis服务启动时会对configs目录进行校验，请保证configs目录的权限为750，配置文件的权限为640。

# 快速入门

## 简介

本章节旨在帮助用户快速完成推理微服务MIS的部署与运行。主要介绍如何在Atlas 800I A2 推理服务器上完成环境准备、模型权重配置与服务启动等关键步骤。
推理微服务MIS提供OpenAI API兼容接口，可无缝对接现有应用。用户仅需完成环境初始化与模型路径配置，即可通过标准API发起推理请求，实现快速验证与集成。

## 环境准备

- 准备Atlas A2 推理系列产品的服务器，并安装对应的驱动和固件，具体安装过程请参见《CANN 软件安装指南》中的[“安装NPU驱动和固件”](https://www.hiascend.com/document/detail/zh/canncommercial/83RC1/softwareinst/instg/instg_0005.html?Mode=PmIns&InstallType=local&OS=openEuler&Software=cannToolKit)章节（商用版）或[“安装NPU驱动和固件”](https://www.hiascend.com/document/detail/zh/CANNCommunityEdition/83RC1/softwareinst/instg/instg_0005.html?Mode=PmIns&InstallType=local&OS=openEuler&Software=cannToolKit)章节（社区版）。
- 安装CANN Toolkit，具体安装过程请参见《CANN 软件安装指南》的[“安装CANN”](https://www.hiascend.com/document/detail/zh/canncommercial/83RC1/softwareinst/instg/instg_0008.html?Mode=PmIns&InstallType=local&OS=openEuler&Software=cannToolKit)章节（商用版）或[“安装CANN”](https://www.hiascend.com/document/detail/zh/CANNCommunityEdition/83RC1/softwareinst/instg/instg_0008.html?Mode=PmIns&InstallType=local&OS=openEuler&Software=cannToolKit)章节（社区版）。
- 安装MIS以及相关依赖，具体安装过程请参见[环境部署](#环境部署)。

## 启动MIS服务

服务运行依赖：
- fastapi 0.121.1
- numpy 1.26.4
- pydantic 2.12.2
- PyYAML 6.0.3
- starlette 0.49.1
- uvloop 0.21.0
- vllm 0.11.0
- vllm-ascend 0.11.0rc2

运行流程：

1. 下载模型权重并设置路径。部署MIS前需将模型权重放置在本地，可选择从开源模型社区(如魔搭社区、魔乐社区、Huggingface)下载对应权重（safetensors类型权重）。假设模型权重下载路径为/data/Qwen3-8B，则将MIS权重缓存路径的环境变量MIS_CACHE_PATH设置为/data。

        export MIS_CACHE_PATH=/data
2. 配置CANN运行环境变量。确保安装环境中已执行CANN环境变量配置脚本，使环境变量生效。具体执行路径，请以实际安装路径为准。

        source $HOME/Ascend/ascend-toolkit/set_env.sh #此处为示例安装路径，根据实际安装路径修改
        source $HOME/Ascend/nnal/atb/set_env.sh #此处为示例安装路径，根据实际安装路径修改
3. 指定运行模型。

        export MIS_MODEL=Qwen3-8B
4. 执行启动命令。

    进入MIS软件包安装路径，例如：

        cd $HOME/Ascend/mis/7.3.0
    执行如下命令部署MIS

        ./mis.pyz
    或通过Python解释器执行部署命令（请根据对应Python环境调整）

        python3 mis.pyz

- 请确保模型文件来源可信，文件未被篡改且权重类型为safetensors。
- 请确保模型权重路径，MIS安装路径及所有文件的属主与运行用户一致。
- 请确保参数配置文件不为软链接，路径字符串长度不大于1024。
- 请确保模型权重路径权限为750，权重文件为640。
- 推理微服务MIS监听至127.0.0.1且MIS需要通过组件集成的方式与其他系统配合才能形成完整的推理服务系统 ，请参考推理微服务安全加固。

## 发起请求

使用OpenAI API发起对话请求。

```python
from openai import OpenAI
client = OpenAI(
    base_url="http://127.0.0.1:8000/openai/v1",
    api_key="dummy_key"  # 占位字段，不作为认证凭据
)
response = client.chat.completions.create(
    model="Qwen3-8B",
    messages=[
        {"role": "system", "content": "你是一个友好的AI助手。"},
        {"role": "user", "content": "你好"},
    ],
    max_tokens=100
)
print(response.choices[0].message)
```

# 特性介绍

Mind Inference Service基于昇腾硬件提供即装即用的在线推理服务，支持模型如下：

| 模型名      | 计算服务器硬件型号     | 数据类型 | 后端   | 最低内存需求 |
|----------|---------------|------|------|--------|
| qwen3-8b | Atlas 800I A2 | BF16 | vLLM | 16GB   |

# 安全声明

- 用户应根据自身业务，重新审视整个系统的网络安全加固措施。
- 外部下载的软件代码或程序可能存在风险，功能的安全性需由用户保证。

# License

Mind Inference Service以Mulan PSL v2许可证许可，对应许可证文本可查阅[LICENSE](LICENSE.md)。

# 建议与交流

欢迎大家为社区做贡献。如果有任何疑问或建议，请提交issues，我们会尽快回复。感谢您的支持。
