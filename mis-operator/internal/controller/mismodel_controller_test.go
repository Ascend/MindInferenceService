/*
Copyright 2025 Huawei Technologies Co., Ltd.
*/

package controller

import (
	"context"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
	"k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/types"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/client/fake"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"

	"ascend.com/mis-operator/api/apps/alphav1"
)

var _ = Describe("MISModel Controller", func() {

	var (
		reconciler *MISModelReconciler
		scheme     *runtime.Scheme
		client     client.Client

		ctx = context.Background()
	)

	BeforeEach(func() {
		scheme = runtime.NewScheme()
		Expect(alphav1.AddToScheme(scheme)).To(Succeed())

		client = fake.NewClientBuilder().
			WithScheme(scheme).
			WithStatusSubresource(&alphav1.MISModel{}).
			Build()

		reconciler = &MISModelReconciler{
			Client: client,
			Scheme: scheme,
		}
	})

	Context("When reconciling a resource", func() {
		It("should successfully reconcile the resource", func() {

			testMISModel := alphav1.MISModel{
				ObjectMeta: v1.ObjectMeta{
					Name: "test-name",
				},
			}
			Expect(client.Create(ctx, &testMISModel)).NotTo(HaveOccurred())

			_, err := reconciler.Reconcile(ctx, reconcile.Request{
				NamespacedName: types.NamespacedName{
					Name: "test-name",
				},
			})
			Expect(err).NotTo(HaveOccurred())
		})
	})
})
