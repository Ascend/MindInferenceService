/*
Copyright 2025 Huawei Technologies Co., Ltd.
*/

package controller

import (
	"testing"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
)

func TestControllers(t *testing.T) {
	RegisterFailHandler(Fail)
	RunSpecs(t, "Controller Suite")
}

var _ = BeforeSuite(func() {
	By("TestControllers start")
})

var _ = AfterSuite(func() {
	By("TestControllers end")
})
