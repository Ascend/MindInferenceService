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
)

const (
	// MISModelFinalizer indicates if mismodel can be deleted
	MISModelFinalizer = "finalizer.mismodel.apps.ascend.com"
	// MISModelPodContainerName indicates container name of download pod
	MISModelPodContainerName = "downloader"
	// MISModelPodVolumeName indicates volume name of used pvc
	MISModelPodVolumeName = "model-path"
	// MISModelPodMountPath indicate cache path in MIS images
	MISModelPodMountPath = "/opt/mis/.cache"
	// MISModelPodCmd indicate command of download pod
	MISModelPodCmd = "mis_download"
	// MISModelLabelPartOf indicate label set to app.kubernetes.io/part-of
	MISModelLabelPartOf = "mis-model"
)
