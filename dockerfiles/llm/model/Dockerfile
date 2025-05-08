ARG BASE_IMAGE=mis-llm-base:0.1
FROM ${BASE_IMAGE}

WORKDIR /opt/mis

ARG MODEL=DeepSeek-R1-Distill-Qwen-7B
ENV MIS_MODEL=${MODEL}
ENV MIS_SERVED_MODEL_NAME=${MODEL}

COPY build/mis*.whl ./
COPY build/configs ./configs/
COPY build/patch ./patch/

RUN pip3 install mis*.whl
RUN chmod +x patch/patch.sh && ./patch/patch.sh

CMD ["mis_run"]