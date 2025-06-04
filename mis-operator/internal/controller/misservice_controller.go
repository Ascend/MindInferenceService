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
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
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
			logger.Error(err, "Unable to fetch MISService")
			return ctrl.Result{}, err
		}

		logger.Info("MISService not exist, reconcile exit")
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
		return ctrl.Result{RequeueAfter: time.Minute}, nil
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
		return ctrl.Result{RequeueAfter: time.Minute}, nil
	}

	return ctrl.Result{}, nil
}

// return requeue and err.
// requeue means MISModel is not ready, controller need check again after one minute
func (r *MISServiceReconciler) checkMISModel(ctx context.Context, misService *alphav1.MISService) (bool, error) {
	misModel := alphav1.MISModel{}
	namespaceName := types.NamespacedName{Namespace: misService.Namespace, Name: misService.Spec.MISModel}
	if err := r.Get(ctx, namespaceName, &misModel); err != nil {
		if client.IgnoreNotFound(err) != nil {
			return false, errors.Wrap(err, "Unable to fetch MISModel")
		}
		return false, errors.Wrap(err, "MISModel not exist")
	}

	if misModel.Status.State != alphav1.MISModelStateReady {
		r.updateMISServiceStatusUtil(misService, metav1.ConditionFalse, alphav1.MISServiceConditionModelReady,
			"ModelPending", "MISModel is not ready")
		return true, nil
	}

	misService.Status.State = alphav1.MISServiceStateModelReady
	misService.Status.Model = misModel.Status.Model
	misService.Status.PVC = misModel.Status.PVC
	misService.Status.MISServerInfo = misModel.Status.MISServerInfo
	misService.Status.Envs = misModel.Spec.Envs
	misService.Status.Image = misModel.Spec.Image
	misService.Status.ImagePullSecret = misModel.Spec.ImagePullSecret
	r.updateMISServiceStatusUtil(misService, metav1.ConditionTrue, alphav1.MISServiceConditionModelReady,
		"ModelReady", "MISModel is ready")
	return false, nil
}

func (r *MISServiceReconciler) reconcileService(ctx context.Context, misService *alphav1.MISService) error {
	logger := log.FromContext(ctx)

	service := v1.Service{}
	namespacedName := types.NamespacedName{Namespace: misService.Namespace, Name: misService.Spec.ServiceSpec.Name}
	if err := r.Get(ctx, namespacedName, &service); err != nil {
		if client.IgnoreNotFound(err) != nil {
			return errors.Wrap(err, "Unable to fetch Service")
		}
		if err := r.constructService(misService, &service); err != nil {
			return errors.Wrap(err, "Unable to construct service")
		}
		if err := r.Create(ctx, &service); err != nil {
			return errors.Wrap(err, "Unable to create service")
		}
		logger.Info("Create service succeeded")
		r.recorder.Event(misService, v1.EventTypeNormal, "ServiceCreate", "Create service succeeded")
	}

	misService.Status.State = alphav1.MISServiceStateServiceCreated
	r.updateMISServiceStatusUtil(misService, metav1.ConditionTrue, alphav1.MISServiceConditionServiceCreated,
		"ServiceCreated", "service is created")

	return nil
}

func (r *MISServiceReconciler) constructService(misService *alphav1.MISService, service *v1.Service) error {
	*service = v1.Service{
		ObjectMeta: metav1.ObjectMeta{
			Namespace:   misService.Namespace,
			Name:        misService.Spec.ServiceSpec.Name,
			Labels:      r.getStandardLabels(misService),
			Annotations: misService.Spec.ServiceSpec.Annotations,
		},
		Spec: v1.ServiceSpec{
			Ports: []v1.ServicePort{
				{
					Name: MISServicePortName,
					Port: misService.Spec.ServiceSpec.Port,
				},
			},
			Selector: r.getStandardSelectorLabels(misService),
			Type:     misService.Spec.ServiceSpec.Type,
		},
	}
	if err := ctrl.SetControllerReference(misService, service, r.Scheme); err != nil {
		return errors.Wrap(err, "Unable to set controller ref to service")
	}
	return nil
}

