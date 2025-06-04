/*
Copyright 2025 Huawei Technologies Co., Ltd.
*/

package alphav1

import (
	"fmt"

	"k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// MISModelSpec defines the desired state of MISModel.
type MISModelSpec struct {
	Storage MISModelStorage `json:"storage,omitempty"`
	// +optional
	ImagePullSecret *string     `json:"imagePullSecret,omitempty"`
	Image           string      `json:"image,omitempty"`
	Envs            []v1.EnvVar `json:"envs,omitempty"`
}

// MISModelStorage defines storage MISModel will use
type MISModelStorage struct {
	PVC MISPVC `json:"pvc,omitempty"`
}

// MISPVC define pvc MISModel will use, created by storageClass or existed one
type MISPVC struct {
	Name             string                        `json:"name,omitempty"`
	StorageClass     string                        `json:"storageClass,omitempty"`
	Size             string                        `json:"size,omitempty"`
	VolumeAccessMode v1.PersistentVolumeAccessMode `json:"volumeAccessMode,omitempty"`
	SubPath          string                        `json:"subPath,omitempty"`
}

// MISModelStatus defines the observed state of MISModel.
type MISModelStatus struct {
	State      string             `json:"state,omitempty"`
	Conditions []metav1.Condition `json:"conditions,omitempty" patchStrategy:"merge" patchMergeKey:"type" 
protobuf:"bytes,1,rep,name=conditions"`
	Model         string        `json:"model,omitempty"`
	PVC           string        `json:"pvc,omitempty"`
	MISServerInfo MISServerInfo `json:"serverInfo,omitempty"`
}

// +kubebuilder:object:root=true
// +kubebuilder:subresource:status
// +kubebuilder:printcolumn:name="State",type=string,JSONPath=`.status.state`,priority=0
// +kubebuilder:printcolumn:name="Model",type=string,JSONPath=`.status.model`,priority=0
// +kubebuilder:printcolumn:name="PVC",type=string,JSONPath=`.status.pvc`,priority=0

// MISModel is the Schema for the mismodels API.
type MISModel struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   MISModelSpec   `json:"spec,omitempty"`
	Status MISModelStatus `json:"status,omitempty"`
}

// GetPVCName return pvc name given by user
func (in *MISModel) GetPVCName() string {
	return in.Spec.Storage.PVC.Name
}

// GetPVCSize return pvc size given by user, default 100Gi
func (in *MISModel) GetPVCSize() resource.Quantity {
	if q, err := resource.ParseQuantity(in.Spec.Storage.PVC.Size); err != nil {
		return resource.MustParse("100Gi")
	} else {
		return q
	}
}

// GetPVCStorageClass return storageClassName for make pvc
func (in *MISModel) GetPVCStorageClass() *string {
	return &in.Spec.Storage.PVC.StorageClass
}

// GetDownloadPodName return job name for caching model
func (in *MISModel) GetDownloadPodName() string {
	return fmt.Sprintf("%s-download-pod", in.Name)
}

// +kubebuilder:object:root=true

// MISModelList contains a list of MISModel.
type MISModelList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []MISModel `json:"items"`
}

func init() {
	SchemeBuilder.Register(&MISModel{}, &MISModelList{})
}
