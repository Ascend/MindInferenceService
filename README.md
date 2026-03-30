# Mind Inference Service

- [最新消息](#最新消息)
- [简介](#简介)
- [目录结构](#目录结构)
- [版本说明](#版本说明)
- [环境部署](#环境部署)
- [编译流程](#编译流程)
- [快速入门](#快速入门)
- [特性介绍](#特性介绍)
- [安全声明](#安全声明)
- [免责声明](#免责声明)
- [License](#license)
- [贡献声明](#贡献声明)
- [建议与交流](#建议与交流)

# 最新消息

- [2025.12.30]: 🚀 Mind Inference Service支持Qwen3-8B模型

# 简介

    昇腾推理微服务MIS（Mind Inference Service）提供了模型推理服务，无需复杂的依赖安装，即可快速完成部署。针对昇腾硬件进行深度的性能优化，省去繁琐的调优过程。提供行业标准接口，便于集成到企业业务系统中，助力业务高效运行。

<div align="center">

[![Zread](https://img.shields.io/badge/Zread-Ask_AI-_.svg?style=flat&color=0052D9&labelColor=000000&logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTQuOTYxNTYgMS42MDAxSDIuMjQxNTZDMS44ODgxIDEuNjAwMSAxLjYwMTU2IDEuODg2NjQgMS42MDE1NiAyLjI0MDFWNC45NjAxQzEuNjAxNTYgNS4zMTM1NiAxLjg4ODEgNS42MDAxIDIuMjQxNTYgNS42MDAxSDQuOTYxNTZDNS4zMTUwMiA1LjYwMDEgNS42MDE1NiA1LjMxMzU2IDUuNjAxNTYgNC45NjAxVjIuMjQwMUM1LjYwMTU2IDEuODg2NjQgNS4zMTUwMiAxLjYwMDEgNC45NjE1NiAxLjYwMDFaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik00Ljk2MTU2IDEwLjM5OTlIMi4yNDE1NkMxLjg4ODEgMTAuMzk5OSAxLjYwMTU2IDEwLjY4NjQgMS42MDE1NiAxMS4wMzk5VjEzLjc1OTlDMS42MDE1NiAxNC4xMTM0IDEuODg4MSAxNC4zOTk5IDIuMjQxNTYgMTQuMzk5OUg0Ljk2MTU2QzUuMzE1MDIgMTQuMzk5OSA1LjYwMTU2IDE0LjExMzQgNS42MDE1NiAxMy43NTk5VjExLjAzOTlDNS42MDE1NiAxMC42ODY0IDUuMzE1MDIgMTAuMzk5OSA0Ljk2MTU2IDEwLjM5OTlaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik0xMy43NTg0IDEuNjAwMUgxMS4wMzg0QzEwLjY4NSAxLjYwMDEgMTAuMzk4NCAxLjg4NjY0IDEwLjM5ODQgMi4yNDAxVjQuOTYwMUMxMC4zOTg0IDUuMzEzNTYgMTAuNjg1IDUuNjAwMSAxMS4wMzg0IDUuNjAwMUgxMy43NTg0QzE0LjExMTkgNS42MDAxIDE0LjM5ODQgNS4zMTM1NiAxNC4zOTg0IDQuOTYwMVYyLjI0MDFDMTQuMzk4NCAxLjg4NjY0IDE0LjExMTkgMS42MDAxIDEzLjc1ODQgMS42MDAxWiIgZmlsbD0iI2ZmZiIvPgo8cGF0aCBkPSJNNCAxMkwxMiA0TDQgMTJaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik00IDEyTDEyIDQiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSIxLjUiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPgo8L3N2Zz4K&logoColor=ffffff)](https://zread.ai/Ascend/MindInferenceService)&nbsp;&nbsp;&nbsp;&nbsp;
[![DeepWiki](https://img.shields.io/badge/DeepWiki-Ask_AI-_.svg?style=flat&color=0052D9&labelColor=000000&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACwAAAAyCAYAAAAnWDnqAAAAAXNSR0IArs4c6QAAA05JREFUaEPtmUtyEzEQhtWTQyQLHNak2AB7ZnyXZMEjXMGeK/AIi+QuHrMnbChYY7MIh8g01fJoopFb0uhhEqqcbWTp06/uv1saEDv4O3n3dV60RfP947Mm9/SQc0ICFQgzfc4CYZoTPAswgSJCCUJUnAAoRHOAUOcATwbmVLWdGoH//PB8mnKqScAhsD0kYP3j/Yt5LPQe2KvcXmGvRHcDnpxfL2zOYJ1mFwrryWTz0advv1Ut4CJgf5uhDuDj5eUcAUoahrdY/56ebRWeraTjMt/00Sh3UDtjgHtQNHwcRGOC98BJEAEymycmYcWwOprTgcB6VZ5JK5TAJ+fXGLBm3FDAmn6oPPjR4rKCAoJCal2eAiQp2x0vxTPB3ALO2CRkwmDy5WohzBDwSEFKRwPbknEggCPB/imwrycgxX2NzoMCHhPkDwqYMr9tRcP5qNrMZHkVnOjRMWwLCcr8ohBVb1OMjxLwGCvjTikrsBOiA6fNyCrm8V1rP93iVPpwaE+gO0SsWmPiXB+jikdf6SizrT5qKasx5j8ABbHpFTx+vFXp9EnYQmLx02h1QTTrl6eDqxLnGjporxl3NL3agEvXdT0WmEost648sQOYAeJS9Q7bfUVoMGnjo4AZdUMQku50McDcMWcBPvr0SzbTAFDfvJqwLzgxwATnCgnp4wDl6Aa+Ax283gghmj+vj7feE2KBBRMW3FzOpLOADl0Isb5587h/U4gGvkt5v60Z1VLG8BhYjbzRwyQZemwAd6cCR5/XFWLYZRIMpX39AR0tjaGGiGzLVyhse5C9RKC6ai42ppWPKiBagOvaYk8lO7DajerabOZP46Lby5wKjw1HCRx7p9sVMOWGzb/vA1hwiWc6jm3MvQDTogQkiqIhJV0nBQBTU+3okKCFDy9WwferkHjtxib7t3xIUQtHxnIwtx4mpg26/HfwVNVDb4oI9RHmx5WGelRVlrtiw43zboCLaxv46AZeB3IlTkwouebTr1y2NjSpHz68WNFjHvupy3q8TFn3Hos2IAk4Ju5dCo8B3wP7VPr/FGaKiG+T+v+TQqIrOqMTL1VdWV1DdmcbO8KXBz6esmYWYKPwDL5b5FA1a0hwapHiom0r/cKaoqr+27/XcrS5UwSMbQAAAABJRU5ErkJggg==)](https://deepwiki.com/Ascend/MindInferenceService)
   
</div>

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

Mind Inference Service的版本说明包含MIS的软件版本配套关系和软件包下载以及每个版本的特性变更说明，具体请参见[版本说明](./docs/zh/release_notes.md)。

# 环境部署

介绍Mind Inference Service的安装方式。具体请参见[安装部署](./docs/zh/installation_guide.md)。

# 编译流程

编译环境依赖：

- Python 3.11.4

编译流程：

1. 拉取mis整体源码，例如放在/home目录下。
2. 执行以下命令，进入/home/MIS目录，选择构建脚本执行：
    **cd /home/MIS**

        python compile.py
3. 执行完成后，在/home/MIS/dist目录下生成可直接执行的mis.pyz文件。
4. 将MIS/configs目录复制到mis.pyz文件所在目录，即可通过mis.pyz文件运行mis服务：
    **cp -r /home/MIS/configs /home/MIS/dist**

        cd /home/MIS/dist
        python3 mis.pyz

- 请注意，mis服务启动时会对configs目录进行校验，请保证configs目录的权限为750，配置文件的权限为640。

# 快速入门

Mind Inference Service的快速入门，包括快速安装、数据准备和工具使用等，具体请参见[快速入门](./docs/zh/quick_start.md)。

# 特性介绍

Mind Inference Service基于昇腾硬件提供即装即用的在线推理服务，支持模型如下：

| 模型名      | 计算服务器硬件型号     | 数据类型 | 后端   | 最低内存需求 |
|----------|---------------|------|------|--------|
| qwen3-8b | Atlas 800I A2 | BF16 | vLLM | 16GB   |

# 安全声明

- 用户应根据自身业务，重新审视整个系统的网络安全加固措施。
- 外部下载的软件代码或程序可能存在风险，功能的安全性需由用户保证。

描述Mind Inference Service的安全加固信息、公网地址信息及通信矩阵等内容，具体请参见[安全加固](./docs/zh/security_hardening.md)与[附录](./docs/zh/appendix.md)。

# 免责声明

- 本仓库代码中包含多个开发分支，这些分支可能包含未完成、实验性或未测试的功能。在正式发布前，这些分支不应被应用于任何生产环境或者依赖关键业务的项目中。请务必使用我们的正式发行版本，以确保代码的稳定性和安全性。使用开发分支所导致的任何问题、损失或数据损坏，本项目及其贡献者概不负责。
- 正式版本请参考release版本<https://gitcode.com/ascend/MindInferenceService/releases>。

# License

Mind Inference Service以Mulan PSL v2许可证许可，对应许可证文本可查阅[LICENSE](LICENSE.md)。

Mind Inference Service docs目录下的文档适用CC-BY 4.0许可证，具体请参见[LICENSE](./docs/LICENSE)文件。

# 贡献声明

- 贡献前，请先签署[开放项目贡献者许可协议（CLA）](https://clasign.osinfra.cn/sign/gitee_ascend-1611222220829317930)。
- 如果您遇到bug，请提交[issue](https://gitcode.com/Ascend/MindInferenceService/issues)。
- 如果您计划贡献bug-fixes，请提交Pull Requests，参见[具体要求](CONTRIBUTING.md)。
- 如果您计划贡献新特性、功能，请先创建issue与我们讨论。写明需求背景/目的，如何设计，对现有API等的影响。未经讨论提交PR可能会导致请求被拒绝，因为项目演进方向可能与您的想法存在偏差。
- 更详细的贡献流程，请参考[贡献指南](CONTRIBUTING.md)

# 建议与交流

欢迎大家为社区做贡献。如果有任何疑问或建议，请提交[issues](https://gitcode.com/ascend/MindInferenceService/issues)，我们会尽快回复。感谢您的支持。
