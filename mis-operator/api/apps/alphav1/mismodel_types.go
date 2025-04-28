/*
Copyright 2025 Huawei Technologies Co., Ltd.
*/

package alphav1

import (
	"k8s.io/apimachinery/pkg/apis/meta/v1"
)

// MISModelSpec defines the desired state of MISModel.
type MISModelSpec struct {
}

// MISModelStatus defines the observed state of MISModel.
type MISModelStatus struct {
}

// +kubebuilder:object:root=true
// +kubebuilder:subresource:status

// MISModel is the Schema for the mismodels API.
type MISModel struct {
	v1.TypeMeta   `json:",inline"`
	v1.ObjectMeta `json:"metadata,omitempty"`

	Spec   MISModelSpec   `json:"spec,omitempty"`
	Status MISModelStatus `json:"status,omitempty"`
}

// +kubebuilder:object:root=true

// MISModelList contains a list of MISModel.
type MISModelList struct {
	v1.TypeMeta `json:",inline"`
	v1.ListMeta `json:"metadata,omitempty"`
	Items       []MISModel `json:"items"`
}

func init() {
	SchemeBuilder.Register(&MISModel{}, &MISModelList{})
}
