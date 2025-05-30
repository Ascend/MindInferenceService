/*
Copyright 2025 Huawei Technologies Co., Ltd.
*/

package utils

import (
	"testing"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
)

func TestControllers(t *testing.T) {
	RegisterFailHandler(Fail)
	RunSpecs(t, "Utils Suite")
}

var _ = BeforeSuite(func() {
	By("Test utils start")
})

var _ = AfterSuite(func() {
	By("Test utils end")
})
