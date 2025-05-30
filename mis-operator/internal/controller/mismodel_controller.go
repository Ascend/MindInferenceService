/*
Copyright 2025 Huawei Technologies Co., Ltd.
*/

package controller

import (
	"context"
	"time"

	"github.com/pkg/errors"
	"k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/meta"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/client-go/tools/record"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"
	"sigs.k8s.io/controller-runtime/pkg/log"

	"ascend.com/mis-operator/api/apps/alphav1"
)

// MISModelReconciler reconciles a MISModel object
type MISModelReconciler struct {
	client.Client
	Scheme   *runtime.Scheme
	recorder record.EventRecorder
}

func (r *MISModelReconciler) getStandardLabels(misModel *alphav1.MISModel) map[string]string {
	return map[string]string{
		MISLabelKeyName:      misModel.Name,
		MISLabelKeyInstance:  misModel.Name,
		MISLabelKeyPartOf:    MISModelLabelPartOf,
		MISLabelKeyManagedBy: MISLabelManagedBy,
	}
}

func (r *MISModelReconciler) getStandardSelectorLabels(misModel *alphav1.MISModel) map[string]string {
	return map[string]string{
		MISLabelManagedBy: misModel.Name,
	}
}

// +kubebuilder:rbac:groups=apps.ascend.com,resources=mismodels,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=apps.ascend.com,resources=mismodels/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=apps.ascend.com,resources=mismodels/finalizers,verbs=update
// +kubebuilder:rbac:groups="",resources=secrets,verbs=get;list;watch
// +kubebuilder:rbac:groups="",resources=persistentvolumeclaims,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups="",resources=pods,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups="",resources=pods/log,verbs=get
// +kubebuilder:rbac:groups="",resources=events,verbs=create;update;patch

// Reconcile is part of the main kubernetes reconciliation loop which aims to
// move the current state of the cluster closer to the desired state.
func (r *MISModelReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	logger := log.FromContext(ctx)

	logger.Info("Start reconciling")

	misModel := &alphav1.MISModel{}
	if err := r.Get(ctx, req.NamespacedName, misModel); err != nil {
		if client.IgnoreNotFound(err) != nil {
			logger.Error(err, "Unable to fetch MISModel")
			return ctrl.Result{}, err
		}
		return ctrl.Result{}, nil
	}

	if misModel.DeletionTimestamp.IsZero() {
		if !controllerutil.ContainsFinalizer(misModel, MISModelFinalizer) {
			controllerutil.AddFinalizer(misModel, MISModelFinalizer)
			if err := r.Update(ctx, misModel); err != nil {
				logger.Error(err, "Unable to add finalizer")
				return ctrl.Result{}, err
			}
			logger.Info("Add finalizer")
		}

		misModel.Status.State = alphav1.MISModelStateStarted
	} else {
		if controllerutil.ContainsFinalizer(misModel, MISModelFinalizer) {
			controllerutil.RemoveFinalizer(misModel, MISModelFinalizer)
			if err := r.Update(ctx, misModel); err != nil {
				logger.Error(err, "Unable to remove finalizer")
				return ctrl.Result{}, err
			}

			logger.Info("Remove finalizer")
			return ctrl.Result{}, nil
		}
	}

	result := ctrl.Result{}
	var err error
	if result, err = r.reconcileMISModel(ctx, misModel); err != nil {
		logger.Error(err, "Reconcile MISModel failed")
		r.recorder.Eventf(misModel, v1.EventTypeWarning, "Reconcile", "Reconcile MISModel failed with err: %s", err)
	}
	if err = r.updateMISModelStatus(ctx, misModel); err != nil {
		logger.Error(err, "Update MISModel status failed")
		return ctrl.Result{}, err
	}

	logger.Info("Reconciling succeed")

	return result, err
}

func (r *MISModelReconciler) reconcileMISModel(ctx context.Context, misModel *alphav1.MISModel) (ctrl.Result, error) {
	if requeue, err := r.checkSecret(ctx, misModel); err != nil {
		return ctrl.Result{}, errors.Wrap(err, "Unable to check secret")
	} else if requeue {
		return ctrl.Result{RequeueAfter: time.Minute}, nil
	}

	if requeue, err := r.reconcilePVC(ctx, misModel); err != nil {
		return ctrl.Result{}, errors.Wrap(err, "Unable to reconcile PVC")
	} else if requeue {
		return ctrl.Result{RequeueAfter: time.Minute}, nil
	}

	if requeue, err := r.reconcilePod(ctx, misModel); err != nil {
		return ctrl.Result{}, errors.Wrap(err, "Unable to reconcile download Job")
	} else if requeue {
		return ctrl.Result{RequeueAfter: time.Second}, nil
	}

	return ctrl.Result{}, nil
}

