/*
Copyright 2025 Huawei Technologies Co., Ltd.
*/

package controller

import (
	"context"

	"k8s.io/apimachinery/pkg/runtime"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/log"

	"ascend.com/mis-operator/api/apps/alphav1"
)

// MISServiceReconciler reconciles a MISService object
type MISServiceReconciler struct {
	client.Client
	Scheme *runtime.Scheme
}

// +kubebuilder:rbac:groups=apps.ascend.com,resources=misservices,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=apps.ascend.com,resources=misservices/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=apps.ascend.com,resources=misservices/finalizers,verbs=update

// Reconcile is part of the main kubernetes reconciliation loop which aims to
// move the current state of the cluster closer to the desired state.
func (r *MISServiceReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	_ = log.FromContext(ctx)

	return ctrl.Result{}, nil
}

// SetupWithManager sets up the controller with the Manager.
func (r *MISServiceReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&alphav1.MISService{}).
		Named("misservice").
		Complete(r)
}
