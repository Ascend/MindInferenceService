# 支持的接口列表及参数<a name="ZH-CN_TOPIC_0000002496569301"></a>

## 约束<a name="ZH-CN_TOPIC_0000002516596123"></a>

MIS的中间件限制最大并发为512，请求头最大为8KB，请求头关键字最多为200，请求体最大为50MB，请求频率限制每分钟60次，请求超时上限为2500秒。实际限制还需参考网关流控配置，例如[Nginx网关](security_hardening.md#nginx网关)。


## 获取可用模型<a name="ZH-CN_TOPIC_0000002463409962"></a>

**接口描述<a name="section1770392514160"></a>**

列出当前可用的模型。

**请求方式<a name="section71891846141619"></a>**

```
GET
```

**请求路径<a name="section1711832721718"></a>**

```
/openai/v1/models
```

**请求示例<a name="section666474715174"></a>**

```
GET /openai/v1/models 
```

**响应示例<a name="section10256183821716"></a>**

```
{  
    "object": "list",  
    "data": [
    {
      "id": "Qwen3-8B",
      "object": "model",
      "created": 1741596839,
      "owned_by": "vllm",
      "max_model_len": 8192
    }
  ]
}
```


## 聊天补全<a name="ZH-CN_TOPIC_0000002463250294"></a>

### 文本模态<a name="ZH-CN_TOPIC_0000002463250262"></a>

**接口描述<a name="section114050180208"></a>**

该接口用于通过API调用OpenAI的聊天功能，生成与用户输入相关的回复。

|接口名称|功能描述|请求方式|URL示例|
|--|--|--|--|
|Chat Completion|根据给定的对话消息和模型，生成一个或多个聊天回复，支持多种参数控制生成过程，支持流式响应等。|POST|http://127.0.0.1:8000/openai/v1/chat/completions|


**请求方式<a name="section71891846141619"></a>**

```
POST
```

**请求路径<a name="section1711832721718"></a>**

```
/openai/v1/chat/completions
```

**请求示例<a name="section666474715174"></a>**

```
POST /openai/v1/chat/completions 
Host: api.openai.com 
Content-Type: application/json 
{
 "model": "Qwen3-8B",
 "messages": [{
     "role": "user",
     "content": "Who won the world series in 2020?"
     }],
 "max_tokens": 100,
 "temperature": 0.6,
 "top_p":0.6,
 "stream": false 
} 
```

**表 1**  参数说明

|参数名称|类型|是否必选|描述|取值范围|
|--|--|--|--|--|
|messages|list|必选|以消息对象组成的列表，表示对话上下文。每条消息必须包含role和content，其中role可以是system、assistant、user。|数组，其中元素为消息对象，参见[表 消息参数](#table2)|
|model|str|可选|模型名称。|取值范围：[Qwen3-8B]|
|frequency_penalty|float|可选|频率惩罚。对高频token施加与出现次数成正比的惩罚，作用于整个生成文本，按token频率调整惩罚强度。|默认值为0.0，取值范围：[-2.0, 2.0]|
|max_tokens|int|可选|允许生成的最大token个数。实际值受配置限制（注：最大值为[表3 引擎详细配置](parameter_configuration.md#模型最优配置)中max_model_len与输入token数的差值）。 <br>说明：max_tokens已被弃用，建议使用max_completion_tokens字段。|取值范围：[1, 64000]|
|min_tokens|int|可选|每个输出序列所需的最小生成令牌数。实际值受配置限制（注：最大值为[表3 引擎详细配置](parameter_configuration.md#模型最优配置)中max_model_len与输入token数的差值）。|默认值为0，取值范围：[0, 64000]|
|max_completion_tokens|int|可选|允许生成的最大token个数。实际值受配置限制（注：最大值为[表3 引擎详细配置](parameter_configuration.md#模型最优配置)中max_model_len与输入token数的差值）。|取值范围：[1, 64000]|
|presence_penalty|float|可选|存在惩罚，对已出现过的token施加固定惩罚，作用于所有已出现的token，不区分频率。|默认值为0.0，取值范围：[-2.0, 2.0]|
|seed|int|可选|随机种子，用于生成确定性输出。|取值范围：[-65535, 65535]|
|stream|bool|可选|是否流式返回部分进度。|默认值为false，取值范围：true、false|
|temperature|float|可选|采样温度，值越高输出越随机。|取值范围：[0, 2]|
|top_p|float|可选|核采样，仅考虑概率质量在top_p内的token。|取值范围：[1e-8, 1]|


**表 2**  消息参数<a id="table2"></a>

|字段|类型|描述|
|--|--|--|
|role|str|消息角色（system，user，assistant）|
|content|str|消息文本内容|


**响应示例<a name="section10256183821716"></a>**

```
{
  "id": "chatcmpl-f390ba5fb0ae4b5bb585c9f6d9875602",
  "object": "chat.completion",
  "created": 1741596881,
  "model": "Qwen3-8B",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "reasoning_content": null,
        "content": "Okay, so I need to figure out who won the World Series in 2020. I'm not super familiar with baseball, but I know the World Series is a big deal in the United States. It's the championship series of Major League Baseball, right? The winner is the team that wins four games, and it's usually a big deal because it determines which team gets to represent the country in things like the World Series of Baseball or other international events.\n\nFirst, I should probably",
        "tool_calls": []
      },
      "logprobs": null,
      "finish_reason": "length"
    }
  ],
  "usage": {
    "prompt_tokens": 17,
    "total_tokens": 117,
    "completion_tokens": 100,
    "prompt_tokens_details": null
  },
  "prompt_logprobs": null,
  "kv_transfer_params":null 
}
```



