/*
Copyright 2025 Huawei Technologies Co., Ltd.
*/

package controller

import (
	"github.com/pkg/errors"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/runtime/schema"
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

func getAcjobCompletionTime(acjob *unstructured.Unstructured) (string, error) {
	completionTime, found, err := unstructured.NestedString(acjob.Object, "status", "completionTime")
	if err != nil {
		return "", errors.Wrap(err, "Unable to solve ascendjob.status.completionTime in string")
	}
	if !found {
		return "", nil
	}
	return completionTime, nil
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
