/*
Copyright 2025 Huawei Technologies Co., Ltd.
*/

package alphav1

import "k8s.io/apimachinery/pkg/api/resource"

// MISServerInfo indicate target server information
type MISServerInfo struct {
	ServerType ServerType        `json:"serverType,omitempty"`
	CardNum    resource.Quantity `json:"cardNum,omitempty"`
	CardMemory string            `json:"cardMemory,omitempty"`
}