func (r *MISServiceReconciler) reconcileServiceMonitor(ctx context.Context, misService *alphav1.MISService) error {
	if misService.Spec.HPA == nil {
		return nil
	}

	logger := log.FromContext(ctx)

	var serviceMonitor monitorv1.ServiceMonitor
	namespacedName := types.NamespacedName{Namespace: misService.Namespace, Name: misService.GetServiceMonitorName()}
	if err := r.Get(ctx, namespacedName, &serviceMonitor); err != nil {
		if client.IgnoreNotFound(err) != nil {
			return errors.Wrap(err, "Unable to fetch ServiceMonitor")
		}
		if err := r.constructServiceMonitor(misService, &serviceMonitor); err != nil {
			return errors.Wrap(err, "Unable to construct ServiceMonitor")
		}
		if err := r.Create(ctx, &serviceMonitor); err != nil {
			return errors.Wrap(err, "Unable to create ServiceMonitor")
		}
		logger.Info("Create service monitor succeeded")
		r.recorder.Event(misService, v1.EventTypeNormal, "ServiceMonitorCreate", "Create service monitor succeeded")
	}

	misService.Status.State = alphav1.MISServiceStateServiceMonitorCreated
	r.updateMISServiceStatusUtil(misService, metav1.ConditionTrue, alphav1.MISServiceConditionServiceMonitorCreated,
		"ServiceMonitorCreated", "service monitor is created")

	return nil
}

func (r *MISServiceReconciler) constructServiceMonitor(
	misService *alphav1.MISService, monitor *monitorv1.ServiceMonitor) error {
	*monitor = monitorv1.ServiceMonitor{
		ObjectMeta: metav1.ObjectMeta{
			Namespace: misService.Namespace,
			Name:      misService.GetServiceMonitorName(),
			Labels:    r.getStandardLabels(misService),
		},
		Spec: monitorv1.ServiceMonitorSpec{
			Endpoints: []monitorv1.Endpoint{
				{
					Port: MISServicePortName,
					Path: MISServiceAcjobMetricsUrl,
				},
			},
			NamespaceSelector: monitorv1.NamespaceSelector{
				MatchNames: []string{
					misService.Namespace,
				},
			},
			Selector: metav1.LabelSelector{
				MatchLabels: r.getStandardLabels(misService),
			},
		},
	}
	if err := ctrl.SetControllerReference(misService, monitor, r.Scheme); err != nil {
		return errors.Wrap(err, "Unable to set controller ref for ServiceMonitor")
	}
	return nil
}

func (r *MISServiceReconciler) reconcileHPA(ctx context.Context, misService *alphav1.MISService) error {
	if misService.Spec.HPA == nil {
		return nil
	}

	logger := log.FromContext(ctx)

	hpa := v2beta2.HorizontalPodAutoscaler{}
	namespacedName := types.NamespacedName{Namespace: misService.Namespace, Name: misService.GetHPAName()}
	if err := r.Get(ctx, namespacedName, &hpa); err != nil {
		if client.IgnoreNotFound(err) != nil {
			return errors.Wrap(err, "Unable to fetch hpa")
		}
		if err := r.constructHPA(ctx, misService, &hpa); err != nil {
			return errors.Wrap(err, "Unable to construct hpa")
		}
		if err := r.Create(ctx, &hpa); err != nil {
			return errors.Wrap(err, "Unable to create hpa")
		}
		logger.Info("Create HPA succeeded")
		r.recorder.Event(misService, v1.EventTypeNormal, "HPACreate", "Create HPA succeeded")
	}

	misService.Status.State = alphav1.MISServiceStateHPACreated
	r.updateMISServiceStatusUtil(misService, metav1.ConditionTrue, alphav1.MISServiceConditionHPACreated,
		"HPACreated", "hpa is created")

	return nil
}

