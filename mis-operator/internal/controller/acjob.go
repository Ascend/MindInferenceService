/*
Copyright 2025 Huawei Technologies Co., Ltd.
*/

package controller

import (
	"time"

	"github.com/pkg/errors"
	"k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/runtime/schema"

	"ascend.com/mis-operator/api/apps/alphav1"
)

// ReplicaStatus indicates acjob status seperated by Master or Worker
type ReplicaStatus struct {
	Active    int32 `json:"active,omitempty"`
	Failed    int32 `json:"failed,omitempty"`
	Succeeded int32 `json:"succeeded,omitempty"`
}

func getAcjobGVK() schema.GroupVersionKind {
	return schema.GroupVersionKind{
		Group:   "mindxdl.gitee.com",
		Version: "v1",
		Kind:    "AscendJob",
	}
}

func getAcjobObject() unstructured.Unstructured {
	acjob := unstructured.Unstructured{}
	acjob.SetGroupVersionKind(getAcjobGVK())
	return acjob
}

func getAcjobListObject() unstructured.UnstructuredList {
	acjobList := unstructured.UnstructuredList{}
	acjobList.SetGroupVersionKind(getAcjobGVK())
	return acjobList
}

func constructAcjobLabelsFromServerInfo(serverType alphav1.ServerType) map[string]string {
	switch serverType {
	case alphav1.ServerTypeAtlas800IA2:
		return map[string]string{
			"framework":             "pytorch",
			"ring-controller.atlas": "ascend-910b",
		}
	default:
		return map[string]string{}
	}
}

func constructAcjobSelectorLabelsFromServerInfo(serverType alphav1.ServerType) map[string]string {
	switch serverType {
	case alphav1.ServerTypeAtlas800IA2:
		return map[string]string{
			"ring-controller.atlas": "ascend-910b",
		}
	default:
		return map[string]string{}
	}
}

func constructAcjobNodeSelectorFromServerInfo(serverType alphav1.ServerType) map[string]string {
	switch serverType {
	case alphav1.ServerTypeAtlas800IA2:
		return map[string]string{
			"host-arch":        "huawei-arm",
			"accelerator-type": "module-910b-8",
		}
	default:
		return map[string]string{}
	}
}

func constructAcjobResourceFromServerInfo(cardNum resource.Quantity) v1.ResourceRequirements {

	return v1.ResourceRequirements{
		Requests: map[v1.ResourceName]resource.Quantity{
			"huawei.com/Ascend910": cardNum,
		},
		Limits: map[v1.ResourceName]resource.Quantity{
			"huawei.com/Ascend910": cardNum,
		},
	}

}

func getAcjobCompletionTime(acjob *unstructured.Unstructured) (metav1.Time, error) {
	completionTimeStr, found, err := unstructured.NestedString(acjob.Object, "status", "completionTime")
	if err != nil {
		return metav1.Time{}, errors.Wrap(err, "Unable to solve ascendjob.status.completionTime in string")
	}
	if !found {
		return metav1.Time{}, nil
	}
	completionTime, err := time.Parse(time.RFC3339, completionTimeStr)
	if err != nil {
		return metav1.Time{}, errors.Wrap(err, "Unable to transform ascendjob.status.completionTime to v1.Time")
	}
	return metav1.NewTime(completionTime), nil
}

func getAcjobReplicaStatuses(acjob *unstructured.Unstructured) (map[string]ReplicaStatus, error) {
	replicaStatusesData, found, err := unstructured.NestedMap(acjob.Object, "status", "replicaStatuses")
	if err != nil {
		return nil, errors.Wrap(err, "Unable to process ascendjob.status.replicaStatuses in type map")
	}
	if !found {
		return nil, errors.Wrap(err, "Unable to find field ascendjob.status.replicaStatuses")
	}

	replicaStatuses := map[string]ReplicaStatus{}
	if err := runtime.DefaultUnstructuredConverter.FromUnstructured(replicaStatusesData, &replicaStatuses); err != nil {
		return nil, errors.Wrap(err, "Unable to convert ascendjob.status.replicaStatuses")
	}

	return replicaStatuses, nil
}
