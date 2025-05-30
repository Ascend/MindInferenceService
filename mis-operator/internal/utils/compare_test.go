/*
Copyright 2025 Huawei Technologies Co., Ltd.
*/

package utils

import (
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
)

var _ = Describe("compare utils", func() {
	Context("Test compare map", func() {

		It("should succeeded when map is same", func() {

			mapa := map[string]interface{}{
				"a": 1,
				"b": 2,
			}

			mapb := map[string]interface{}{
				"a": 1,
				"b": 2,
			}

			Expect(MapEqual(mapa, mapb)).To(BeTrue())
		})

		It("should failed when map is not same", func() {

			mapa := map[string]interface{}{
				"a": 1,
				"b": 2,
			}

			mapb := map[string]interface{}{
				"a": "hello",
				"b": 2,
			}

			Expect(MapEqual(mapa, mapb)).NotTo(BeTrue())
		})
	})
})
