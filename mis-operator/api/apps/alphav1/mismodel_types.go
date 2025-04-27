/*
Copyright 2025 Huawei Technologies Co., Ltd.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
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
