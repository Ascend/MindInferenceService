FROM ubuntu:22.04 as mis-cann

ARG PYTHON_VER=3.10

WORKDIR /tmp

RUN apt-get update && apt-get -y install ca-certificates && update-ca-certificates && \
    apt-get install -y software-properties-common && add-apt-repository ppa:deadsnakes/ppa && \
    apt-get install -y gcc make net-tools python${PYTHON_VER} python${PYTHON_VER}-dev python${PYTHON_VER}-venv curl wget && \
    ln -sf /usr/bin/python${PYTHON_VER} /usr/bin/python3 && curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python3 get-pip.py && rm -rf *

ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

RUN pip3 install attrs cython numpy==1.24.0 decorator sympy cffi pyyaml pathlib2 psutil protobuf==3.20 scipy requests absl-py

RUN wget -q http://172.17.0.1:3000/Ascend-cann-toolkit_8.0.0_linux-aarch64.run -P cann/ && \
    wget -q http://172.17.0.1:3000/Ascend-cann-kernels-910b_8.0.0_linux-aarch64.run -P cann/ && \
    wget -q http://172.17.0.1:3000/Ascend-cann-nnal_8.0.0_linux-aarch64.run -P cann/ && \
    /bin/bash cann/Ascend-cann-toolkit*.run --install --quiet && \
    /bin/bash cann/Ascend-cann-kernels*.run --install --quiet && \
    /bin/bash -c "source /usr/local/Ascend/ascend-toolkit/set_env.sh; /bin/bash cann/Ascend-cann-nnal*.run --install --quiet" && \
    rm -rf *

ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/Ascend/driver/lib64/common:/usr/local/Ascend/driver/lib64/driver:/usr/local/Ascend/driver/lib64


FROM mis-cann as mis-llm-vllm

ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

RUN apt-get install -y git && mkdir -p /opt/vllm-ascend/
RUN cd /opt/vllm-ascend/ && \
    git clone https://github.com/vllm-project/vllm.git && \
    cd vllm && git checkout 4f4d427 && \
    pip3 install -r requirements-build.txt && VLLM_TARGET_DEVICE=empty pip3 install -e .
RUN cd /opt/vllm-ascend/ && \
    git clone https://github.com/vllm-project/vllm-ascend.git && \
    cd vllm-ascend && git checkout f17417f && \
    pip3 install -e .
RUN cd /opt/vllm-ascend/ && mkdir pta && \
    curl https://pytorch-package.obs.cn-north-4.myhuaweicloud.com/pta/Daily/v2.5.1/20250218.4/pytorch_v2.5.1_py310.tar.gz -o pta.tar.gz && \
    tar -zxvf pta.tar.gz -C pta && \
    pip3 install pta/torch_npu-2.5.1.dev20250218-cp310-cp310-manylinux_2_17_aarch64.*.whl



FROM mis-llm-vllm as mis-llm-run

WORKDIR /opt

ARG MODEL=DeepSeek-R1-Distill-Qwen-7B
ENV MIS_SERVED_MODEL_NAME=${MODEL}

COPY build/mis ./mis/
COPY build/requirements.txt ./
COPY build/run.sh ./

RUN pip3 install -r requirements.txt && chmod +x run.sh
CMD ["/bin/bash", "-c", "./run.sh"]