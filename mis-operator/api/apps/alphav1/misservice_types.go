/*
Copyright 2025 Huawei Technologies Co., Ltd.
*/

package alphav1

import (
	"k8s.io/apimachinery/pkg/apis/meta/v1"
)

// MISServiceSpec defines the desired state of MISService.
type MISServiceSpec struct {
}

// MISServiceStatus defines the observed state of MISService.
type MISServiceStatus struct {
}

// +kubebuilder:object:root=true
// +kubebuilder:subresource:status

// MISService is the Schema for the misservices API.
type MISService struct {
	v1.TypeMeta   `json:",inline"`
	v1.ObjectMeta `json:"metadata,omitempty"`

	Spec   MISServiceSpec   `json:"spec,omitempty"`
	Status MISServiceStatus `json:"status,omitempty"`
}

// +kubebuilder:object:root=true

// MISServiceList contains a list of MISService.
type MISServiceList struct {
	v1.TypeMeta `json:",inline"`
	v1.ListMeta `json:"metadata,omitempty"`
	Items       []MISService `json:"items"`
}

func init() {
	SchemeBuilder.Register(&MISService{}, &MISServiceList{})
}
