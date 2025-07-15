/*
Copyright 2025 Huawei Technologies Co., Ltd.
*/

package utils

import (
	"net"

	"github.com/pkg/errors"
)

// GetIPv4ByInterface get ipv4 address base on given network-interface and only return one.
func GetIPv4ByInterface(name string) (string, error) {
	ief, err := net.InterfaceByName(name)
	if err != nil {
		return "", err
	}

	addrs, err := ief.Addrs()
	if err != nil {
		return "", err
	}

	for _, addr := range addrs {
		ipNet, ok := addr.(*net.IPNet)
		if !ok {
			continue
		}
		ip := ipNet.IP.To4()
		if ip == nil {
			continue // It's not an ipv4 address
		}
		return ip.String(), nil
	}

	return "", errors.New("unable to get IPV4 address of the given network interface")
}