func (r *MISModelReconciler) checkSecret(ctx context.Context, misModel *alphav1.MISModel) (requeue bool, err error) {
	if misModel.Spec.ImagePullSecret == nil || *misModel.Spec.ImagePullSecret == "" {
		return false, nil
	}

	secret := v1.Secret{}
	secretName := types.NamespacedName{Namespace: misModel.Namespace, Name: *misModel.Spec.ImagePullSecret}
	if err := r.Get(ctx, secretName, &secret); err != nil {
		if client.IgnoreNotFound(err) != nil {
			return false, errors.Wrap(err, "Unable to fetch secret")
		}

		meta.SetStatusCondition(&misModel.Status.Conditions, metav1.Condition{
			Type:    alphav1.MISModelConditionSecretExist,
			Status:  metav1.ConditionFalse,
			Reason:  "SecretNotExist",
			Message: "secret not found",
		})

		return true, nil
	}

	misModel.Status.State = alphav1.MISModelStateSecretOK
	meta.SetStatusCondition(&misModel.Status.Conditions, metav1.Condition{
		Type:    alphav1.MISModelConditionSecretExist,
		Status:  metav1.ConditionTrue,
		Reason:  "SecretExist",
		Message: "secret found",
	})

	return false, nil
}

func (r *MISModelReconciler) reconcilePVC(ctx context.Context, misModel *alphav1.MISModel) (requeue bool, err error) {
	logger := log.FromContext(ctx)
	pvcName := misModel.Spec.Storage.PVC.Name
	pvcNamespaceName := types.NamespacedName{Namespace: misModel.Namespace, Name: pvcName}
	pvc := v1.PersistentVolumeClaim{}
	if err := r.Get(ctx, pvcNamespaceName, &pvc); err != nil {
		if client.IgnoreNotFound(err) != nil {
			return false, errors.Wrap(err, "Unable to fetch pvc")
		}
		if err := r.constructPVC(misModel, &pvc); err != nil {
			return false, errors.Wrap(err, "Unable to construct pvc")
		}
		if err := r.Create(ctx, &pvc); err != nil {
			return false, errors.Wrap(err, "Unable to create pvc")
		}
		logger.Info("Create pvc success")
		r.recorder.Eventf(misModel, v1.EventTypeNormal, "CreatePVC", "Create pvc success")
		meta.SetStatusCondition(&misModel.Status.Conditions, metav1.Condition{
			Type:    alphav1.MISModelConditionPVCReady,
			Status:  metav1.ConditionFalse,
			Reason:  "PVCCreate",
			Message: "pvc is create, waiting for ready",
		})
		return true, nil
	}

	if pvc.Status.Phase != v1.ClaimBound {
		meta.SetStatusCondition(&misModel.Status.Conditions, metav1.Condition{
			Type:    alphav1.MISModelConditionPVCReady,
			Status:  metav1.ConditionFalse,
			Reason:  "PVCPending",
			Message: "pvc is not bound",
		})
		return true, nil
	}

	misModel.Status.State = alphav1.MISModelStatePVCReady
	misModel.Status.PVC = pvcName
	meta.SetStatusCondition(&misModel.Status.Conditions, metav1.Condition{
		Type:    alphav1.MISModelConditionPVCReady,
		Status:  metav1.ConditionTrue,
		Reason:  "PVCReady",
		Message: "pvc is bound",
	})

	return false, nil
}

func (r *MISModelReconciler) constructPVC(misModel *alphav1.MISModel, pvc *v1.PersistentVolumeClaim) error {
	*pvc = v1.PersistentVolumeClaim{
		ObjectMeta: metav1.ObjectMeta{
			Namespace: misModel.Namespace,
			Name:      misModel.Spec.Storage.PVC.Name,
			Labels:    r.getStandardLabels(misModel),
		},
		Spec: v1.PersistentVolumeClaimSpec{
			AccessModes: []v1.PersistentVolumeAccessMode{misModel.Spec.Storage.PVC.VolumeAccessMode},
			Resources: v1.ResourceRequirements{
				Requests: v1.ResourceList{
					v1.ResourceStorage: misModel.GetPVCSize(),
				},
			},
			StorageClassName: misModel.GetPVCStorageClass(),
		},
	}
	if err := ctrl.SetControllerReference(misModel, pvc, r.Scheme); err != nil {
		return errors.Wrap(err, "Unable to set controller ref to PVC")
	}

	return nil
}

func (r *MISModelReconciler) reconcilePod(ctx context.Context, misModel *alphav1.MISModel) (bool, error) {
	return false, nil
}

func (r *MISModelReconciler) updateMISModelStatus(ctx context.Context, misModel *alphav1.MISModel) error {

	obj := alphav1.MISModel{}
	if err := r.Get(ctx, types.NamespacedName{Name: misModel.Name, Namespace: misModel.Namespace}, &obj); r != nil {
		if err != nil {
			return errors.Wrap(err, "Fetch MISModel failed")
		}
	}

	patch := client.MergeFrom(obj.DeepCopy())
	obj.Status = (*misModel).Status

	if err := r.Status().Patch(ctx, &obj, patch); err != nil {
		if err != nil {
			return errors.Wrap(err, "Update MISModel failed")
		}
	}

	return nil
}

// SetupWithManager sets up the controller with the Manager.
func (r *MISModelReconciler) SetupWithManager(mgr ctrl.Manager) error {
	r.recorder = mgr.GetEventRecorderFor("mismodel-controller")
	return ctrl.NewControllerManagedBy(mgr).
		For(&alphav1.MISModel{}).
		Named("mismodel").
		Owns(&v1.Secret{}).
		Owns(&v1.PersistentVolumeClaim{}).
		Owns(&v1.Pod{}).
		Complete(r)
}
