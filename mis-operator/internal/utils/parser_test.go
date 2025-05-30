/*
Copyright 2025 Huawei Technologies Co., Ltd.
*/

package utils

import (
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
)

var _ = Describe("parser utils", func() {
	Context("Test parser log", func() {

		It("should succeeded when log is valid", func() {
			logs := "INFO 05-24 18:23:49 mis_download:8] [MIS Downloader] [model] [DeepSeek-R1-Distill-Qwen-14B]"

			modelName, err := ExtractModelName(logs)
			Expect(err).NotTo(HaveOccurred())
			Expect(modelName).To(Equal("DeepSeek-R1-Distill-Qwen-14B"))
		})

	})
})
