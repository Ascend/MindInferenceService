ARG BASE_IMAGE=mis-llm-base:0.1
FROM ${BASE_IMAGE}

WORKDIR /opt/mis

ARG MODEL=DeepSeek-R1-Distill-Qwen-7B
ENV MIS_SERVED_MODEL_NAME=${MODEL}

COPY build/mis ./mis/
COPY build/setup.py ./

RUN chmod +x /opt/mis/mis/patch/patch.sh && \
    /opt/mis/mis/patch/patch.sh

RUN pip3 install -e .
CMD ["/usr/bin/python3", "mis/run.py"]