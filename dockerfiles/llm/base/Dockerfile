ARG BASE_IMAGE=mis-cann:0.1
FROM ${BASE_IMAGE}

WORKDIR /opt

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
RUN pip3 install transformers==4.45.0 # mindie needed