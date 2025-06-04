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
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/client-go/kubernetes/scheme"
	"k8s.io/client-go/tools/record"
	"k8s.io/utils/ptr"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/client/fake"

	"ascend.com/mis-operator/api/apps/alphav1"
	"ascend.com/mis-operator/internal/utils"
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

	Context("Prepare test for reconcile service, service monitor, hpa", func() {

		var (
			testNamespace      string
			testSvcName        string
			testPort           int32
			testMISServiceName string

			testMISService alphav1.MISService
			testSvc        v1.Service
			testSvcMonitor monitorv1.ServiceMonitor
			testHPA        v2beta2.HorizontalPodAutoscaler
		)

		BeforeEach(func() {
			testNamespace = "test-namespace"
			testSvcName = "test-svc-name"
			testPort = 12345
			testMISServiceName = "test-mis-service-name"

			testMISService = alphav1.MISService{
				ObjectMeta: metav1.ObjectMeta{
					Name:      testMISServiceName,
					Namespace: testNamespace,
				},
				Spec: alphav1.MISServiceSpec{
					ServiceSpec: alphav1.MISSvcSpec{
						Type: v1.ServiceTypeClusterIP,
						Name: testSvcName,
						Port: testPort,
						Annotations: map[string]string{
							"key": "value",
						},
					},
					HPA: &alphav1.HPA{
						MinReplicas: 1,
						MaxReplicas: 3,
						Metrics: &[]alphav1.Metric{
							{
								Type:      alphav1.MetricsTypeRequestRate,
								Threshold: "0.1",
							},
						},
						Behavior: &v2beta2.HorizontalPodAutoscalerBehavior{
							ScaleUp: &v2beta2.HPAScalingRules{
								Policies: []v2beta2.HPAScalingPolicy{
									{
										Type:          v2beta2.PodsScalingPolicy,
										Value:         1,
										PeriodSeconds: 120,
									},
								},
							},
						},
					},
				},
			}

			testSvc = v1.Service{
				ObjectMeta: metav1.ObjectMeta{
					Name:      testSvcName,
					Namespace: testNamespace,
				},
				Spec: v1.ServiceSpec{},
			}

			testSvcMonitor = monitorv1.ServiceMonitor{
				ObjectMeta: metav1.ObjectMeta{
					Name:      testMISService.GetServiceMonitorName(),
					Namespace: testNamespace,
				},
				Spec: monitorv1.ServiceMonitorSpec{},
			}

			testHPA = v2beta2.HorizontalPodAutoscaler{
				ObjectMeta: metav1.ObjectMeta{
					Name:      testMISService.GetServiceMonitorName(),
					Namespace: testNamespace,
				},
				Spec: v2beta2.HorizontalPodAutoscalerSpec{},
			}
		})

		Context("Test reconcile service", func() {
			It("should create new svc if svc not found", func() {
				Expect(reconciler.reconcileService(ctx, &testMISService)).NotTo(HaveOccurred())

				testSvcNamespaceName := types.NamespacedName{Name: testSvcName, Namespace: testNamespace}
				Expect(testClient.Get(ctx, testSvcNamespaceName, &testSvc)).NotTo(HaveOccurred())

				Expect(testSvc.Spec.Type == testMISService.Spec.ServiceSpec.Type).To(BeTrue())
				Expect(testSvc.Spec.Ports[0].Port == testMISService.Spec.ServiceSpec.Port).To(BeTrue())
				Expect(utils.MapEqual(testSvc.Annotations, testMISService.Spec.ServiceSpec.Annotations)).To(BeTrue())
			})

			It("should update status if svc is found", func() {
				Expect(testClient.Create(ctx, &testSvc)).NotTo(HaveOccurred())

				Expect(reconciler.reconcileService(ctx, &testMISService)).NotTo(HaveOccurred())

				Expect(testMISService.Status.State == alphav1.MISServiceStateServiceCreated).To(BeTrue())
			})
		})

		Context("Test reconcile service monitor", func() {
			It("should do nothing if no hpa given", func() {
				testMISService.Spec.HPA = nil

				Expect(reconciler.reconcileServiceMonitor(ctx, &testMISService)).NotTo(HaveOccurred())

				testSvcNamespaceName := types.NamespacedName{Namespace: testNamespace, Name: testSvcName}
				Expect(testClient.Get(ctx, testSvcNamespaceName, &testSvcMonitor)).To(HaveOccurred())
			})

			It("should create service monitor if hpa given", func() {
				Expect(reconciler.reconcileServiceMonitor(ctx, &testMISService)).NotTo(HaveOccurred())

				testSvcNamespaceName := types.NamespacedName{
					Namespace: testNamespace, Name: testMISService.GetServiceMonitorName()}
				Expect(testClient.Get(ctx, testSvcNamespaceName, &testSvcMonitor)).NotTo(HaveOccurred())

				Expect(testSvcMonitor.Spec.Endpoints[0].Port == MISServicePortName).To(BeTrue())
				Expect(utils.MapEqual(testSvcMonitor.Spec.Selector.MatchLabels, reconciler.getStandardLabels(&testMISService))).To(BeTrue())
			})
		})

		Context("Test reconcile hpa", func() {
			It("should do nothing if no hpa given", func() {
				testMISService.Spec.HPA = nil

				Expect(reconciler.reconcileHPA(ctx, &testMISService)).NotTo(HaveOccurred())

				testHPANamespaceName := types.NamespacedName{
					Namespace: testNamespace, Name: testMISService.GetHPAName()}
				Expect(testClient.Get(ctx, testHPANamespaceName, &testHPA)).To(HaveOccurred())
			})

			It("should create hpa if hpa is config", func() {
				Expect(reconciler.reconcileHPA(ctx, &testMISService)).NotTo(HaveOccurred())

				testHPANamespaceName := types.NamespacedName{
					Namespace: testNamespace, Name: testMISService.GetHPAName()}
				Expect(testClient.Get(ctx, testHPANamespaceName, &testHPA)).NotTo(HaveOccurred())

				policya := (*testHPA.Spec.Behavior).ScaleUp.Policies[0]
				policyb := (*testMISService.Spec.HPA.Behavior).ScaleUp.Policies[0]
				Expect(policya == policyb).To(BeTrue())
				Expect(*testHPA.Spec.MinReplicas == testMISService.Spec.HPA.MinReplicas).To(BeTrue())
				Expect(testHPA.Spec.MaxReplicas == testMISService.Spec.HPA.MaxReplicas).To(BeTrue())
				Expect(testMISService.Status.State == alphav1.MISServiceStateHPACreated).To(BeTrue())
			})
		})
	})

})
