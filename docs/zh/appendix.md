# 附录<a name="ZH-CN_TOPIC_0000002496569313"></a>

## 安装软件包参数说明<a name="ZH-CN_TOPIC_0000002471044384"></a>

本章节介绍了run格式软件包相关参数说明，run格式软件包支持通过命令行参数进行一键式安装，各个命令之间可以配合使用，用户根据安装需要选择对应参数，所有参数都是可选参数。

安装命令格式： ./Ascend-mis\__\{version\}_\_linux-_\{arch\}_.run \[options\]

详细参数参见[表1](#table13536440982)。

**表 1**  参数说明<a id="table13536440982"></a>

|输入参数|含义|
|--|--|
|--help \| -h|查询帮助信息。|
|--info|查询包构建信息。|
|--list|查询文件列表。|
|--check|查询包完整性。|
|--quiet \| -q|启用静默模式。需要和--install参数配合使用。|
|--nox11|不生成一个xterm终端。|
|--noexec|不运行嵌入的脚本。|
|--extract=\<path>|直接提取到目标目录（绝对路径或相对路径）。通常与--noexec选项一起使用，仅用于提取文件而不运行它们。|
|--tar arg1 [arg2 ...]|通过tar命令访问归档文件的内容。|
|--version|查询软件包的MIS版本。|
|--install|MIS软件包安装操作命令。<li>当前路径和安装路径不能存在非法字符，仅支持大小写字母、数字、-_./特殊字符。</li><li>安装路径下不能存在名为mis的文件或文件夹。</li><li>若存在名为mis的软链接，则会被覆盖。</li>|
|--install-path=\<path>|（可选）自定义软件包安装根目录。如未设置，默认为当前命令执行所在目录。<li>建议用户使用绝对路径安装MIS，指定安装路径时请避免使用相对路径。</li><li>需要和--install参数配合使用。</li><li>传入的路径参数不能存在非法字符，仅支持大小写字母、数字、-_./特殊字符。</li>|
|--uninstall|卸载所有已安装的MIS版本。|


> [!NOTE] 说明
>以下参数未展示在--help参数中，用户请勿直接使用。
>-   --xwin：使用xwin模式运行。
>-   --phase2：要求执行第二步动作。


## 日志说明<a name="ZH-CN_TOPIC_0000002498452221"></a>

本系统内置了日志记录功能，用于记录MIS运行过程中的操作日志和服务日志。

-   日志会同时输出到控制台（标准输出）和磁盘文件。
-   控制台输出格式与磁盘文件格式一致。

**日志落盘地址<a name="section1982832611817"></a>**

默认日志落盘路径：$HOME/log/mis。

日志文件名以 log\_mis\_disk\_ 为前缀，后缀根据日志类型和时间戳生成，例如：

-   普通日志：log\_mis\_disk\_20250405\_143000.log
-   操作日志：log\_mis\_disk\_operation\_20250405\_143000.log
-   服务日志：log\_mis\_disk\_service\_20250405\_143000.log

**日志文件管理<a name="section177191716122916"></a>**

-   日志文件大小限制：单个日志文件最大为 50MB，超过后会自动进行日志轮转（即生成新的日志文件）。
-   日志文件数量限制：系统最多保留 36 个日志文件，超出部分会自动删除最早的日志文件。
-   日志文件权限：
    -   当前正在写入的日志文件权限为 640（即用户可读写，组可读）。
    -   已轮转的日志文件权限为 440（即用户和组均可读，不可写）。

> [!NOTE] 说明
>-   请确保日志落盘路径及文件与运行用户属主一致。
>-   请确保日志落盘路径权限为750。
>-   请确保日志落盘路径与文件不为软链接，路径字符串长度不能大于1024。


## 公网地址<a name="ZH-CN_TOPIC_0000002469838190"></a>

MIS软件中会存在公开网址，MIS本身不会访问也不会造成风险。

更多公网地址请参考[MIS 公网地址.xlsx](./resource/MIS%20公网地址.xlsx)。


## 三方环境变量使用设置<a name="ZH-CN_TOPIC_0000002466051662"></a>

MIS在服务部署过程中会设置如下三方环境变量。

|环境变量名称|描述|
|--|--|
|VLLM_DO_NOT_TRACK|用于控制是否禁用统计信息的收集。取值为1，即表示禁用统计信息的收集。|
|HF_DATASETS_OFFLINE|用于控制是否以离线模式运行数据集相关操作。取值为1，即表示以离线模式运行数据集相关操作。|
|HF_HUB_OFFLINE|用于控制是否以离线模式运行Hugging Face Hub相关操作。取值为1，即表示以离线模式运行Hugging Face Hub相关操作。|
|TRANSFORMERS_OFFLINE|用于控制是否以离线模式运行Transformers相关操作。取值为1，即表示以离线模式运行Transformers相关操作。|
|VLLM_HOST_IP|vLLM分布式环境中当前节点的IP地址。取值为127.0.0.1。|
|GLOO_SOCKET_IFNAME|强制Gloo使用loopback接口（127.0.0.1）。取值为lo。|



## vLLM环境变量参考列表<a name="ZH-CN_TOPIC_0000002496449369"></a>

vLLM环境变量对应版本的详细信息请参考[vLLM文档-环境变量](https://docs.vllm.ai/en/latest/configuration/env_vars.html?h=env)。

vLLM环境变量可能会影响MIS的部署环境，参考如下：

**表 1** **分布式与并行配置**

|环境变量名称|类型|描述|
|--|--|--|
|VLLM_HOST_IP|str|节点IP地址。|
|VLLM_PORT|int|通信端口。|
|VLLM_DP_RANK|int|数据并行rank，默认为0。|
|VLLM_DP_SIZE|int|数据并行大小，默认为1。|
|VLLM_USE_RAY_COMPILED_DAG_CHANNEL_TYPE|str|Ray编译图通道类型。默认为auto，取值范围：[auto, nccl, shm]。|
|VLLM_DP_MASTER_IP|str|数据并行主节点IP，默认为127.0.0.1。|
|VLLM_DP_MASTER_PORT|int|数据并行主节点端口，默认为0。|


**表 2** **注意力机制配置**

|环境变量名称|类型|描述|
|--|--|--|
|VLLM_ATTENTION_BACKEND|str|Attention计算后端。|
|VLLM_V1_USE_PREFILL_DECODE_ATTENTION|bool|是否在V1引擎中为注意力计算使用独立的预填充和解码内核。默认为0，取值范围：[0, 1]，其中：<li>0：表示使用统一的内核。</li><li>1：表示使用独立的预填充和解码内核。</li>|
|VLLM_FLASH_ATTN_VERSION|int|强制指定使用的Flash Attention版本，仅在使用Flash Attention后端时有效。取值范围[2, 3]，其中：<li>2：表示使用Flash Attention 2。</li><li>3：表示使用Flash Attention 3。</li>|
|VLLM_USE_FLASHINFER_SAMPLER|bool|是否使用FlashInfer采样器。默认为0，取值范围：[0, 1]，其中：<li>0：表示不使用FlashInfer采样器。</li><li>1：表示使用FlashInfer采样器。</li>|
|VLLM_DISABLE_FLASHINFER_PREFILL|bool|是否禁用FlashInfer的预填充注意力内核。默认为0，取值范围：[0, 1]，其中：<li>0：表示启用FlashInfer预填充内核。</li><li>1：表示禁用FlashInfer预填充内核。</li>|


**表 3** **API服务器配置**

|环境变量名称|类型|描述|
|--|--|--|
|VLLM_API_KEY|str|API服务器认证密钥。|
|VLLM_DEBUG_LOG_API_SERVER_RESPONSE|bool|是否记录API服务器的详细响应日志。默认为0，取值范围：[0, 1]，其中：<li>0：表示不记录API服务器的详细响应日志。</li><li>1：表示记录API服务器的详细响应日志。</li>|
|VLLM_HTTP_TIMEOUT_KEEP_ALIVE|int|HTTP长连接超时时长（秒）。默认为5。|
|VLLM_RPC_TIMEOUT|int|ZMQ客户端超时时长（毫秒）。默认为10000。|
|VLLM_SERVER_DEV_MODE|bool|是否开启服务器的开发者模式。默认为0，取值范围：[0, 1]，其中：0：表示关闭开发者模式。1：表示开启开发者模式，即启用额外的调试端点。|
|VLLM_KEEP_ALIVE_ON_ENGINE_DEATH|bool|当底层引擎进程出错停止后，API服务器是否继续保持存活。默认为0，取值范围：[0, 1]，其中：<li>0：表示引擎出错后API服务器也随之关闭。</li><li>1：表示引擎出错后API服务器继续保持存活。</li>|
|VLLM_ENABLE_RESPONSES_API_STORE|bool|是否在OpenAI API服务器中启用对Responses API store参数的支持。默认为0，取值范围：[0, 1]，其中：<li>0：表示禁用，即忽略store参数。</li><li>1：表示启用，即在内存中保留请求的输入和输出消息。</li>|
|VLLM_LOOPBACK_IP|str|强制设置回环IP。|
|VLLM_PROCESS_NAME_PREFIX|str|进程名前缀。默认值为VLLM。|


**表 4** **内核选择配置**

|环境变量名称|类型|描述|
|--|--|--|
|VLLM_DISABLED_KERNELS|list|禁用的量化内核列表。|
|VLLM_COMPUTE_NANS_IN_LOGITS|bool|是否在计算logits时检查并报告NaN值。默认为0，取值范围：[0, 1]，其中：<li>0：表示不检查NaN值。</li><li>1：表示检查并报告NaN值。</li>|


**表 5** **日志与监控配置**

|环境变量名称|类型|描述|
|--|--|--|
|VLLM_CONFIGURE_LOGGING|int|是否启用日志配置。默认为1，取值范围：[0, 1]，其中：0：表示禁止使用日志配置。1：表示启用日志配置。|
|VLLM_LOGGING_CONFIG_PATH|str|日志配置文件路径。|
|VLLM_LOGGING_LEVEL|str|日志级别，默认为INFO。|
|VLLM_LOGGING_STREAM|str|日志输出流，默认为ext://sys.stdout。|
|VLLM_LOGGING_PREFIX|str|日志消息前缀。|
|VLLM_LOG_STATS_INTERVAL|float|统计日志间隔时长（秒）。|
|VLLM_LOG_BATCHSIZE_INTERVAL|float|Batch size日志间隔时长（秒）。|
|VLLM_RINGBUFFER_WARNING_INTERVAL|int|环形缓冲区警告间隔时长（秒），默认为60。|
|VLLM_TRACE_FUNCTION|int|是否启用函数调用跟踪。默认为0，取值范围：[0, 1]，其中：<li>0：表示禁用函数跟踪。</li><li>1：表示启用函数调用跟踪。</li>|
|VLLM_DEBUG_DUMP_PATH|str|FX图转储目录。|
|VLLM_PATTERN_MATCH_DEBUG|str|自定义pass模式匹配调试。|
|VLLM_TORCH_PROFILER_DIR|str|Torch profiler输出目录。|
|VLLM_TORCH_PROFILER_RECORD_SHAPES|bool|在使用PyTorch Profiler时，是否记录操作的输入和输出张量形状。默认为0，取值范围：[0, 1]，其中：<li>0：表示性能分析时不记录张量形状信息。</li><li>1：表示性能分析时记录张量形状信息。</li>|
|VLLM_TORCH_PROFILER_WITH_PROFILE_MEMORY|bool|在使用PyTorch Profiler时，是否分析张量内存使用情况。默认为0，取值范围：[0, 1]，其中：<li>0：表示性能分析时不分析内存使用情况。</li><li>1：表示性能分析时分析张量内存使用情况。</li>|
|VLLM_TORCH_PROFILER_WITH_STACK|bool|在使用PyTorch Profiler时，是否记录Python堆栈信息。默认为1，取值范围：[0, 1]，其中：<li>0：表示性能分析时不记录堆栈信息。</li><li>1：表示性能分析时记录堆栈信息。</li>|
|VLLM_TORCH_PROFILER_WITH_FLOPS|bool|在使用PyTorch Profiler时，是否分析操作的浮点运算次数。默认为0，取值范围：[0, 1]，其中：<li>0：表示性能分析时不记录FLOPS数据。</li><li>1：表示性能分析时记录FLOPS数据。</li>|


**表 6** **CPU后端配置**

|环境变量名称|类型|描述|
|--|--|--|
|VLLM_CPU_KVCACHE_SPACE|int|CPU键值缓存空间。|
|VLLM_CPU_OMP_THREADS_BIND|str|OpenMP线程绑定的CPU核心。默认为auto。|


**表 7** **测试与调试配置**

|环境变量名称|类型|描述|
|--|--|--|
|VLLM_TEST_FORCE_LOAD_FORMAT|str|测试强制加载格式。默认为dummy。|
|VLLM_TEST_USE_PRECOMPILED_NIGHTLY_WHEEL|bool|是否在测试中使用预编译nightly版本wheel包。默认为0，取值范围：[0, 1]，其中：<li>0：表示不使用预编译的nightly版本。</li><li>1：表示使用预编译的nightly版本进行测试。</li>|
|VLLM_ALLOW_INSECURE_SERIALIZATION|bool|是否允许不安全的序列化方法。默认为0，取值范围：[0, 1]，其中：<li>0：表示禁用不安全的序列化。</li><li>1：表示允许使用不安全的序列化方法。</li>|
|VLLM_MLA_DISABLE|bool|是否禁用MLA注意力优化。默认为0，取值范围：[0, 1]，其中：<li>0：表示启用MLA注意力优化。</li><li>1：表示禁用MLA注意力优化。</li>|
|VLLM_GC_DEBUG|str|GC调试配置。|


**表 8** **通信与RPC配置**

|环境变量名称|类型|描述|
|--|--|--|
|VLLM_RPC_BASE_PATH|str|RPC通信基础路径。|
|VLLM_RPC_TIMEOUT|int|RPC超时时长（毫秒）。默认为10000。|
|VLLM_ENGINE_ITERATION_TIMEOUT_S|int|引擎迭代超时时长（秒）。默认为60。|
|VLLM_HTTP_TIMEOUT_KEEP_ALIVE|int|HTTP长连接保持超时时长（秒）。默认为5。|
|VLLM_MQ_MAX_CHUNK_BYTES_MB|int|RPC消息队列最大块（MB）。默认为16。|


**表 9** **统计和调试配置**

|环境变量名称|类型|描述|
|--|--|--|
|VLLM_USAGE_STATS_SERVER|str|使用统计服务器URL。默认为https://stats.vllm.ai。|
|VLLM_NO_USAGE_STATS|bool|是否禁止向vLLM服务器发送使用情况统计信息。默认为0，取值范围：[0, 1]，其中：<li>0：表示允许发送使用统计。</li><li>1：表示禁止发送任何使用统计。</li>|
|VLLM_DO_NOT_TRACK|bool|是否禁止跟踪和上报使用数据。默认为0，取值范围：[0, 1]，其中：<li>0：表示允许跟踪和上报数据。</li><li>1：表示禁止跟踪和上报数据。</li>|
|VLLM_USAGE_SOURCE|str|使用统计来源。默认为production。|


**表 10** **其他配置**

|环境变量名称|类型|描述|
|--|--|--|
|VLLM_V1_OUTPUT_PROC_CHUNK_SIZE|int|V1引擎输出处理块大小。默认为128。|
|VLLM_SLEEP_WHEN_IDLE|bool|是否开启空闲时降低CPU使用率的休眠功能。默认为0，取值范围：[0, 1]，其中：<li>0：表示关闭空闲休眠功能。</li><li>1：表示激活空闲休眠功能。</li>|
|VLLM_USE_V1|bool|是否启用vLLM V1版本的引擎。默认为1，取值范围：[0, 1]，其中：<li>0：表示启用V0引擎。</li><li>1：表示启用V1引擎。</li>|
|VLLM_ENABLE_V1_MULTIPROCESSING|bool|是否在V1代引擎启用多进程支持。默认为1，取值范围：[0, 1]，其中：<li>0：表示禁用V1多进程。</li><li>1：表示启用V1多进程。</li>|



## 软件通讯矩阵示例<a name="ZH-CN_TOPIC_0000002504077011"></a>

> [!NOTE] 说明
>-   vLLM基于PyTorch分布式服务开启的通信端口默认为全0侦听，为了降低安全风险，建议用户针对此场景进行安全加固（可参见[安全加固](./security_hardening.md)）。如使用iptables配置防火墙，在运行推理服务前限制外部对PyTorch分布式使用端口的访问，在运行推理服务结束后清理防火墙规则。HTTP协议存在安全风险，建议使用HTTPS安全协议。
>-   推理微服务MIS监听至127.0.0.1，默认端口为8000，若部署时修改环境变量MIS\_PORT请参考实际端口。
>-   PyTorch（与vLLM）的通信端口号与vLLM环境变量VLLM\_PORT设置相关。

**vLLM侦听示例**（LISTEN）

\(单机部署情况下\)如下述7个端口侦听\(用于vLLM内部通讯\)：

```
# 示例
tcp        0      0 127.0.0.1:39601       0.0.0.0:*               LISTEN
tcp        0      0 127.0.0.1:39465       0.0.0.0:*               LISTEN      
tcp        0      0 127.0.0.1:37287       0.0.0.0:*               LISTEN 
tcp        0      0 127.0.0.1:36361       0.0.0.0:*               LISTEN      
tcp        0      0 127.0.0.1:36289       0.0.0.0:*               LISTEN      
tcp        0      0 127.0.0.1:45093       0.0.0.0:*               LISTEN 
tcp        0      0 127.0.0.1:38382       0.0.0.0:*               LISTEN
```


