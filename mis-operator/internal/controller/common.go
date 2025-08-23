/*
Copyright 2025 Huawei Technologies Co., Ltd.
*/

// Package controller contains all controller of mis-operator
package controller

const (
	// MISLabelKeyName indicate label key set to sub resource
	MISLabelKeyName = "app.kubernetes.io/name"
	// MISLabelKeyInstance indicate label key set to sub resource
	MISLabelKeyInstance = "app.kubernetes.io/instance"
	// MISLabelKeyPartOf indicate label key set to sub resource
	MISLabelKeyPartOf = "app.kubernetes.io/part-of"
	// MISLabelKeyManagedBy indicate label key set to sub resource
	MISLabelKeyManagedBy = "app.kubernetes.io/managed-by"

	// MISLabelManagedBy indicate label set to app.kubernetes.io/managed-by
	MISLabelManagedBy = "mis-operator"

	// MISEnvironmentTlsCert indicate environment key to set tls cert for MIS
	MISEnvironmentTlsCert = "MIS_SSL_CERTFILE"
	// MISEnvironmentTlsKey indicate environment key to set tls key for MIS
	MISEnvironmentTlsKey = "MIS_SSL_KEYFILE"
)

const (
	// MISModelFinalizer indicates if mismodel can be deleted
	MISModelFinalizer = "finalizer.mismodel.apps.ascend.com"

	// MISModelPodContainerName indicates container name of download pod
	MISModelPodContainerName = "downloader"

	// MISModelPodVolumeName indicates volume name of used pvc
	MISModelPodVolumeName = "model-path"
	// MISModelPodMountPath indicate cache path in MIS images
	MISModelPodMountPath = "/opt/mis-management/"

	// MISModelPodCmd indicate command of download pod
	MISModelPodCmd = "mis_download"

	// MISModelLabelPartOf indicate label set to app.kubernetes.io/part-of
	MISModelLabelPartOf = "mis-model"
)

const (
	// MISServiceFinalizer indicates if misservice can be deleted
	MISServiceFinalizer = "finalizer.misservice.apps.ascend.com"

	// MISServicePortName indicates mis service‘s port name
	MISServicePortName = "service-port"
	// MISServiceMetricsPortName indicates mis service‘s metrics port name
	MISServiceMetricsPortName = "service-metrics-port"

	// MISServiceTLSPath indicates mount path of TLSSecret in pod
	MISServiceTLSPath = "/etc/mis/tls/"
	// MISServiceTLSCert indicates tls cert name
	MISServiceTLSCert = "tls.crt"
	// MISServiceTLSKey indicates tls key name
	MISServiceTLSKey = "tls.key"

	// MISServiceVolumeModel indicates volume for model weight
	MISServiceVolumeModel = "model"
	// MISServiceVolumeTmpfs indicates volume for tmpfs
	MISServiceVolumeTmpfs = "dshm"
	// MISServiceVolumeTime indicates volume for time zone
	MISServiceVolumeTime = "localtime"
	// MISServiceVolumeTls indicates volume for tls
	MISServiceVolumeTls = "tls"

	// MISServiceVolumeTmpfsPath indicates path for tmpfs
	MISServiceVolumeTmpfsPath = "/dev/shm"
	// MISServiceVolumeTimePath indicates path for time zone
	MISServiceVolumeTimePath = "/etc/localtime"

	// MISServiceAcjobNameSuffixLen indicates acjob‘s random suffix length
	MISServiceAcjobNameSuffixLen = 8
	// MISServiceAcjobMaster indicates acjob‘s master replicas name
	MISServiceAcjobMaster = "Master"
	// MISServiceAcjobWorker indicates acjob‘s worker replicas name
	MISServiceAcjobWorker = "Worker"
	// MISServiceAcjobPortName indicates acjob‘s port name
	MISServiceAcjobPortName = "ascendjob-port"
	// MISServiceAcjobContainerName indicates acjob‘s container name
	MISServiceAcjobContainerName = "ascend"
	// MISServiceAcjobDeleteLastTime indicates how long will acjob be deleted after completion
	MISServiceAcjobDeleteLastTime = 5 * 60
	// MISServiceAcjobMetricsUrl indicates how to query metrics
	MISServiceAcjobMetricsUrl = "/v1/metrics"

	// MISServiceAcjobSchedulerName indicate use what to scheduler acjob
	MISServiceAcjobSchedulerName = "volcano"
	// MISServiceAcjobSuccessPolicy indicate acjob success policy
	MISServiceAcjobSuccessPolicy = "AllWorkers"

	// MISServicePodGracePeriodSeconds indicates pod survival time before killed by k8s
	MISServicePodGracePeriodSeconds = 5 * 60

	// MISServiceLabelPartOf indicate label set to app.kubernetes.io/part-of
	MISServiceLabelPartOf = "mis-service"
)
