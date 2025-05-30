/*
Copyright 2025 Huawei Technologies Co., Ltd.
*/

package controller

import (
	"context"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
	monitorv1 "github.com/prometheus-operator/prometheus-operator/pkg/apis/monitoring/v1"
	"k8s.io/api/autoscaling/v2beta2"
	"k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/client-go/kubernetes/scheme"
	"k8s.io/client-go/tools/record"
	"k8s.io/utils/ptr"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/client/fake"

	"ascend.com/mis-operator/api/apps/alphav1"
)

var _ = Describe("MISService Controller", func() {

	var (
		reconciler *MISServiceReconciler
		testScheme *runtime.Scheme
		testClient client.Client

		ctx = context.Background()
	)

	BeforeEach(func() {
		testScheme = runtime.NewScheme()
		Expect(scheme.AddToScheme(testScheme)).To(Succeed())
		Expect(alphav1.AddToScheme(testScheme)).To(Succeed())
		Expect(monitorv1.AddToScheme(testScheme)).To(Succeed())

		testClient = fake.NewClientBuilder().
			WithScheme(testScheme).
			WithStatusSubresource(&alphav1.MISService{}).
			WithStatusSubresource(&alphav1.MISModel{}).
			WithStatusSubresource(&v1.Service{}).
			WithStatusSubresource(&monitorv1.ServiceMonitor{}).
			WithStatusSubresource(&v2beta2.HorizontalPodAutoscaler{}).
			WithStatusSubresource(ptr.To(getAcjobObject())).
			Build()

		reconciler = &MISServiceReconciler{
			Client:   testClient,
			Scheme:   testScheme,
			recorder: record.NewFakeRecorder(1000),
		}
	})

	Context("Test Check MISModel", func() {

		var (
			testNamespace      string
			testPVCName        string
			testMISModelName   string
			testModelName      string
			testMISServiceName string

			testMISModel   alphav1.MISModel
			testMISService alphav1.MISService
		)

		BeforeEach(func() {
			testNamespace = "test-namespace"
			testPVCName = "test-pvc-name"
			testMISModelName = "test-mis-model-name"
			testModelName = "test-model-name"
			testMISServiceName = "test-mis-service-name"

			testMISModel = alphav1.MISModel{
				ObjectMeta: metav1.ObjectMeta{
					Name:      testMISModelName,
					Namespace: testNamespace,
				},
				Spec: alphav1.MISModelSpec{
					Storage: alphav1.MISModelStorage{
						PVC: alphav1.MISPVC{
							Name: testPVCName,
						},
					},
				},
				Status: alphav1.MISModelStatus{
					State: alphav1.MISModelStateReady,
					PVC:   testPVCName,
					Model: testModelName,
				},
			}

			testMISService = alphav1.MISService{
				ObjectMeta: metav1.ObjectMeta{
					Name:      testMISServiceName,
					Namespace: testNamespace,
				},
				Spec: alphav1.MISServiceSpec{
					MISModel: testMISModelName,
				},
			}
		})

		It("should return err if no MISModel found", func() {
			requeue, err := reconciler.checkMISModel(ctx, &testMISService)
			Expect(requeue).To(BeFalse())
			Expect(err).To(HaveOccurred())
		})

		It("should requeue if MISModel not ready", func() {
			testMISModel.Status.State = alphav1.MISModelStateInProgress
			Expect(testClient.Create(ctx, &testMISModel)).NotTo(HaveOccurred())

			requeue, err := reconciler.checkMISModel(ctx, &testMISService)
			Expect(requeue).To(BeTrue())
			Expect(err).NotTo(HaveOccurred())
		})

		It("should return true if MISModel found", func() {
			Expect(testClient.Create(ctx, &testMISModel)).NotTo(HaveOccurred())

			requeue, err := reconciler.checkMISModel(ctx, &testMISService)
			Expect(requeue).To(BeFalse())
			Expect(err).NotTo(HaveOccurred())

			Expect(testMISService.Status.State).To(Equal(alphav1.MISServiceStateModelReady))
			Expect(testMISService.Status.PVC).To(Equal(testPVCName))
			Expect(testMISService.Status.Model).To(Equal(testModelName))
		})
	})
})
