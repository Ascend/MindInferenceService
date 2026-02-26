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
1. 提交错误报告：如果您在MIS中发现了一个不存在安全问题的漏洞，请在MIS仓库中的Issues中搜索，以防该漏洞被重复提交，如果找不到漏洞可以创建一个新的Issues。如果发现了一个安全问题请不要将其公开，请参阅安全问题处理方式。提交错误报告时应该包含完整信息。
2. 安全问题处理：本项目中对安全问题处理的形式，请通过邮箱通知项目核心人员确认编辑。
3. 解决现有问题：通过查看仓库的Issues列表可以发现需要处理的问题信息, 可以尝试解决其中的某个问题。
4. 如何提出新功能：请使用Issues的Feature标签进行标记，我们会定期处理和确认开发。
5. 开始贡献：
    - Fork本项目的仓库
    - Clone到本地
    - 创建开发分支
    - 本地自测，提交前请通过所有的单元测试，包括为您要解决的问题新增的单元测试。
    - 提交代码
    - 新建Pull Request
    - 代码检视，您需要根据评审意见修改代码，并重新提交更新。此流程可能涉及多轮迭代。
    - 当您的PR获得足够数量的检视者批准后，Committer会进行最终审核。
    - 审核和测试通过后，CI会将您的PR合并入到项目的主干分支。

# 建议与交流

欢迎大家为社区做贡献。如果有任何疑问或建议，请提交[issues](https://gitcode.com/ascend/MindInferenceService/issues)，我们会尽快回复。感谢您的支持。
