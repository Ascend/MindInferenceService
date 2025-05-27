/*
Copyright 2025 Huawei Technologies Co., Ltd.
*/

package alphav1

const (
	// MISModelStateStarted indicates MISModel first create
	MISModelStateStarted = "Started"
	// MISModelStateSecretOK indicates secret is provided
	MISModelStateSecretOK = "SecretOK"
	// MISModelStatePVCReady indicates pvc is in ready
	MISModelStatePVCReady = "PVCReady"
	// MISModelStatePodCreate indicates download pod is created
	MISModelStatePodCreate = "PodCreate"
	// MISModelStateInProgress indicates download pod is running
	MISModelStateInProgress = "InProgress"
	// MISModelStateFailed indicates download pod failed
	MISModelStateFailed = "Failed"
	// MISModelStateReady indicates download pod succeeded
	MISModelStateReady = "Ready"

	// MISModelConditionSecretExist indicates if secret exist
	MISModelConditionSecretExist = "MIS_MODEL_SECRET_EXIST"
	// MISModelConditionPVCReady indicates if pvc is ready
	MISModelConditionPVCReady = "MIS_MODEL_PVC_READY"
	// MISModelConditionPodCreate indicates if download pod is created
	MISModelConditionPodCreate = "MIS_MODEL_POD_CREATE"
	// MISModelConditionPodRunning indicates if download pod is running
	MISModelConditionPodRunning = "MIS_MODEL_POD_RUNNING"
	// MISModelConditionPodComplete indicate if download pod is complete or failed
	MISModelConditionPodComplete = "MIS_MODEL_POD_COMPLETE"
)

const (
	// MISServiceStateStarted indicates MISService first create
	MISServiceStateStarted = "Stared"
	// MISServiceStateModelReady indicates related MISModel is ok
	MISServiceStateModelReady = "ModelReady"
	// MISServiceStateServiceCreated indicates related service is created
	MISServiceStateServiceCreated = "ServiceCreated"
	// MISServiceStateServiceMonitorCreated indicates related service monitor is created
	MISServiceStateServiceMonitorCreated = "ServiceMonitorCreated"
	// MISServiceStateHPACreated indicates related service monitor is created
	MISServiceStateHPACreated = "HPACreated"
	// MISServiceStateWaiting indicates can't provide inference
	MISServiceStateWaiting = "Waiting"
	// MISServiceStateReady indicates inference is running
	MISServiceStateReady = "Ready"
	// MISServiceStateFailed indicates err occurred and can't provide service
	MISServiceStateFailed = "Failed"

	// MISServiceConditionModelReady indicates if MISModel is in ready
	MISServiceConditionModelReady = "MIS_SVC_MODEL_READY"
	// MISServiceConditionServiceCreated indicates if service is created
	MISServiceConditionServiceCreated = "MIS_SVC_SERVICE_CREATED"
	// MISServiceConditionServiceMonitorCreated indicates if service monitor is created
	MISServiceConditionServiceMonitorCreated = "MIS_SVC_SERVICE_MONITOR_CREATED"
	// MISServiceConditionHPACreated indicates if hpa is created
	MISServiceConditionHPACreated = "MIS_SVC_HPA_CREATED"
	// MISServiceConditionAcjobReconciling indicates at least one acjob is not in active
	MISServiceConditionAcjobReconciling = "MIS_SVC_ACJOB_RECONCILING"
	// MISServiceConditionAcjobReady indicate at least one acjob is running
	MISServiceConditionAcjobReady = "MIS_SVC_ACJOB_READY"
	// MISServiceConditionAcjobFailed indicate at least one acjob is failed
	MISServiceConditionAcjobFailed = "MIS_SVC_ACJOB_FAILED"
)

// MetricsType indicates available metric type
type MetricsType string

const (
	// MetricsTypeRequestRate indicates request rate within one second
	MetricsTypeRequestRate MetricsType = "RequestRate"
	// MetricsTypeWaitRequest indicates request in waiting
	MetricsTypeWaitRequest MetricsType = "WaitRequest"
	// MetricsTypeCpuKVCacheUtilization indicates cpu kv cache utilization
	MetricsTypeCpuKVCacheUtilization MetricsType = "CpuKVCacheUtilization"
	// MetricsTypeAccKVCacheUtilization indicates Accelerator kv cache utilization
	MetricsTypeAccKVCacheUtilization MetricsType = "AcceleratorKVCacheUtilization"
)
