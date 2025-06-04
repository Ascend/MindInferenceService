/*
Copyright 2025 Huawei Technologies Co., Ltd.
*/

package utils

import (
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
	"k8s.io/apimachinery/pkg/api/resource"

	"ascend.com/mis-operator/api/apps/alphav1"
)

var _ = Describe("parser utils", func() {
	Context("Test parser log", func() {

		It("should return model name succeeded when log is valid", func() {
			logs := "INFO 05-24 18:23:49 mis_download:8] [MIS Downloader] [model] [DeepSeek-R1-Distill-Qwen-14B]"

			modelName, err := ExtractModelName(logs)
			Expect(err).NotTo(HaveOccurred())
			Expect(modelName).To(Equal("DeepSeek-R1-Distill-Qwen-14B"))
		})

		It("should return mis config succeeded when log is valid", func() {
			logs := "INFO 05-24 18:23:49 mis_download:8] [MIS Downloader] [MIS_CONFIG] [atlas800ia2-1x32gb-bf16-vllm-default]"

			misConfig, err := ExtractMISConfig(logs)
			Expect(err).NotTo(HaveOccurred())
			Expect(misConfig).To(Equal("atlas800ia2-1x32gb-bf16-vllm-default"))
		})

	})

	Context("Test parser server info", func() {

		It("should return server info succeeded", func() {
			misConfig := "atlas800ia2-1x32gb-bf16-vllm-default"

			serverInfo, err := ExtractServerInfo(misConfig)
			Expect(err).NotTo(HaveOccurred())
			Expect(serverInfo.ServerType).To(Equal(alphav1.ServerTypeAtlas800IA2))
			Expect(serverInfo.CardNum).To(Equal(resource.MustParse("1")))
			Expect(serverInfo.CardMemory).To(Equal("32G"))
		})

	})
})
