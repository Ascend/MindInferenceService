/*
Copyright 2025 Huawei Technologies Co., Ltd.
*/

package controller

import (
	"context"

	"github.com/agiledragon/gomonkey/v2"
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
	"github.com/pkg/errors"
	monitorv1 "github.com/prometheus-operator/prometheus-operator/pkg/apis/monitoring/v1"
	"k8s.io/api/autoscaling/v2"
	"k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/apimachinery/pkg/util/intstr"
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
			WithStatusSubresource(&v1.Secret{}).
			WithStatusSubresource(&v1.Service{}).
			WithStatusSubresource(&monitorv1.ServiceMonitor{}).
			WithStatusSubresource(&v2.HorizontalPodAutoscaler{}).
			WithStatusSubresource(ptr.To(getAcjobObject())).
			Build()

		reconciler = &MISServiceReconciler{
			Client:   testClient,
			Scheme:   testScheme,
			recorder: record.NewFakeRecorder(1000),
		}
	})

	Context("Test Check TLSSecret", func() {

		var (
			testNamespace string

			testTLSSecretName string

			testMISServiceName string

			testTLSSecret  v1.Secret
			testMISService alphav1.MISService
		)

		BeforeEach(func() {
			testNamespace = "test-namespace"

			testTLSSecretName = "test-tls-secret"

			testMISServiceName = "test-mis-service-name"

			testTLSSecret = v1.Secret{
				ObjectMeta: metav1.ObjectMeta{
					Name:      testTLSSecretName,
					Namespace: testNamespace,
				},
				Type: v1.SecretTypeTLS,
				Data: map[string][]byte{
					"tls.crt": []byte{},
					"tls.key": []byte{},
				},
			}

			testMISService = alphav1.MISService{
				ObjectMeta: metav1.ObjectMeta{
					Name:      testMISServiceName,
					Namespace: testNamespace,
				},
				Spec: alphav1.MISServiceSpec{
					TLSSecret: testTLSSecretName,
				},
			}
		})

		It("should return err if no TLSSecret found", func() {
			err := reconciler.checkTLSSecret(ctx, &testMISService)
			Expect(err).To(HaveOccurred())
		})

		It("should requeue if TLSSecret type not right", func() {
			testTLSSecret.Type = v1.SecretTypeBasicAuth
			Expect(testClient.Create(ctx, &testTLSSecret)).NotTo(HaveOccurred())

			err := reconciler.checkTLSSecret(ctx, &testMISService)
			Expect(err).To(HaveOccurred())
		})

		It("should return true if TLSSecret is right", func() {
			Expect(testClient.Create(ctx, &testTLSSecret)).NotTo(HaveOccurred())

			err := reconciler.checkTLSSecret(ctx, &testMISService)
			Expect(err).NotTo(HaveOccurred())

			Expect(testMISService.Status.State).To(Equal(alphav1.MISServiceStateTLSSecretReady))
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
			testHPA        v2.HorizontalPodAutoscaler
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
						Behavior: &v2.HorizontalPodAutoscalerBehavior{
							ScaleUp: &v2.HPAScalingRules{
								Policies: []v2.HPAScalingPolicy{
									{
										Type:          v2.PodsScalingPolicy,
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

			testHPA = v2.HorizontalPodAutoscaler{
				ObjectMeta: metav1.ObjectMeta{
					Name:      testMISService.GetServiceMonitorName(),
					Namespace: testNamespace,
				},
				Spec: v2.HorizontalPodAutoscalerSpec{},
			}
		})

		Context("Test reconcile service", func() {
			It("should create new svc if svc not found", func() {
				Expect(reconciler.reconcileService(ctx, &testMISService)).NotTo(HaveOccurred())

				testSvcNamespaceName := types.NamespacedName{Name: testSvcName, Namespace: testNamespace}
				Expect(testClient.Get(ctx, testSvcNamespaceName, &testSvc)).NotTo(HaveOccurred())

				Expect(testSvc.Spec.Type == testMISService.Spec.ServiceSpec.Type).To(BeTrue())
				Expect(testSvc.Spec.Ports[1].Port == testMISService.Spec.ServiceSpec.Port).To(BeTrue())
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

				Expect(testSvcMonitor.Spec.Endpoints[0].Port == MISServiceMetricsPortName).To(BeTrue())
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

	Context("Test reconcile acjob", func() {
		var (
			testMISServiceName  string
			testNamespace       string
			testReplicas        int
			testPort            int32
			testUserId          int64
			testGroupId         int64
			testImage           string
			testImagePullSecret string
			testPVC             string
			testProbUrl         string
			testEnvs            []v1.EnvVar

			testMISService alphav1.MISService
		)

		BeforeEach(func() {
			testReplicas = 2
			testPort = 8000
			testUserId = 1000
			testGroupId = 1000
			testImage = "deepseek-r1-qwen1.5:0.1"
			testImagePullSecret = "test-secret"
			testPVC = "test-pvc"
			testProbUrl = "/openai/v1/models"
			testEnvs = []v1.EnvVar{
				{
					Name:  "MIS_CONFIG",
					Value: "test-mid-config",
				}, {
					Name:  "MIS_CACHE_PATH",
					Value: "/opt/mis-management/test",
				},
			}

			testMISService = alphav1.MISService{
				ObjectMeta: metav1.ObjectMeta{
					Name:      testMISServiceName,
					Namespace: testNamespace,
				},
				Spec: alphav1.MISServiceSpec{
					Replicas: testReplicas,
					ReadinessProbe: &v1.Probe{
						ProbeHandler: v1.ProbeHandler{
							HTTPGet: &v1.HTTPGetAction{
								Path: testProbUrl,
								Port: intstr.FromInt32(testPort),
							},
						},
					},
					Image:           testImage,
					ImagePullSecret: &testImagePullSecret,
					PVC:             testPVC,
					Envs:            testEnvs,
					UserID:          ptr.To[int64](testUserId),
					GroupID:         ptr.To[int64](testGroupId),
				},
				Status: alphav1.MISServiceStatus{},
			}

		})

		It("should success create target replicas of acjob", func() {
			createTimes := 0
			reservedObject := unstructured.Unstructured{}

			createPatch := gomonkey.ApplyMethodFunc(testClient, "Create",
				func(ctx context.Context, obj client.Object, opts ...client.CreateOption) error {
					createTimes++
					acjob, ok := obj.(*unstructured.Unstructured)
					if !ok {
						return errors.New("failed")
					}
					reservedObject = *acjob
					return nil
				})
			defer createPatch.Reset()

			requeue, err := reconciler.reconcileAcJob(ctx, &testMISService)
			Expect(requeue).To(BeTrue())
			Expect(err).NotTo(HaveOccurred())

			Expect(createTimes == testReplicas).To(BeTrue())

			acjobSpecData, ok := reservedObject.Object["spec"]
			Expect(ok).To(BeTrue())
			acjobSpec, ok := acjobSpecData.(map[string]interface{})
			Expect(ok).To(BeTrue())

			acjobReplicaSpecsData, ok := acjobSpec["replicaSpecs"]
			Expect(ok).To(BeTrue())
			acjobReplicaSpec, ok := acjobReplicaSpecsData.(map[string]interface{})
			Expect(ok).To(BeTrue())

			masterReplicaSpecPtrData, ok := acjobReplicaSpec[MISServiceAcjobMaster]
			Expect(ok).To(BeTrue())
			masterReplicaSpecPtr, ok := masterReplicaSpecPtrData.(*map[string]interface{})
			Expect(ok).To(BeTrue())

			masterTemplateSpecData, ok := (*masterReplicaSpecPtr)["template"]
			Expect(ok).To(BeTrue())
			masterReplicaSpec, ok := masterTemplateSpecData.(v1.PodTemplateSpec)
			Expect(ok).To(BeTrue())

			podSpec := masterReplicaSpec.Spec
			Expect(podSpec.Containers[0].Name == MISServiceAcjobContainerName).To(BeTrue())

			Expect(*podSpec.SecurityContext.RunAsUser == testUserId).To(BeTrue())
			Expect(*podSpec.SecurityContext.RunAsGroup == testGroupId).To(BeTrue())

			Expect(podSpec.Containers[0].ReadinessProbe.ProbeHandler.HTTPGet.Path == testProbUrl).To(BeTrue())
			Expect(podSpec.Containers[0].ReadinessProbe.ProbeHandler.HTTPGet.Port == intstr.FromInt32(testPort)).To(BeTrue())
			Expect(podSpec.Containers[0].Image == testImage).To(BeTrue())

			Expect(podSpec.Containers[0].Env[0].Name).To(Equal("MIS_CONFIG"))

			Expect(podSpec.ImagePullSecrets[0].Name).To(Equal(testImagePullSecret))

		})
	})
})
