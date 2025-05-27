/*
Copyright 2025 Huawei Technologies Co., Ltd.
*/

package alphav1

import (
	"fmt"

	"k8s.io/api/autoscaling/v2beta2"
	"k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// MISServiceSpec defines the desired state of MISService.
type MISServiceSpec struct {
	// MISModel name of used MISModel
	MISModel string `json:"misModel,omitempty"`
	// +kubebuilder:validation:Minimum=1
	// +kubebuilder:default:=1
	Replicas int `json:"replicas,omitempty"`
	// +optional
	HPA         *HPA                     `json:"hpa,omitempty"`
	ServiceSpec MISSvcSpec               `json:"serviceSpec,omitempty"`
	Resources   *v1.ResourceRequirements `json:"resources,omitempty"`
	// +optional
	StartupProbe *v1.Probe `json:"startupProbe,omitempty"`
	// +optional
	ReadinessProbe *v1.Probe `json:"readinessProbe,omitempty"`
	// +optional
	LivenessProbe *v1.Probe `json:"livenessProbe,omitempty"`
	// +optional
	// +kubebuilder:validation:Minimum=0
	// +kubebuilder:validation:Maximum=65535
	UserID *int64 `json:"userID,omitempty"`
	// +optional
	// +kubebuilder:validation:Minimum=0
	// +kubebuilder:validation:Maximum=65535
	GroupID *int64 `json:"groupID,omitempty"`
}

// HPA is used to scale up or scale down replicas while load variation
type HPA struct {
	// +kubebuilder:validation:Minimum=1
	MinReplicas int32 `json:"minReplicas,omitempty"`
	// +kubebuilder:validation:Minimum=1
	MaxReplicas int32 `json:"maxReplicas,omitempty"`

	Metrics *[]Metric `json:"metrics,omitempty"`
	// +optional
	Behavior *v2beta2.HorizontalPodAutoscalerBehavior `json:"behavior,omitempty"`
}

// Metric indicates metrics used to control replicas of MIS service instance
type Metric struct {
	Type      MetricsType `json:"type,omitempty"`
	Threshold string      `json:"threshold,omitempty"`
}

// MISSvcSpec defines how to create service for MIS inference server
type MISSvcSpec struct {
	Type v1.ServiceType `json:"type,omitempty"`
	Name string         `json:"name,omitempty"`
	// +kubebuilder:validation:Minimum=1
	// +kubebuilder:validation:Maximum=65535
	// +kubebuilder:default:=8000
	Port        int32             `json:"port,omitempty"`
	Annotations map[string]string `json:"annotations,omitempty"`
}

// MISServiceStatus defines the observed state of MISService.
type MISServiceStatus struct {
	State      string             `json:"state,omitempty"`
	Conditions []metav1.Condition `json:"conditions,omitempty" patchStrategy:"merge" patchMergeKey:"type" 
protobuf:"bytes,1,rep,name=conditions"`
	Replicas        int         `json:"replicas,omitempty"`
	Selector        string      `json:"selector,omitempty"`
	Model           string      `json:"model,omitempty"`
	PVC             string      `json:"pvc,omitempty"`
	Envs            []v1.EnvVar `json:"envs,omitempty"`
	Image           string      `json:"image,omitempty"`
	ImagePullSecret *string     `json:"imagePullSecret,omitempty"`
	Running         string      `json:"running,omitempty"`
}

// +kubebuilder:object:root=true
// +kubebuilder:subresource:status
// +kubebuilder:subresource:scale:specpath=.spec.replicas,statuspath=.status.replicas,selectorpath=.status.selector
// +kubebuilder:printcolumn:name="State",type=string,JSONPath=`.status.state`,priority=0
// +kubebuilder:printcolumn:name="CurrentReplicas",type=string,JSONPath=`.status.replicas`,priority=0
// +kubebuilder:printcolumn:name="Running",type=string,JSONPath=`.status.running`,priority=0

// MISService is the Schema for the misservices API.
type MISService struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   MISServiceSpec   `json:"spec,omitempty"`
	Status MISServiceStatus `json:"status,omitempty"`
}

// GetServiceMonitorName get service monitor name of MISService
func (in *MISService) GetServiceMonitorName() string {
	return fmt.Sprintf("%s-service-monitor", in.Name)
}

// GetHPAName get HPA name of MISService
func (in *MISService) GetHPAName() string {
	return fmt.Sprintf("%s-horizontal-pod-autoscaling", in.Name)
}

// +kubebuilder:object:root=true

// MISServiceList contains a list of MISService.
type MISServiceList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []MISService `json:"items"`
}

func init() {
	SchemeBuilder.Register(&MISService{}, &MISServiceList{})
}
