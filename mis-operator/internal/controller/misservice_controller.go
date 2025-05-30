/*
Copyright 2025 Huawei Technologies Co., Ltd.
*/

package controller

import (
	"context"
	"fmt"
	"time"

	"github.com/pkg/errors"
	monitorv1 "github.com/prometheus-operator/prometheus-operator/pkg/apis/monitoring/v1"
	"k8s.io/api/autoscaling/v2beta2"
	"k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/meta"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/client-go/tools/record"
	"k8s.io/utils/ptr"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"
	"sigs.k8s.io/controller-runtime/pkg/log"

	"ascend.com/mis-operator/api/apps/alphav1"
)

// MISServiceReconciler reconciles a MISService object
type MISServiceReconciler struct {
	client.Client
	Scheme   *runtime.Scheme
	recorder record.EventRecorder
}

func (r *MISServiceReconciler) getStandardLabels(misService *alphav1.MISService) map[string]string {
	return map[string]string{
		MISLabelKeyName:      misService.Name,
		MISLabelKeyInstance:  misService.Name,
		MISLabelKeyPartOf:    MISServiceLabelPartOf,
		MISLabelKeyManagedBy: MISLabelManagedBy,
	}
}

func (r *MISServiceReconciler) getStandardSelectorLabels(misService *alphav1.MISService) map[string]string {
	return map[string]string{
		MISLabelManagedBy: misService.Name,
	}
}

// +kubebuilder:rbac:groups=apps.ascend.com,resources=misservices,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=apps.ascend.com,resources=misservices/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=apps.ascend.com,resources=misservices/finalizers,verbs=update
// +kubebuilder:rbac:groups=apps.ascend.com,resources=mismodel,verbs=get;list;watch
// +kubebuilder:rbac:groups="",resources=services,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=monitoring.coreos.com,resources=servicemonitors,verbs=get;list;watch
// +kubebuilder:rbac:groups=monitoring.coreos.com,resources=servicemonitors,verbs=create;update;patch;delete
// +kubebuilder:rbac:groups=autoscaling,resources=horizontalpodautoscalers,verbs=get;list;watch
// +kubebuilder:rbac:groups=autoscaling,resources=horizontalpodautoscalers,verbs=create;update;patch;delete
// +kubebuilder:rbac:groups=mindxdl.gitee.com,resources=ascendjobs,verbs=get;list;watch;create;update;patch;delete

// Reconcile is part of the main kubernetes reconciliation loop which aims to
// move the current state of the cluster closer to the desired state.
func (r *MISServiceReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	logger := log.FromContext(ctx)

	logger.Info("Start reconciling")

	misService := &alphav1.MISService{}
	if err := r.Get(ctx, req.NamespacedName, misService); err != nil {
		if client.IgnoreNotFound(err) != nil {
			logger.Error(err, "Unable to fetch misService")
			return ctrl.Result{}, err
		}
		return ctrl.Result{}, nil
	}

	if misService.DeletionTimestamp.IsZero() {
		if !controllerutil.ContainsFinalizer(misService, MISServiceFinalizer) {
			controllerutil.AddFinalizer(misService, MISServiceFinalizer)
			if err := r.Update(ctx, misService); err != nil {
				logger.Error(err, "Unable to add finalizer")
				return ctrl.Result{}, err
			}
			logger.Info("Add finalizer")
		}

		misService.Status.State = alphav1.MISServiceStateStarted
		misService.Status.Selector = fmt.Sprintf("%s=%s", "mis-service", misService.Name)
	} else {
		if controllerutil.ContainsFinalizer(misService, MISServiceFinalizer) {
			controllerutil.RemoveFinalizer(misService, MISServiceFinalizer)
			if err := r.Update(ctx, misService); err != nil {
				logger.Error(err, "Unable to remove finalizer")
				return ctrl.Result{}, err
			}
			logger.Info("Remove finalizer")
			return ctrl.Result{}, nil
		}
	}

	result := ctrl.Result{}
	var err error
	if result, err = r.reconcileMISService(ctx, misService); err != nil {
		logger.Error(err, "Reconcile misService failed")
		r.recorder.Eventf(misService, v1.EventTypeWarning, "Reconcile",
			"Reconcile misService failed with err: %s", err)
	}
	if err = r.updateMISServiceStatus(ctx, misService); err != nil {
		logger.Error(err, "Update misService status failed")
		return ctrl.Result{}, err
	}

	logger.Info("Reconciling succeed")

	return result, err
}

