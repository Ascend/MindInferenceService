FROM ubuntu:22.04

ARG PYTHON_VER=3.10

WORKDIR /tmp

ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

RUN apt-get update && apt-get -y install ca-certificates && update-ca-certificates && \
    apt-get install -y software-properties-common && add-apt-repository ppa:deadsnakes/ppa && \
    apt-get install -y gcc make net-tools python${PYTHON_VER} python${PYTHON_VER}-dev python${PYTHON_VER}-venv curl wget && \
    ln -sf /usr/bin/python${PYTHON_VER} /usr/bin/python3 && curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python3 get-pip.py && rm -rf *

RUN pip3 install attrs cython numpy==1.24.0 decorator sympy cffi pyyaml pathlib2 psutil protobuf==3.20 scipy requests absl-py

RUN wget -q http://172.17.0.1:3000/Ascend-cann-toolkit_8.0.0_linux-aarch64.run -P cann/ && \
    wget -q http://172.17.0.1:3000/Ascend-cann-kernels-910b_8.0.0_linux-aarch64.run -P cann/ && \
    wget -q http://172.17.0.1:3000/Ascend-cann-nnal_8.0.0_linux-aarch64.run -P cann/ && \
    wget -q http://172.17.0.1:3000/Ascend-mindie_1.0.0_linux-aarch64.run -P cann/ && \
    wget -q http://172.17.0.1:3000/Ascend-mindie-atb-models_1.0.0_linux-aarch64_py310_torch2.3.1-abi0.tar.gz -P cann/ && \
    /bin/bash cann/Ascend-cann-toolkit*.run --install --quiet && \
    /bin/bash cann/Ascend-cann-kernels*.run --install --quiet && \
    /bin/bash -c "source /usr/local/Ascend/ascend-toolkit/set_env.sh; /bin/bash cann/Ascend-cann-nnal*.run --install --quiet" && \
    /bin/bash -c "source /usr/local/Ascend/ascend-toolkit/set_env.sh; /bin/bash cann/Ascend-mindie_*.run --install --quiet" && \
    /bin/bash -c "mkdir -p /usr/local/Ascend/atb; tar -zxvf cann/Ascend-mindie-atb-models*.tar.gz -C /usr/local/Ascend/atb/" && \
    rm -rf *

ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/Ascend/driver/lib64/common:/usr/local/Ascend/driver/lib64/driver:/usr/local/Ascend/driver/lib64
