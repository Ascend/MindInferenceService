/*
Copyright 2025 Huawei Technologies Co., Ltd.
*/

// Package utils contains utils of mis-operator
package utils

import (
	"bytes"
	"context"
	"io"
	"regexp"
	"strings"

	"github.com/pkg/errors"
	"k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/resource"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"

	"ascend.com/mis-operator/api/apps/alphav1"
)

const (
	mISServerInfoLen           = 3
	mISServerInfoServerTypeIdx = 1
	mISServerInfoCardNumIdx    = 2
	mISServerInfoCardMemIdx    = 3
)

// GetPodLogs get logs from given container of pod
func GetPodLogs(ctx context.Context, podNamespace string, podName string, containerName string) (string, error) {
	podLogOpts := v1.PodLogOptions{Container: containerName}
	config, err := rest.InClusterConfig()
	if err != nil {
		return "", err
	}
	// create a clientset
	clientset, err := kubernetes.NewForConfig(config)
	if err != nil {
		return "", err
	}
	req := clientset.CoreV1().Pods(podNamespace).GetLogs(podName, &podLogOpts)
	podLogs, err := req.Stream(ctx)
	if err != nil {
		return "", err
	}
	defer podLogs.Close()

	buf := new(bytes.Buffer)
	_, err = io.Copy(buf, podLogs)
	if err != nil {
		return "", err
	}

	return buf.String(), nil
}

// ExtractModelName extract model name from logs
func ExtractModelName(logs string) (string, error) {
	re := regexp.MustCompile(`\[MIS Downloader] \[model] \[([\dA-Za-z.-]+)]`)

	matches := re.FindStringSubmatch(logs)

	if len(matches) > 1 {
		return matches[1], nil
	}

	return "", errors.New("unable to extract model name from logs")
}

// ExtractMISConfig extract mis_config from logs
func ExtractMISConfig(logs string) (string, error) {
	re := regexp.MustCompile(`\[MIS Downloader] \[MIS_CONFIG] \[([\da-z-]+)]`)

	matches := re.FindStringSubmatch(logs)

	if len(matches) > 1 {
		return matches[1], nil
	}

	return "", errors.New("unable to extract mis_config from logs")
}

// ExtractServerInfo extract server type and card num from config name
func ExtractServerInfo(misConfigName string) (alphav1.MISServerInfo, error) {
	re := regexp.MustCompile(`([\da-z]+)-(\d+)x(\d+g)b`)

	matches := re.FindStringSubmatch(misConfigName)

	serverTypeStr := ""
	cardNumStr := ""
	cardMemStr := ""

	if len(matches) > mISServerInfoLen {
		serverTypeStr = matches[mISServerInfoServerTypeIdx]
		cardNumStr = matches[mISServerInfoCardNumIdx]
		cardMemStr = matches[mISServerInfoCardMemIdx]
	} else {
		return alphav1.MISServerInfo{}, errors.New("unable to extract server info from mis_config")
	}

	var serverType alphav1.ServerType
	availableServerTypes := []alphav1.ServerType{alphav1.ServerTypeAtlas800IA2}
	for _, sType := range availableServerTypes {
		if serverTypeStr == string(sType) {
			serverType = sType
		}
	}
	if serverType == "" {
		return alphav1.MISServerInfo{}, errors.New("mis_config receive unsupported serverType")
	}

	var err error
	var cardNum resource.Quantity
	cardNum, err = resource.ParseQuantity(cardNumStr)
	if err != nil {
		return alphav1.MISServerInfo{}, errors.Wrap(err, "Unable to parse card num from mis_config")
	}

	cardMem := strings.ToUpper(cardMemStr)

	return alphav1.MISServerInfo{ServerType: serverType, CardNum: cardNum, CardMemory: cardMem}, nil
}
