{{/*
Define global host arch.
*/}}
{{- define "mis-llm.global.host-arch" -}}
{{- if eq .Values.global.aiServer "800I A2" -}}
host-arch: huawei-arm
{{- end -}}
{{- end }}

{{/*
Create a default fully qualified job name for llm.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "mis-llm.llm.jobName" -}}
{{- printf "%s-%s" .Chart.Name .Values.llm.modelName | replace "." "p" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified service name for llm.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "mis-llm.llm.serviceName" -}}
{{- printf "%s-%s" .Chart.Name .Values.llm.modelName | replace "." "p" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels for llm.
*/}}
{{- define "mis-llm.llm.labels" -}}
{{- if eq .Values.global.aiServer "800I A2" -}}
ring-controller.atlas: ascend-910b
fault-scheduling: "force"
app: {{ .Values.llm.modelName }}
{{- end -}}
{{- end }}

{{/*
Define accelerator for llm.
*/}}
{{- define "mis-llm.llm.accelerator" -}}
{{- if eq .Values.global.aiServer "800I A2" -}}
huawei.com/Ascend910
{{- end -}}
{{- end }}

{{/*
Define resources for llm.
*/}}
{{- define "mis-llm.llm.resources" -}}
{{- if eq .Values.global.aiServer "800I A2" -}}
{{- $accelerator := "huawei.com/Ascend910" }}
limits:
  {{ $accelerator }}: {{ .Values.llm.acceleratorCards }}
requests:
  {{ $accelerator }}: {{ .Values.llm.acceleratorCards }}
{{- end -}}
{{- end }}

{{/*
Define node selectors for llm.
*/}}
{{- define "mis-llm.llm.nodeSelectors" -}}
{{- if eq .Values.global.aiServer "800I A2" -}}
accelerator-type: module-910b-8
{{ include "mis-llm.global.host-arch" . }}
{{- end -}}
{{- end }}

{{/*
Define OPENAI_API_BASE_URL for frontend.
*/}}
{{- define "mis-llm.frontend.apiURL" -}}
http://{{ include "mis-llm.llm.serviceName" . }}.{{ .Values.global.namespace }}.svc.cluster.local:8000/openai/v1
{{- end }}