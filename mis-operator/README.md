# mis-operator

mis-operator用来提供MIS推理微服务的模型管理、微服务部署、弹性扩缩容能力

## 描述

模型管理，使用mis-operator通过MISModel资源管理和下载模型

微服务部署，使用MISService资源在集群中启动多个MIS微服务

弹性扩缩容，结合HPA可以让MIS微服务根据负载情况动态调整实例

## 开始

### 前提

- go version v1.20.0+
- docker version 17.03+.
- kubectl version v1.11.3+.
- Access to a Kubernetes v1.11.3+ cluster.

### 如何部署

**下载工具:**

```shell
GOBIN=/usr/local/bin go install sigs.k8s.io/kustomize/kustomize/v5@v5.3
GOBIN=/usr/local/bin go install sigs.k8s.io/controller-tools/cmd/controller-gen@v0.13.0
```

**生成crd和role.yaml:**

```shell
controller-gen rbac:roleName=manager-role crd paths="./api/..." paths="./internal/..." output:crd:artifacts:config=config/crd/bases
```

**生成zz_generated.deepcopy.go:**

```shell
controller-gen object:headerFile="hack/boilerplate.go.txt" paths="./api/..."
```

**测试运行:**

```shell
go test $(go list ./internal/...) -coverprofile=cover.out
```

**手动编译二进制(测试):**

```shell
CGO_ENABLED=0 GOOS=linux go build -a -o mis-operator-manager cmd/main.go
```

**构建镜像:**

```shell
docker build -t image:tag
```

**部署:**

```shell
cd config/manager/
kustomize edit set image controller=image:tag
cd ../../
kustomize build config/default | kubectl apply -f -
```

**解除部署:**

```shell
kustomize build config/default | kubectl delete --ignore-not-found=true -f -
```

## 版权

Copyright 2025 Huawei Technologies Co., Ltd.