func (r *MISServiceReconciler) reconcileMISService(
	ctx context.Context, misService *alphav1.MISService) (ctrl.Result, error) {

	logger := log.FromContext(ctx)

	if requeue, err := r.checkMISModel(ctx, misService); err != nil {
		logger.Error(err, "Unable to check MISModel status")
		return ctrl.Result{}, err
	} else if requeue {
		return ctrl.Result{RequeueAfter: time.Minute}, err
	}

	if err := r.reconcileService(ctx, misService); err != nil {
		logger.Error(err, "Error occur while create Service")
		return ctrl.Result{}, err
	}

	if err := r.reconcileServiceMonitor(ctx, misService); err != nil {
		logger.Error(err, "Error occur while create ServiceMonitor")
		return ctrl.Result{}, err
	}

	if err := r.reconcileHPA(ctx, misService); err != nil {
		logger.Error(err, "Error occur while create HPA")
		return ctrl.Result{}, err
	}

	if requeue, err := r.reconcileAcJob(ctx, misService); err != nil {
		logger.Error(err, "Error occur while reconcile acjob")
		return ctrl.Result{}, err
	} else if requeue {
		return ctrl.Result{Requeue: true}, nil
	}

	return ctrl.Result{}, nil
}

func (r *MISServiceReconciler) checkMISModel(
	ctx context.Context, misService *alphav1.MISService) (requeue bool, err error) {

	misModel := alphav1.MISModel{}
	namespaceName := types.NamespacedName{Namespace: misService.Namespace, Name: misService.Spec.MISModel}
	if err := r.Get(ctx, namespaceName, &misModel); err != nil {
		if client.IgnoreNotFound(err) != nil {
			return false, errors.Wrap(err, "Unable to fetch MISModel")
		}
		return false, errors.Wrap(err, "MISModel not exist")
	}

	if misModel.Status.State != alphav1.MISModelStateReady {
		meta.SetStatusCondition(&misService.Status.Conditions, metav1.Condition{
			Type:    alphav1.MISServiceConditionModelReady,
			Status:  metav1.ConditionFalse,
			Reason:  "ModelPending",
			Message: "MISModel is not ready",
		})
		return true, nil
	}

	misService.Status.State = alphav1.MISServiceStateModelReady
	misService.Status.Model = misModel.Status.Model
	misService.Status.PVC = misModel.Status.PVC
	misService.Status.Envs = misModel.Spec.Envs
	misService.Status.Image = misModel.Spec.Image
	misService.Status.ImagePullSecret = misModel.Spec.ImagePullSecret
	meta.SetStatusCondition(&misService.Status.Conditions, metav1.Condition{
		Type:    alphav1.MISServiceConditionModelReady,
		Status:  metav1.ConditionTrue,
		Reason:  "ModelReady",
		Message: "MISModel is ready",
	})
	return false, nil
}

func (r *MISServiceReconciler) reconcileService(ctx context.Context, misService *alphav1.MISService) error {
	return nil
}

func (r *MISServiceReconciler) reconcileServiceMonitor(ctx context.Context, misService *alphav1.MISService) error {
	return nil
}

func (r *MISServiceReconciler) reconcileHPA(ctx context.Context, misService *alphav1.MISService) error {
	return nil
}

func (r *MISServiceReconciler) reconcileAcJob(ctx context.Context, misService *alphav1.MISService) (bool, error) {
	return false, nil
}

func (r *MISServiceReconciler) updateMISServiceStatus(ctx context.Context, misService *alphav1.MISService) error {

	obj := alphav1.MISService{}
	if err := r.Get(ctx, types.NamespacedName{Name: misService.Name, Namespace: misService.Namespace}, &obj); r != nil {
		if err != nil {
			return errors.Wrap(err, "Fetch MISService failed")
		}
	}

	patch := client.MergeFrom(obj.DeepCopy())
	obj.Status = (*misService).Status

	if err := r.Status().Patch(ctx, &obj, patch); err != nil {
		if err != nil {
			return errors.Wrap(err, "Update MISService failed")
		}
	}

	return nil
}

// SetupWithManager sets up the controller with the Manager.
func (r *MISServiceReconciler) SetupWithManager(mgr ctrl.Manager) error {
	r.recorder = mgr.GetEventRecorderFor("misservice-controller")
	return ctrl.NewControllerManagedBy(mgr).
		For(&alphav1.MISService{}).
		Named("misservice").
		Owns(&v1.Service{}).
		Owns(&monitorv1.ServiceMonitor{}).
		Owns(&v2beta2.HorizontalPodAutoscaler{}).
		Owns(ptr.To(getAcjobObject())).
		Complete(r)
}
