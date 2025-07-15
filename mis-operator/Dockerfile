FROM alpine AS builder

COPY mis-operator-manager .
RUN chmod +x mis-operator-manager

FROM ubuntu:22.04

WORKDIR /
COPY --from=builder --chown=1000:1000 mis-operator-manager .
# 用户1000为默认用户，可自行修改
USER 1000:1000

ENTRYPOINT ["/mis-operator-manager"]
