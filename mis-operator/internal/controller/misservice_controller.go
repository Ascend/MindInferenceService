/*
Copyright 2025 Huawei Technologies Co., Ltd.
*/

package controller

import (
	"context"
	"fmt"
	"path/filepath"
	"time"

	"github.com/google/uuid"
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
	"sigs.k8s.io/controller-runtime/pkg/handler"
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
		MISServiceLabelPartOf: misService.Name,
	}
}

// +kubebuilder:rbac:groups=apps.ascend.com,resources=misservices,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=apps.ascend.com,resources=misservices/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=apps.ascend.com,resources=misservices/finalizers,verbs=update
// +kubebuilder:rbac:groups=apps.ascend.com,resources=mismodel,verbs=get;list;watch
// +kubebuilder:rbac:groups="",resources=secrets,verbs=get;list;watch
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
		misService.Status.Selector = fmt.Sprintf("%s=%s", MISServiceLabelPartOf, misService.Name)
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

	if err := r.checkTLSSecret(ctx, misService); err != nil {
		logger.Error(err, "Unable to check TLSSecret")
		return ctrl.Result{}, err
	}

	if err := r.checkMISModel(ctx, misService); err != nil {
		logger.Error(err, "Unable to check MISModel status")
		return ctrl.Result{}, err
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

// checkTLSSecret used to check if TLSSecret is set and exists, then check its type and content.
func (r *MISServiceReconciler) checkTLSSecret(ctx context.Context, misService *alphav1.MISService) error {
	if misService.Spec.TLSSecret == "" {
		return nil
	}

	tlsSecret := v1.Secret{}
	namespaceName := types.NamespacedName{Namespace: misService.Namespace, Name: misService.Spec.TLSSecret}
	if err := r.Get(ctx, namespaceName, &tlsSecret); err != nil {
		if client.IgnoreNotFound(err) != nil {
			return errors.Wrap(err, "Unable to fetch Secret")
		}
		return errors.Wrap(err, "TLSSecret not exist")
	}

	if tlsSecret.Type != v1.SecretTypeTLS {
		return errors.New(fmt.Sprintf("TLSSecret type is not %s", v1.SecretTypeTLS))
	}

	if _, ok := tlsSecret.Data["tls.crt"]; !ok {
		return errors.New("TLSSecret has no `tls.crt`")
	}

	if _, ok := tlsSecret.Data["tls.key"]; !ok {
		return errors.New("TLSSecret has no `tls.key`")
	}

	misService.Status.State = alphav1.MISServiceStateTLSSecretReady
	r.updateMISServiceStatusUtil(misService, metav1.ConditionTrue, alphav1.MISServiceConditionTLSSecretReady,
		"TLSSecretReady", "TLSSecret is ready")
	return nil
}

// checkMISModel check if MISModel exists, and copy its useful information to MISService.
func (r *MISServiceReconciler) checkMISModel(ctx context.Context, misService *alphav1.MISService) error {
	misModel := alphav1.MISModel{}
	namespaceName := types.NamespacedName{Namespace: misService.Namespace, Name: misService.Spec.MISModel}
	if err := r.Get(ctx, namespaceName, &misModel); err != nil {
		if client.IgnoreNotFound(err) != nil {
			return errors.Wrap(err, "Unable to fetch MISModel")
		}
		return errors.Wrap(err, "MISModel not exist")
	}

	if misModel.Status.State != alphav1.MISModelStateReady {
		r.updateMISServiceStatusUtil(misService, metav1.ConditionFalse, alphav1.MISServiceConditionModelReady,
			"ModelPending", "MISModel is not ready")
		return errors.New("MISModel not ready")
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
	return nil
}

// reconcileService is responsible for process ServiceSpec in MISService.
// It will create Service if Service with given name is not exist, and update status of MISService.
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

// constructService used to construct Service.
// It will expose inference port and metrics port for the Service, and use getStandardSelectorLabels to match pod.
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
				{
					Name: MISServiceMetricsPortName,
					Port: misService.Spec.ServiceSpec.MetricsPort,
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

// reconcileServiceMonitor used to construct ServiceMonitor.
// It helps create ServiceMonitor on Service to adjust the Prometheus scrape configuration to fetch metrics from pods
// that routed by the Service.
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

// constructServiceMonitor set Prometheus to scrape metrics from port MISServiceMetricsPortName of Service.
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
					Port: MISServiceMetricsPortName,
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

	acjobList := getAcjobListObject()
	if err := r.queryAcjobList(ctx, misService, &acjobList); err != nil {
		return false, err
	}

	if err := r.checkAcJobList(ctx, misService, &acjobList); err != nil {
		return false, errors.Wrap(err, "Check acjob list failed")
	}

	if query, err := r.scaleAcjobList(ctx, misService, &acjobList); err != nil {
		return false, errors.Wrap(err, "Scale acjob failed")
	} else if query {
		if err := r.queryAcjobList(ctx, misService, &acjobList); err != nil {
			return false, err
		}
	}

	if requeue, err := r.checkAcjobStatus(misService, &acjobList); err != nil {
		return false, errors.Wrap(err, "Unable to check acjob status")
	} else if requeue {
		return true, nil
	}

	return false, nil
}

func (r *MISServiceReconciler) checkAcJobList(
	ctx context.Context, misService *alphav1.MISService, acjobList *unstructured.UnstructuredList) error {

	validAcjobItems := acjobList.Items[:0]

	for _, acjob := range acjobList.Items {
		if completionTime, err := getAcjobCompletionTime(&acjob); err != nil {
			return errors.Wrap(err, "Unable to process acjob.status.completionTime")
		} else if !completionTime.IsZero() {
			if completionTime.Add(MISServiceAcjobDeleteLastTime * time.Second).After(time.Now()) {
				validAcjobItems = append(validAcjobItems, acjob)
				continue
			}
			err := r.deleteAcjob(ctx, misService, &acjob)
			if err != nil {
				return err
			}
		} else {
			validAcjobItems = append(validAcjobItems, acjob)
		}
	}

	acjobList.Items = validAcjobItems

	return nil
}

// return query and err
// query mean acjob instance changed, need query again to get the latest status
func (r *MISServiceReconciler) scaleAcjobList(ctx context.Context,
	misService *alphav1.MISService, acjobList *unstructured.UnstructuredList) (bool, error) {
	logger := log.FromContext(ctx)
	currentReplicas := len(acjobList.Items)
	targetReplicas := misService.Spec.Replicas
	if targetReplicas > currentReplicas {
		addNum := targetReplicas - currentReplicas
		logger.Info(fmt.Sprintf("Scale acjob, %d instance will be add", addNum))
		for i := 0; i < addNum; i++ {
			job := getAcjobObject()
			if err := r.constructAcjob(misService, &job); err != nil {
				return false, errors.Wrap(err, "Unable to construct Acjob")
			}
			if err := r.Create(ctx, &job); err != nil {
				return false, errors.Wrap(err, "Unable to create Acjob")
			}
			logger.Info(fmt.Sprintf("Create %d acjob succeeded", currentReplicas+i))
			r.recorder.Eventf(misService, v1.EventTypeNormal, "CreateAcjob",
				"Create %d's acjob succeeded", currentReplicas+i)
		}
	} else if targetReplicas < currentReplicas {
		delNum := currentReplicas - targetReplicas
		logger.Info(fmt.Sprintf("Scale acjob, %d instance will be del", delNum))
		var runningAcjobList []*unstructured.Unstructured
		delCnt := 0
		// 优先删除进入completions状态的
		for i := 0; i < currentReplicas && delCnt < delNum; i++ {
			completionTime, err := getAcjobCompletionTime(&acjobList.Items[i])
			if err != nil {
				return false, errors.Wrap(err, "Unable to process acjob.status.completionTime")
			} else if completionTime.IsZero() {
				runningAcjobList = append(runningAcjobList, &acjobList.Items[i])
				continue
			}
			if err := r.deleteAcjob(ctx, misService, &acjobList.Items[i]); err != nil {
				return false, err
			}
			delCnt++
		}
		// 然后删除正常running的
		for i := 0; i < len(runningAcjobList) && delCnt < delNum; i++ {
			if err := r.deleteAcjob(ctx, misService, runningAcjobList[i]); err != nil {
				return false, err
			}
			delCnt++
		}
	} else {
		return false, nil
	}
	return true, nil
}

func (r *MISServiceReconciler) constructAcjob(misService *alphav1.MISService, job *unstructured.Unstructured) error {
	acjobName := fmt.Sprintf("%s-%s", misService.Name, uuid.New().String()[:MISServiceAcjobNameSuffixLen])

	(*job).Object["metadata"] = map[string]interface{}{
		"name":      acjobName,
		"namespace": misService.Namespace,
		"labels":    r.constructAcjobLabels(misService),
	}

	(*job).Object["spec"] = map[string]interface{}{
		"schedulerName": MISServiceAcjobSchedulerName,
		"runPolicy": map[string]interface{}{
			"schedulingPolicy": map[string]interface{}{
				"minAvailable": ptr.To[int32](1),
				"queue":        "default",
			},
		},
		"successPolicy": MISServiceAcjobSuccessPolicy,
		"replicaSpecs": map[string]interface{}{
			MISServiceAcjobMaster: ptr.To(r.constructMasterReplicas(misService)),
		},
	}

	if err := ctrl.SetControllerReference(misService, job, r.Scheme); err != nil {
		return errors.Wrap(err, "Unable to set controller ref to acjob")
	}

	return nil
}

func (r *MISServiceReconciler) constructAcjobLabels(misService *alphav1.MISService) map[string]string {
	labels := r.getStandardLabels(misService)
	acjobLabels := constructAcjobLabelsFromServerInfo(&misService.Status.MISServerInfo)
	for key, value := range acjobLabels {
		labels[key] = value
	}
	return labels
}

func (r *MISServiceReconciler) constructAcjobSelectorLabels(misService *alphav1.MISService) map[string]string {
	selectorLabels := r.getStandardSelectorLabels(misService)
	acjobSelectorLabels := constructAcjobSelectorLabelsFromServerInfo(&misService.Status.MISServerInfo)
	for key, value := range acjobSelectorLabels {
		selectorLabels[key] = value
	}
	return selectorLabels
}

func (r *MISServiceReconciler) constructMasterReplicas(misService *alphav1.MISService) map[string]interface{} {
	nodeSelector := constructAcjobNodeSelectorFromServerInfo(&misService.Status.MISServerInfo)

	podSpec := v1.PodSpec{
		NodeSelector:                  nodeSelector,
		Containers:                    r.constructMasterContainer(misService),
		Volumes:                       r.constructVolumes(misService),
		TerminationGracePeriodSeconds: ptr.To[int64](MISServicePodGracePeriodSeconds),
		SecurityContext: &v1.PodSecurityContext{
			RunAsUser:  misService.Spec.UserID,
			RunAsGroup: misService.Spec.GroupID,
		},
	}

	// if ImagePullSecret got from mismodel, then set it to acjob’s running pod
	if misService.Status.ImagePullSecret != nil && *misService.Status.ImagePullSecret != "" {
		podSpec.ImagePullSecrets = []v1.LocalObjectReference{
			{Name: *misService.Status.ImagePullSecret},
		}
	}

	masterReplicas := map[string]interface{}{
		"replicas":      ptr.To[int32](1),
		"restartPolicy": v1.RestartPolicyNever,
		"template": v1.PodTemplateSpec{
			ObjectMeta: metav1.ObjectMeta{
				Labels: r.constructAcjobSelectorLabels(misService),
			},
			Spec: podSpec,
		},
	}

	return masterReplicas
}

func (r *MISServiceReconciler) constructMasterContainer(misService *alphav1.MISService) []v1.Container {
	return []v1.Container{
		{
			Name:  MISServiceAcjobContainerName,
			Image: misService.Status.Image,

			ImagePullPolicy: v1.PullIfNotPresent,
			Env:             r.constructMasterEnvs(misService),
			Ports: []v1.ContainerPort{
				{
					ContainerPort: misService.Spec.ServiceSpec.Port,
					Name:          MISServiceAcjobPortName,
				},
			},
			Resources:      constructAcjobResourceFromServerInfo(&misService.Status.MISServerInfo),
			VolumeMounts:   r.constructVolumeMounts(misService),
			ReadinessProbe: misService.Spec.ReadinessProbe,
			LivenessProbe:  misService.Spec.LivenessProbe,
			StartupProbe:   misService.Spec.StartupProbe,
			Stdin:          true,
			TTY:            true,
		},
	}
}

// constructMasterEnvs use envs from MISModel to construct envs for create acjob, some unavailable envs will be ignored,
// if TLSSecret is provided, TLS config will be added.
func (r *MISServiceReconciler) constructMasterEnvs(misService *alphav1.MISService) []v1.EnvVar {
	unavailableServiceEnvs := map[string]struct{}{
		"http_proxy":                    {},
		"https_proxy":                   {},
		"HTTP_PROXY":                    {},
		"HTTPS_PROXY":                   {},
		"TORCH_DEVICE_BACKEND_AUTOLOAD": {},
	}

	var envs []v1.EnvVar

	for _, env := range misService.Status.Envs {
		if _, ok := unavailableServiceEnvs[env.Name]; !ok {
			envs = append(envs, env)
		}
	}

	if misService.Spec.TLSSecret != "" {
		envs = append(envs, v1.EnvVar{
			Name:  MISEnvironmentTlsCert,
			Value: filepath.Join(MISServiceTLSPath, MISServiceTLSCert),
		})

		envs = append(envs, v1.EnvVar{
			Name:  MISEnvironmentTlsKey,
			Value: filepath.Join(MISServiceTLSPath, MISServiceTLSKey),
		})
	}

	return envs
}

// constructVolumeMounts construct volume mount config for creating acjob. Related to constructVolumes.
func (r *MISServiceReconciler) constructVolumeMounts(misService *alphav1.MISService) []v1.VolumeMount {
	volumeMounts := []v1.VolumeMount{
		{
			Name:      MISServiceVolumeModel,
			MountPath: MISModelPodMountPath,
		},
		{
			Name:      MISServiceVolumeTmpfs,
			MountPath: MISServiceVolumeTmpfsPath,
		},
		{
			Name:      MISServiceVolumeTime,
			MountPath: MISServiceVolumeTimePath,
		},
	}

	if misService.Spec.TLSSecret != "" {
		volumeMounts = append(volumeMounts, v1.VolumeMount{
			Name:      MISServiceVolumeTls,
			MountPath: filepath.Join(MISServiceTLSPath, MISServiceTLSCert),
			SubPath:   MISServiceTLSCert,
		})

		volumeMounts = append(volumeMounts, v1.VolumeMount{
			Name:      MISServiceVolumeTls,
			MountPath: filepath.Join(MISServiceTLSPath, MISServiceTLSKey),
			SubPath:   MISServiceTLSKey,
		})
	}

	return volumeMounts
}

// constructVolumeMounts construct volumes for creating acjob.
// Include model, shared memory, timezone, or tls path if TLSSecret exists.
func (r *MISServiceReconciler) constructVolumes(misService *alphav1.MISService) []v1.Volume {
	volumes := []v1.Volume{
		{
			Name: MISServiceVolumeModel,
			VolumeSource: v1.VolumeSource{
				PersistentVolumeClaim: &v1.PersistentVolumeClaimVolumeSource{
					ClaimName: misService.Status.PVC,
				},
			},
		},
		{
			Name: MISServiceVolumeTmpfs,
			VolumeSource: v1.VolumeSource{
				EmptyDir: &v1.EmptyDirVolumeSource{
					Medium: v1.StorageMediumMemory,
				},
			},
		},
		{
			Name: MISServiceVolumeTime,
			VolumeSource: v1.VolumeSource{
				HostPath: &v1.HostPathVolumeSource{
					Path: "/etc/localtime",
				},
			},
		},
	}

	if misService.Spec.TLSSecret != "" {
		volumes = append(volumes, v1.Volume{
			Name: MISServiceVolumeTls,
			VolumeSource: v1.VolumeSource{
				Secret: &v1.SecretVolumeSource{
					SecretName: misService.Spec.TLSSecret,
				},
			},
		})
	}

	return volumes
}

// checkAcjobStatus check status of acjob created by MISService and adjust status of MISService.
func (r *MISServiceReconciler) checkAcjobStatus(
	misService *alphav1.MISService, acjobList *unstructured.UnstructuredList) (requeue bool, err error) {
	totolNum := len(acjobList.Items)
	running, failed, pending := 0, 0, 0
	for _, acjob := range acjobList.Items {
		replicaStatuses, err := getAcjobReplicaStatuses(&acjob)
		if err != nil {
			return false, errors.Wrap(err, "Unable to process acjob.status.replicaStatuses")
		}
		masterStatus, ok := replicaStatuses[MISServiceAcjobMaster]
		if !ok {
			pending++
		} else if masterStatus.Active > 0 {
			running++
		} else if masterStatus.Failed > 0 {
			failed++
		} else {
			pending++
		}
	}
	if pending > 0 {
		misService.Status.State = alphav1.MISServiceStateWaiting
		r.updateMISServiceStatusUtil(misService, metav1.ConditionTrue, alphav1.MISServiceConditionAcjobReconciling,
			"AcjobReconciling", "At least one Acjob in waiting")
	} else {
		r.updateMISServiceStatusUtil(misService, metav1.ConditionFalse, alphav1.MISServiceConditionAcjobReconciling,
			"AcjobNotReconciling", "No Acjob in waiting")
	}
	if running > 0 {
		misService.Status.State = alphav1.MISServiceStateReady
		r.updateMISServiceStatusUtil(misService, metav1.ConditionTrue, alphav1.MISServiceConditionAcjobReady,
			"AcjobReady", "At least one Acjob in running")
	} else {
		r.updateMISServiceStatusUtil(misService, metav1.ConditionFalse, alphav1.MISServiceConditionAcjobReady,
			"AcjobNotReady", "No Acjob in running")
	}
	if failed > 0 {
		misService.Status.State = alphav1.MISServiceStateFailed
		r.updateMISServiceStatusUtil(misService, metav1.ConditionTrue, alphav1.MISServiceConditionAcjobFailed,
			"AcjobFailed", "At least one Acjob is failed")
	} else {
		r.updateMISServiceStatusUtil(misService, metav1.ConditionFalse, alphav1.MISServiceConditionAcjobFailed,
			"AcjobNotFailed", "No Acjob is failed")
	}
	misService.Status.Replicas = running
	misService.Status.Running = fmt.Sprintf("%d/%d", running, totolNum)
	if running != misService.Spec.Replicas {
		return true, nil
	}
	return false, nil
}

// updateMISServiceStatusUtil helps set status for MISService.
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

// updateMISServiceStatus use Patch to update MISService status efficiently.
func (r *MISServiceReconciler) updateMISServiceStatus(ctx context.Context, misService *alphav1.MISService) error {

	obj := alphav1.MISService{}
	if err := r.Get(
		ctx, types.NamespacedName{Name: misService.Name, Namespace: misService.Namespace}, &obj); err != nil {
		return errors.Wrap(err, "Fetch MISService failed")
	}

	patch := client.MergeFrom(obj.DeepCopy())
	obj.Status = (*misService).Status

	if err := r.Status().Patch(ctx, &obj, patch); err != nil {
		return errors.Wrap(err, "Update MISService failed")
	}

	return nil
}

// createIndexTLSSecretForService create index for TLSSecret to accelerate query.
func (r *MISServiceReconciler) createIndexTLSSecretForService(mgr ctrl.Manager) error {
	return mgr.GetFieldIndexer().IndexField(
		context.Background(),
		&alphav1.MISService{},
		"tlsSecret",
		func(o client.Object) []string {
			misservice, ok := o.(*alphav1.MISService)
			if !ok {
				return []string{}
			}
			return []string{misservice.Spec.TLSSecret}
		},
	)
}

// createIndexTLSSecretForService create index for MISModel to accelerate query.
func (r *MISServiceReconciler) createIndexMISModelForService(mgr ctrl.Manager) error {
	return mgr.GetFieldIndexer().IndexField(
		context.Background(),
		&alphav1.MISService{},
		"misModel",
		func(o client.Object) []string {
			misservice, ok := o.(*alphav1.MISService)
			if !ok {
				return []string{}
			}
			return []string{misservice.Spec.MISModel}
		},
	)
}

func (r *MISServiceReconciler) findMISServiceForIndexTLSSecret(ctx context.Context, obj client.Object) []ctrl.Request {
	return r.findMISServiceForIndex(ctx, obj, "tlsSecret")
}

func (r *MISServiceReconciler) findMISServiceForIndexMISModel(ctx context.Context, obj client.Object) []ctrl.Request {
	return r.findMISServiceForIndex(ctx, obj, "misModel")
}

// findMISServiceForIndex use index to query MISService. Must use with createIndexTLSSecretForService liked method.
// For example, if createIndexTLSSecretForService has been used to create index `tlsSecret` for column
// MISService.spec.TLSSecret, after register findMISServiceForIndex and index `tlsSecret` to Watch Secret,
// when Secret changes, this method will return MISService searched by Secret.Name.
func (r *MISServiceReconciler) findMISServiceForIndex(
	ctx context.Context, obj client.Object, index string) []ctrl.Request {

	var requests []ctrl.Request

	misservices := alphav1.MISServiceList{}
	if err := r.List(ctx, &misservices,
		client.InNamespace(obj.GetNamespace()),
		client.MatchingFields{index: obj.GetName()},
	); err == nil {
		for _, misservice := range misservices.Items {
			requests = append(requests, ctrl.Request{
				NamespacedName: types.NamespacedName{
					Namespace: misservice.Namespace,
					Name:      misservice.Name,
				},
			})
		}
	}

	return requests
}

// SetupWithManager sets up the controller with the Manager.
func (r *MISServiceReconciler) SetupWithManager(mgr ctrl.Manager) error {
	r.recorder = mgr.GetEventRecorderFor("misservice-controller")

	if err := r.createIndexTLSSecretForService(mgr); err != nil {
		return errors.Wrap(err, "Unable to build index of TLSSecret for MISService")
	}

	if err := r.createIndexMISModelForService(mgr); err != nil {
		return errors.Wrap(err, "Unable to build index of MISModel for MISService")
	}

	return ctrl.NewControllerManagedBy(mgr).
		For(&alphav1.MISService{}).
		Named("misservice").
		Watches(&v1.Secret{}, handler.EnqueueRequestsFromMapFunc(r.findMISServiceForIndexTLSSecret)).
		Watches(&alphav1.MISModel{}, handler.EnqueueRequestsFromMapFunc(r.findMISServiceForIndexMISModel)).
		Owns(&v1.Service{}).
		Owns(&monitorv1.ServiceMonitor{}).
		Owns(&v2beta2.HorizontalPodAutoscaler{}).
		Owns(ptr.To(getAcjobObject())).
		Complete(r)
}