func (r *MISServiceReconciler) constructHPA(
	ctx context.Context, misService *alphav1.MISService, hpa *v2beta2.HorizontalPodAutoscaler) error {
	*hpa = v2beta2.HorizontalPodAutoscaler{
		ObjectMeta: metav1.ObjectMeta{
			Namespace: misService.Namespace,
			Name:      misService.GetHPAName(),
			Labels:    r.getStandardLabels(misService),
		},
		Spec: v2beta2.HorizontalPodAutoscalerSpec{
			ScaleTargetRef: v2beta2.CrossVersionObjectReference{
				Kind:       misService.Kind,
				Name:       misService.Name,
				APIVersion: misService.APIVersion,
			},
			MinReplicas: &misService.Spec.HPA.MinReplicas,
			MaxReplicas: misService.Spec.HPA.MaxReplicas,
			Metrics:     r.resolveMetrics(ctx, misService),
			Behavior:    misService.Spec.HPA.Behavior,
		},
	}
	if err := ctrl.SetControllerReference(misService, hpa, r.Scheme); err != nil {
		return errors.Wrap(err, "Unable to set controller ref to hpa")
	}
	return nil
}

func (r *MISServiceReconciler) resolveMetrics(
	ctx context.Context, misService *alphav1.MISService) []v2beta2.MetricSpec {
	logger := log.FromContext(ctx)

	var metricSpecs []v2beta2.MetricSpec

	for _, metric := range *misService.Spec.HPA.Metrics {
		metricSpec, err := r.getMetricSpecFromMetric(metric)
		if err != nil {
			logger.Error(err, "Receive unsupported MetricsType")
			continue
		}
		metricSpecs = append(metricSpecs, metricSpec)
	}

	return metricSpecs
}

func (r *MISServiceReconciler) getMetricSpecFromMetric(metric alphav1.Metric) (v2beta2.MetricSpec, error) {

	value, err := resource.ParseQuantity(metric.Threshold)
	if err != nil {
		value = resource.MustParse("0")
	}

	metricSpec := v2beta2.MetricSpec{
		Type: v2beta2.PodsMetricSourceType,
		Pods: &v2beta2.PodsMetricSource{
			Target: v2beta2.MetricTarget{
				Type:         v2beta2.AverageValueMetricType,
				AverageValue: &value,
			},
		},
	}

	switch metric.Type {
	case alphav1.MetricsTypeRequestRate:
		metricSpec.Pods.Metric.Name = "http_requests_per_second"
	case alphav1.MetricsTypeWaitRequest:
		metricSpec.Pods.Metric.Name = "http_requests_wait_num"
	case alphav1.MetricsTypeCpuKVCacheUtilization:
		metricSpec.Pods.Metric.Name = "kv_cache_utilization_cpu"
	case alphav1.MetricsTypeAccKVCacheUtilization:
		metricSpec.Pods.Metric.Name = "kv_cache_utilization_accelerator"
	default:
		return metricSpec, errors.New("metric type is not allowed")
	}

	return metricSpec, nil
}

// return requeue and err.
// requeue mean acjob is inconsistent with target state, controller need reconcile after one minute.
func (r *MISServiceReconciler) reconcileAcJob(ctx context.Context, misService *alphav1.MISService) (bool, error) {
	return false, nil
}

func (r *MISServiceReconciler) updateMISServiceStatusUtil(
	misService *alphav1.MISService, status metav1.ConditionStatus, t, reason, message string) {
	meta.SetStatusCondition(&misService.Status.Conditions, metav1.Condition{
		Type: t, Status: status, Reason: reason, Message: message,
	})
}

func (r *MISServiceReconciler) queryAcjobList(
	ctx context.Context, misService *alphav1.MISService, acjobList *unstructured.UnstructuredList) error {
	if err := r.List(
		ctx, acjobList,
		client.InNamespace(misService.Namespace),
		client.MatchingLabels(r.getStandardLabels(misService)),
	); err != nil {
		if client.IgnoreNotFound(err) != nil {
			return errors.Wrap(err, "Unable to fetch acjob list")
		}
	}

	return nil
}

func (r *MISServiceReconciler) deleteAcjob(
	ctx context.Context, misService *alphav1.MISService, acjob *unstructured.Unstructured) error {

	logger := log.FromContext(ctx)

	if err := r.Delete(ctx, acjob); err != nil {
		return errors.Wrap(err, "Unable to delete Acjob")
	}

	logger.Info(fmt.Sprintf("Delete acjob: %s succeeded", acjob.GetName()))
	r.recorder.Eventf(misService, v1.EventTypeNormal, "DeleteAcjob",
		"Delete acjob: %s succeeded", acjob.GetName())

	return nil
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
