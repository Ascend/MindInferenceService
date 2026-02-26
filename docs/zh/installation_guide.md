# 安装部署<a name="ZH-CN_TOPIC_0000002463411430"></a>

## 获取软件包<a name="ZH-CN_TOPIC_0000002463252390"></a>

请参考本章获取所需软件包和对应的数字签名文件。

|组件名称|软件包名称|获取方式|
|--|--|--|
|Mind Inference Service（MIS）|Ascend-mis_*{version}*_linux-*{arch}*.run|待发布|


>[!NOTE] 说明
>{version\}为软件包的版本号。
>{arch\}为CPU架构。

**软件数字签名验证<a name="section122616813321"></a>**

为了防止软件包在传递过程中或存储期间被恶意篡改，下载软件包时请下载对应的数字签名文件用于完整性验证。

在软件包下载之后，请参考《OpenPGP签名验证指南》，对下载的软件包进行PGP数字签名校验。如果校验失败，请勿使用该软件包并联系华为技术支持工程师解决。

使用软件包安装/升级前，也需要按照上述过程，验证软件包的数字签名，确保软件包未被篡改。

运营商客户请访问：[https://support.huawei.com/carrier/digitalSignatureAction](https://support.huawei.com/carrier/digitalSignatureAction)

企业客户请访问：[https://support.huawei.com/enterprise/zh/tool/software-digital-signature-openpgp-validation-tool-TL1000000054](https://support.huawei.com/enterprise/zh/tool/software-digital-signature-openpgp-validation-tool-TL1000000054)

**注意事项<a name="section11874161518517"></a>**

如需安装MIS软件包以外的第三方软件，请注意及时升级到最新版本，关注并修补其存在的漏洞。


## 安装依赖<a name="ZH-CN_TOPIC_0000002496451473"></a>

### 安装Ubuntu系统依赖<a name="ZH-CN_TOPIC_0000002496571413"></a>

Ubuntu系统环境中所需依赖名称、对应版本及获取建议请参见[表1](#table1252213214253)。

**表 1** Ubuntu系统依赖名称对应版本<a id="table1252213214253"></a>

|依赖名称|版本建议|获取建议|
|--|--|--|
|Python|3.10或3.11|请从[Python](https://www.python.org/)官网获取源码包并进行编译安装。|
|CMake|3.14及以上|建议通过包管理安装，安装命令参考如下。sudo apt-get install -y cmake若包管理中的版本不符合最低版本要求，可自行通过源码方式安装。|
|Make|4.1及以上|建议通过包管理安装，安装命令参考如下。sudo apt-get install -y make若包管理中的版本不符合最低版本要求，可自行通过源码方式安装。|
|GCC|9.4及以上|建议通过包管理安装，安装命令参考如下。sudo apt-get install -y gcc若包管理中的版本不符合最低版本要求，可自行通过源码方式安装。|


使用如下命令查询GCC、Make、CMake及Python等依赖软件包的版本信息，确认依赖软件是否已安装。

```
gcc --version 
make --version 
cmake --version 
python3 --version
```

若返回如下信息，则说明相应软件已安装（以下回显仅为示例，请以实际情况为准）。

```
gcc (Ubuntu 13.3.0-6ubuntu2~24.04) 13.3.0 
GNU Make 4.3 
cmake version 4.0.3 
Python 3.11.13
```


### 安装NPU驱动固件和CANN<a name="ZH-CN_TOPIC_0000002463252394"></a>

**下载依赖软件包<a name="section152612378439"></a>**


**表 1**  软件包清单

|软件类型|软件包名称|获取方式|
|--|--|--|
|昇腾NPU驱动|Ascend-hdk-*{chip_type}*-npu-driver_*{version}*_linux-*{arch}*.run|固件与驱动：[获取链接](https://www.hiascend.com/hardware/firmware-drivers/commercial?product=1&model=30&cann=8.3.RC1.alpha003&driver=Ascend+HDK+25.2.0)|
|昇腾NPU固件|Ascend-hdk-*{chip_type}*-npu-firmware_*{version}*.run|固件与驱动：[获取链接](https://www.hiascend.com/hardware/firmware-drivers/commercial?product=1&model=30&cann=8.3.RC1.alpha003&driver=Ascend+HDK+25.2.0)|
|CANN开发套件包|Ascend-cann-toolkit_*{version}*_linux-*{arch}*.run|支持在线一键下载和安装，无需获取软件包|
|CANN算子包集成一系列库文件|Ascend-cann-*{chip_type}*-ops_*{version}*_linux-*{arch}*.run|支持在线一键下载和安装，无需获取软件包|
|NNAL软件包|Ascend-cann-nnal_*{version}*_linux-*{arch}*.run|资源下载中心：[获取链接](https://www.hiascend.com/developer/download/commercial?product=4&model=10&os=j0105&networkadapter=SP333&raidcard=9460-8i&solution=4f0929885dcb40a7a12be5704f5ccb15)|


> [!NOTE] 说明
>-   {version\}表示软件版本号。
>-   {arch\}表示CPU架构。
>-   {chip\_type\}表示处理器类型。可在安装昇腾AI处理器的服务器执行**npu-smi info**命令进行查询。
>-   为了让普通用户能够使用驱动，安装npu-driver要添加**--install-for-all**选项

**安装NPU驱动固件和CANN<a name="section105460919442"></a>**

1.  参考《CANN 软件安装指南》中的“安装NPU驱动和固件”章节（商用版）或“安装NPU驱动和固件”章节（社区版）安装NPU驱动固件。
2.  参考《CANN 软件安装指南》的“安装CANN”章节（商用版）或《CANN 软件安装指南》的“安装CANN”章节（社区版）安装CANN。

    > [!NOTE] 说明
    >-   安装CANN（toolkit）、NPU驱动固件和安装MIS的用户需为同一用户，建议为普通用户。
    >-   安装CANN时，为确保MIS正常使用，CANN的相关依赖也需要一并安装。
    >-   运行CANN的过程中，会生成kernel\_meta等文件夹，MIS不具有转储和删除这些文件的功能，用户可参考《CANN 环境变量参考》中的“安装配置相关”\>“落盘文件配置”\>“ASCEND\_WORK\_PATH”章节使用环境变量进行文件统一管理。


### 安装Python软件包依赖<a name="ZH-CN_TOPIC_0000002496571417"></a>

使用MIS相关功能还需安装如下依赖。

**表 1**  依赖名称及建议版本

|依赖名称|版本建议|获取建议|
|--|--|--|
|fastapi|0.121.1|建议通过pip安装，安装命令参考如下。<br>pip3 install fastapi==0.121.1|
|numpy|1.26.4|建议通过pip安装，安装命令参考如下。<br>pip3 install numpy==1.26.4|
|pydantic|2.12.2|建议通过pip安装，安装命令参考如下。<br>pip3 install pydantic==2.12.2|
|PyYAML|6.0.3|建议通过pip安装，安装命令参考如下。<br>pip3 install pyyaml==6.0.3|
|starlette|0.49.1|建议通过pip安装，安装命令参考如下。<br>pip3 install starlette==0.49.1|
|uvloop|0.21.0|建议通过pip安装，安装命令参考如下。<br>pip3 install uvloop==0.21.0|
|vllm|0.11.0rc3|安装详情请参考[vllm-ascend安装指南](https://vllm-ascend.readthedocs.io/zh-cn/latest/installation.html)。|
|vllm-ascend|0.11.0rc0|安装详情请参考[vllm-ascend安装指南](https://vllm-ascend.readthedocs.io/zh-cn/latest/installation.html)。|


> [!NOTE] 说明
>-   若无所需安装vllm-ascend版本的对应文档，在满足vllm-ascend库系统依赖的情况下可参照较低版本的安装指南。
>-   安装vllm-ascend时，如果需要依赖特定版本的torch-npu包，可参考[torch-npu镜像库](https://mirrors.huaweicloud.com/ascend/repos/pypi/torch-npu/)。



## 安装MIS<a name="ZH-CN_TOPIC_0000002463252398"></a>

**安装须知<a name="section10532115594811"></a>**

-   安装和运行MIS的用户，需要满足以下要求：
    -   安装和运行MIS的用户建议为普通用户。
    -   安装和运行MIS的用户需为同一用户。
    -   安装NPU驱动固件，CANN（toolkit），NNAL和安装MIS的用户需为同一用户，建议为普通用户。

-   软件包的安装、卸载等管理面的相关日志会保存至“\~/log/mis/deployment.log”；完整性校验、提取文件、tar命令访问相关的日志会保存至“\~/log/makeself/makeself.log”文件。用户可查看相应文件，完成后续的日志跟踪及审计。

**安装准备<a name="section1818125498"></a>**

确保安装环境中已执行CANN环境变量配置脚本，使环境变量生效。具体执行路径，请按照实际安装为准。

```
source $HOME/Ascend/cann/set_env.sh #此处为示例安装路径，根据实际安装路径修改
source $HOME/Ascend/nnal/atb/set_env.sh #此处为示例安装路径，根据实际安装路径修改
```

**安装步骤<a name="section997712834912"></a>**

1.  进入MIS安装包所在路径，增加对软件包的可执行权限。

    ```
    chmod u+x Ascend-mis_{version}_linux-{arch}.run
    ```

2.  执行如下命令，校验软件包的一致性和完整性。

    ```
    ./Ascend-mis_{version}_linux-{arch}.run --check 
    ```

    如果系统没有shasum或者sha256sum工具则会校验失败，此时需要自行安装shasum或者sha256sum工具。

    若显示如下信息，说明软件包已通过校验。

    ```
    Verifying archive integrity...  100%   SHA256 checksums are OK. All good.    
    ```

3.  安装软件包（安装命令支持--install-path=_<path\>_等参数，具体使用方式请参见[安装软件包参数说明](appendix.md#安装软件包参数说明)）。

    ```
    ./Ascend-mis_{version}_linux-{arch}.run --install
    ```

    如果用户未指定安装路径，软件会默认安装到软件包所在的路径。

4.  安装完成后，若显示如下信息，表示软件安装成功。

    ```
    Successfully installed MIS
    ```

> [!NOTE] 说明
>安装信息文件路径：
>-   普通用户安装：$HOME/Ascend/ascend\_mis\_install.info
>-   root用户安装：/etc/Ascend/ascend\_mis\_install.info


# 卸载<a name="ZH-CN_TOPIC_0000002496570837"></a>

**方法一 软件包卸载<a name="section930793451919"></a>**

用户可以通过以下步骤对已安装的软件包进行卸载。

1.  进入软件包所在路径。
2.  执行以下命令卸载软件包。

    ```
    ./Ascend-mis_{version}_linux-{arch}.run --uninstall
    ```

    > [!NOTE] 说明
    >-   该方式将删除MIS的所有版本以及安装信息。
    >-   MIS的安装目录所属用户必须与当前执行操作的用户相同。

**方法二 脚本卸载<a name="section248625714251"></a>**

用户可以在MIS的安装目录下通过卸载脚本完成卸载。

1.  进入MIS的安装路径。

    ```
    cd <path>/mis/<version>
    ```

    其中_<path\>_为MIS的安装路径，_<version\>_为需要卸载的MIS版本。

2.  执行如下命令，开始卸载。

    ```
    ./uninstall.sh
    ```

    若脚本没有可执行权限，请执行如下命令赋予“uninstall.sh”脚本的可执行权限。

    ```
    chmod u+x uninstall.sh
    ```

    > [!NOTE] 说明
    >-   该方式将删除MIS当前版本的所在目录。若删除MIS的当前版本后，安装目录为空，则会删除对应的安装信息文件，否则安装信息文件将会保留。
    >-   MIS的安装目录所属用户必须与当前执行操作的用户相同。
    >-   使用“uninstall.sh”脚本进行卸载操作仅适用于正常安装途径，且安装后未对安装文件结构进行修改。如需解决安装异常等情况，请删除安装目录下有关MIS的全部文件夹，以及ascend\_mis\_install.info文件（root用户路径：/etc/Ascend/ascend\_mis\_install.info；普通用户路径：$HOME/Ascend/ascend\_mis\_install.info）。


