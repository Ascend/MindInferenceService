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

	"github.com/pkg/errors"
	"k8s.io/api/core/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
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
