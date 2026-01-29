# 参数配置<a name="ZH-CN_TOPIC_0000002496570833"></a>

## 环境变量列表<a name="ZH-CN_TOPIC_0000002496571433"></a>

**表 1**  MIS环境变量

|名称|类型|描述|取值范围|
|--|--|--|--|
|MIS_CACHE_PATH|str|缓存权重路径，需具有正确的权限与所属。|默认值：$HOME/mis/.cache。|
|MIS_MODEL|str|服务模型名称。|默认值：Qwen3-8B。<br>取值范围：[Qwen3-8B]。|
|MIS_ENGINE_TYPE|str|模型引擎类型。|默认值：vllm。<br>取值范围：[vllm]。|
|MIS_CONFIG|str|优化配置名称。|默认值：atlas800ia2-1x32gb-bf16-vllm-default。<br>取值范围请参考[模型支持与配置列表](#模型最优配置)。|
|MIS_PORT|int|服务绑定的端口。|默认值：8000。<br>取值范围：[1024, 65535]。|
|MIS_ENABLE_DOS_PROTECTION|bool|使能或去使能MIS的防DOS攻击特性。包含限制请求头/体大小、限制并发、限流、限制超时。|默认值：True。<br>当取值为“true”（忽略大小写）或“1”时设为True；其他值设为False。|
|MIS_LOG_LEVEL|str|MIS的日志等级。|默认值：INFO。<br>取值范围：[DEBUG, INFO, WARNING, ERROR, CRITICAL]。|
|MIS_MAX_LOG_LEN|int|配置日志的最大长度。|默认值：2048。<br>取值范围：[0, 8192]。|
|UVICORN_LOG_LEVEL|str|配置Uvicorn服务的日志级别。|默认值：info。<br>取值范围：[debug, info, warning, error, critical]。|


> [!NOTE] 说明
>三方组件的环境变量可能会更改MIS的服务状态，请参阅对应三方组件文档。


## 模型最优配置<a name="ZH-CN_TOPIC_0000002463252414"></a>

> [!NOTE] 说明
>-   请确保参数配置路径及文件与运行用户属主一致。
>-   请确保参数配置文件的大小不超过1MB。
>-   请确保参数配置文件不为软链接，路径字符串长度不大于1024。
>-   请确保参数配置路径权限为750，配置文件为640。

**模型支持<a name="section7482154712357"></a>**

**表 1**  模型支持与配置列表

|配置模型名|可选值|计算服务器硬件型号|计算卡规格|数据类型|后端|性能倾向|最低内存需求|
|--|--|--|--|--|--|--|--|
|qwen3-8b|atlas800ia2-1x32gb-bf16-vllm-default|Atlas 800I A2|1x32GB|BF16|vLLM|均衡|16GB|
|qwen3-8b|atlas800ia2-1x32gb-bf16-vllm-latency|Atlas 800I A2|1x32GB|BF16|vLLM|低时延|16GB|
|qwen3-8b|atlas800ia2-1x32gb-bf16-vllm-throughput|Atlas 800I A2|1x32GB|BF16|vLLM|高吞吐|16GB|


**优化配置参数示例<a name="section49261519367"></a>**

```
vllm:  # 引擎类型 (必填项，可选项为vllm，与后续engine_type对应)  
  dtype: bfloat16  # 具体配置信息(选填项，详情见如下配置参数总览)  
  tensor_parallel_size: 1  
  pipeline_parallel_size: 1  
  max_num_seqs: 128  
  block_size: 128
engine_type: vllm  # 必填项，可选项为vllm, 与引擎类型相应
model: Qwen3-8B  # 模型权重路径(必填项)
```

**优化配置参数列表<a name="section03608318374"></a>**

**表 2**  模型与引擎配置

|参数名|类型|描述|
|--|--|--|
|vllm|dict|引擎类型对应的配置字典。键名及其值请参考[表3 引擎详细配置](#table3)。|
|engine_type|str|引擎类型，取值范围：[vllm]。|
|model|str|模型的权重路径，取值范围：[Qwen3-8B]。|


**表 3**  引擎详细配置<a id="table3"></a>

|参数名|**类型**|**描述**|
|--|--|--|
|dtype|str|数据类型，取值范围：[bfloat16]。|
|tensor_parallel_size|int|张量并行大小，取值范围：[1, 2, 4, 8]。|
|pipeline_parallel_size|int|管道并行大小，取值范围：1。|
|distributed_exector_size|str|分布式执行器后端，取值范围：[mp]。|
|max_num_seqs|int|最大序列数，取值范围：[1, 512]。|
|max_model_len|int|最大模型长度（根据模型参数实际配置），取值范围：[1, 64000]。|
|max_num_batched_tokens|int|最大批处理词元数（根据模型参数实际配置），取值范围：[1, 64000]。|
|gpu_memory_utilization|float|GPU内存利用率，取值范围：[0.0, 1.0]。|
|block_size|int|块大小，取值范围：[16, 32, 64, 128]。|
|swap_space|int|交换空间大小（GB），取值范围：[0, 1024]。|
|cpu_offload_gb|int|CPU卸载大小（GB），取值范围：[0, 1024]。|
|scheduling_policy|str|调度策略，取值范围：[fcfs, priority]。|
|num_scheduler_steps|int|多步调度器数，取值范围：[1, 1024]。|
|enable_chunked_prefill|bool|是否启用分块预填充，取值范围：[True, False]。|
|enable_prefix_caching|bool|是否启用前缀缓存，取值范围：[True, False]。|
|multi_step_stream_outputs|bool|是否启用多步流输出，取值范围：[True, False]。|
|enforce_eager|bool|是否强制即时执行模式，取值范围：[True, False]。|



