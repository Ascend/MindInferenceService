/*
Copyright 2025 Huawei Technologies Co., Ltd.
*/

package controller

import (
	"context"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
	"k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/client-go/kubernetes/scheme"
	"k8s.io/client-go/tools/record"
	"k8s.io/utils/ptr"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/client/fake"
	"sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"

	"ascend.com/mis-operator/api/apps/alphav1"
)

var _ = Describe("MISModel Controller", func() {

	var (
		reconciler *MISModelReconciler
		testScheme *runtime.Scheme
		testClient client.Client

		ctx = context.Background()
	)

	BeforeEach(func() {
		testScheme = runtime.NewScheme()
		Expect(scheme.AddToScheme(testScheme)).To(Succeed())
		Expect(alphav1.AddToScheme(testScheme)).To(Succeed())

		testClient = fake.NewClientBuilder().
			WithScheme(testScheme).
			WithStatusSubresource(&alphav1.MISModel{}).
			WithStatusSubresource(&v1.Secret{}).
			WithStatusSubresource(&v1.PersistentVolumeClaim{}).
			WithStatusSubresource(&v1.Pod{}).
			Build()

		reconciler = &MISModelReconciler{
			Client:   testClient,
			Scheme:   testScheme,
			recorder: record.NewFakeRecorder(1000),
		}
	})

	Context("Test reconcile", func() {
		It("should add finalizer to new MISModel", func() {
			secretName := "test-secret-name"
			misModel := alphav1.MISModel{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "test-name",
					Namespace: "default",
				},
				Spec: alphav1.MISModelSpec{
					ImagePullSecret: &secretName,
				},
			}
			Expect(testClient.Create(ctx, &misModel)).NotTo(HaveOccurred())

			namespaceName := types.NamespacedName{Name: "test-name", Namespace: "default"}
			_, err := reconciler.Reconcile(ctx, ctrl.Request{NamespacedName: namespaceName})
			Expect(err).NotTo(HaveOccurred())

			Expect(testClient.Get(ctx, namespaceName, &misModel)).NotTo(HaveOccurred())
			Expect(controllerutil.ContainsFinalizer(&misModel, MISModelFinalizer)).To(BeTrue())
		})

		It("should delete MISModel when deletion time exist", func() {
			secretName := "test-secret-name"
			misModel := alphav1.MISModel{
				ObjectMeta: metav1.ObjectMeta{
					Name:              "test-name",
					Namespace:         "default",
					DeletionTimestamp: ptr.To(metav1.Now()),
				},
				Spec: alphav1.MISModelSpec{
					ImagePullSecret: &secretName,
				},
			}
			Expect(testClient.Create(ctx, &misModel)).NotTo(HaveOccurred())

			namespaceName := types.NamespacedName{Name: "test-name", Namespace: "default"}
			_, err := reconciler.Reconcile(ctx, ctrl.Request{NamespacedName: namespaceName})
			Expect(err).NotTo(HaveOccurred())

			Expect(client.IgnoreNotFound(testClient.Get(ctx, namespaceName, &misModel))).NotTo(HaveOccurred())
		})
	})

	Context("Test check secret", func() {

		It("should succeeded when secret existed", func() {
			secretName := "test-secret-name"
			misModel := alphav1.MISModel{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "test-name",
					Namespace: "default",
				},
				Spec: alphav1.MISModelSpec{
					ImagePullSecret: &secretName,
				},
			}
			Expect(testClient.Create(ctx, &misModel)).NotTo(HaveOccurred())

			secret := v1.Secret{
				ObjectMeta: metav1.ObjectMeta{
					Namespace: "default",
					Name:      secretName,
				},
			}
			Expect(testClient.Create(ctx, &secret)).NotTo(HaveOccurred())

			requeue, err := reconciler.checkSecret(ctx, &misModel)
			Expect(requeue).To(BeFalse())
			Expect(err).NotTo(HaveOccurred())
		})

		It("should requeue when secret not existed", func() {
			secretName := "test-secret-name"
			misModel := alphav1.MISModel{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "test-name",
					Namespace: "default",
				},
				Spec: alphav1.MISModelSpec{
					ImagePullSecret: &secretName,
				},
			}
			Expect(testClient.Create(ctx, &misModel)).NotTo(HaveOccurred())

			requeue, err := reconciler.checkSecret(ctx, &misModel)
			Expect(requeue).To(BeTrue())
			Expect(err).NotTo(HaveOccurred())
		})

	})

	Context("Test reconcile pvc", func() {

		It("should succeeded when pvc existed", func() {
			pvcName := "test-pvc-name"
			misModel := alphav1.MISModel{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "test-name",
					Namespace: "default",
				},
				Spec: alphav1.MISModelSpec{
					Storage: alphav1.MISModelStorage{
						PVC: alphav1.MISPVC{
							Name: pvcName,
						},
					},
				},
			}
			Expect(testClient.Create(ctx, &misModel)).NotTo(HaveOccurred())

			pvc := v1.PersistentVolumeClaim{
				ObjectMeta: metav1.ObjectMeta{
					Namespace: "default",
					Name:      pvcName,
				},
				Status: v1.PersistentVolumeClaimStatus{
					Phase: v1.ClaimBound,
				},
			}
			Expect(testClient.Create(ctx, &pvc)).NotTo(HaveOccurred())

			requeue, err := reconciler.reconcilePVC(ctx, &misModel)
			Expect(requeue).To(BeFalse())
			Expect(err).NotTo(HaveOccurred())
		})

		It("should requeue when pvc not bound", func() {
			pvcName := "test-pvc-name"
			misModel := alphav1.MISModel{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "test-name",
					Namespace: "default",
				},
				Spec: alphav1.MISModelSpec{
					Storage: alphav1.MISModelStorage{
						PVC: alphav1.MISPVC{
							Name: pvcName,
						},
					},
				},
			}
			Expect(testClient.Create(ctx, &misModel)).NotTo(HaveOccurred())

			pvc := v1.PersistentVolumeClaim{
				ObjectMeta: metav1.ObjectMeta{
					Namespace: "default",
					Name:      pvcName,
				},
				Status: v1.PersistentVolumeClaimStatus{
					Phase: v1.ClaimPending,
				},
			}
			Expect(testClient.Create(ctx, &pvc)).NotTo(HaveOccurred())

			requeue, err := reconciler.reconcilePVC(ctx, &misModel)
			Expect(requeue).To(BeTrue())
			Expect(err).NotTo(HaveOccurred())
		})

		It("should produce pvc when no pvc found", func() {
			pvcName := "test-pvc-name"
			misModel := alphav1.MISModel{
				ObjectMeta: metav1.ObjectMeta{
					Name:      "test-name",
					Namespace: "default",
				},
				Spec: alphav1.MISModelSpec{
					Storage: alphav1.MISModelStorage{
						PVC: alphav1.MISPVC{
							Name:             pvcName,
							StorageClass:     "test-storage-class",
							Size:             "10Gi",
							VolumeAccessMode: v1.ReadWriteOnce,
						},
					},
				},
			}
			Expect(testClient.Create(ctx, &misModel)).NotTo(HaveOccurred())

			requeue, err := reconciler.reconcilePVC(ctx, &misModel)
			Expect(requeue).To(BeTrue())
			Expect(err).NotTo(HaveOccurred())

			pvc := v1.PersistentVolumeClaim{}
			err = testClient.Get(ctx, types.NamespacedName{Namespace: misModel.Namespace, Name: pvcName}, &pvc)
			Expect(err).NotTo(HaveOccurred())

			Expect(pvc.Spec.StorageClassName).NotTo(Equal(nil))
			Expect(misModel.Spec.Storage.PVC.StorageClass).To(Equal(*pvc.Spec.StorageClassName))
			Expect(resource.MustParse(misModel.Spec.Storage.PVC.Size)).To(Equal(pvc.Spec.Resources.Requests[v1.ResourceStorage]))
		})

	})

})
