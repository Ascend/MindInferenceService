# 快速入门<a name="ZH-CN_TOPIC_0000002463251810"></a>

**简介<a name="section174721916135213"></a>**

本章节旨在帮助用户快速完成推理微服务MIS的部署与运行。主要介绍如何在Atlas 800I A2 推理服务器上完成环境准备、模型权重配置与服务启动等关键步骤。

推理微服务MIS提供**OpenAI API兼容接口**，可无缝对接现有应用。用户仅需完成环境初始化与模型路径配置，即可通过标准API发起推理请求，实现快速验证与集成。

**环境准备<a name="section470012716523"></a>**

-   准备Atlas A2 推理系列产品的服务器，并安装对应的驱动和固件，具体安装过程请参见[《CANN 软件安装指南》](https://www.hiascend.com/document/detail/zh/canncommercial/850/softwareinst/instg/instg_0000.html?Mode=PmIns&InstallType=netconda&OS=openEuler&Software=cannToolKit)中的“安装NPU驱动和固件”章节（商用版）或[《CANN 软件安装指南》](https://www.hiascend.com/document/detail/zh/CANNCommunityEdition/850/softwareinst/instg/instg_0000.html?Mode=PmIns&InstallType=netconda&OS=openEuler&Software=cannToolKit)中的““安装NPU驱动和固件”章节[（社区版）]。
-   安装CANN Toolkit，具体安装过程请参见[《CANN 软件安装指南》](https://www.hiascend.com/document/detail/zh/canncommercial/850/softwareinst/instg/instg_0000.html?Mode=PmIns&InstallType=netconda&OS=openEuler&Software=cannToolKit)的“安装CANN”章节（商用版）或[《CANN 软件安装指南》](https://www.hiascend.com/document/detail/zh/CANNCommunityEdition/850/softwareinst/instg/instg_0000.html?Mode=PmIns&InstallType=netconda&OS=openEuler&Software=cannToolKit)的“安装CANN”章节（社区版）。
-   安装MIS以及相关依赖，具体安装过程请参见[安装部署](installation_guide.md#安装部署)。

**启动MIS服务<a name="section19292103315523"></a>**

1.  下载模型权重并设置路径

    部署MIS前需将模型权重放置在本地，可选择从开源模型社区\(如魔乐社区、Huggingface\)下载对应权重（safetensors类型权重）。假设模型权重下载路径为/data/Qwen3-8B，则将MIS权重缓存路径的环境变量MIS\_CACHE\_PATH设置为/data。

    ```
    export MIS_CACHE_PATH=/data
    ```

2.  配置CANN运行环境变量

    确保安装环境中已执行CANN环境变量配置脚本，使环境变量生效。具体执行路径，请以实际安装路径为准。

    ```
    source $HOME/Ascend/cann/set_env.sh #此处为示例安装路径，根据实际安装路径修改
    source $HOME/Ascend/nnal/atb/set_env.sh #此处为示例安装路径，根据实际安装路径修改
    ```

3.  指定运行模型

    ```
    export MIS_MODEL=Qwen3-8B
    ```

4.  执行启动命令

    进入MIS软件包安装路径，例如：

    ```
    cd $HOME/Ascend/mis/7.3.0
    ```

    执行如下命令部署MIS

    ```
    ./mis.pyz
    ```

    或通过Python解释器执行部署命令（请根据对应Python环境调整）

    ```
    python3 mis.pyz
    ```

> [!NOTICE] 须知 
>-   请确保模型文件来源可信，文件未被篡改且权重类型为safetensors。
>-   请确保模型权重路径，MIS安装路径及所有文件的属主与运行用户一致。
>-   请确保参数配置文件不为软链接，路径字符串长度不大于1024。
>-   请确保模型权重路径权限为750，权重文件为640。
>-   推理微服务MIS监听至127.0.0.1且MIS需要通过组件集成的方式与其他系统配合才能形成完整的推理服务系统 ，请参考[推理微服务安全加固](security_hardening.md#推理微服务安全加固)。

**发起请求<a name="section57121852205210"></a>**

使用OpenAI API发起对话请求。

```
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

