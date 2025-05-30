/*
Copyright 2025 Huawei Technologies Co., Ltd.
*/

// Package main is the entrypoint of mis operator
package main

import (
	"crypto/tls"
	"flag"
	"os"
	"path/filepath"

	// Import all Kubernetes client auth plugins (e.g. Azure, GCP, OIDC, etc.)
	// to ensure that exec-entrypoint and run can make use of them.
	_ "k8s.io/client-go/plugin/pkg/client/auth"

	"github.com/prometheus-operator/prometheus-operator/pkg/apis/monitoring/v1"
	"k8s.io/apimachinery/pkg/runtime"
	utilruntime "k8s.io/apimachinery/pkg/util/runtime"
	"k8s.io/client-go/kubernetes/scheme"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/certwatcher"
	"sigs.k8s.io/controller-runtime/pkg/healthz"
	"sigs.k8s.io/controller-runtime/pkg/log/zap"
	"sigs.k8s.io/controller-runtime/pkg/metrics/filters"
	"sigs.k8s.io/controller-runtime/pkg/metrics/server"

	"ascend.com/mis-operator/api/apps/alphav1"
	"ascend.com/mis-operator/internal/controller"
)

// ControllerParams indicates all params need for start mis-controller
type ControllerParams struct {
	metricsAddr          string
	metricsCertPath      string
	metricsCertName      string
	metricsCertKey       string
	enableLeaderElection bool
	probeAddr            string
	secureMetrics        bool
	opts                 zap.Options
}

var (
	setupScheme = runtime.NewScheme()
	setupLog    = ctrl.Log.WithName("setup")
)

func init() {
	utilruntime.Must(scheme.AddToScheme(setupScheme))

	utilruntime.Must(v1.AddToScheme(setupScheme))
	utilruntime.Must(alphav1.AddToScheme(setupScheme))
}

func parseParams(params *ControllerParams) {
	flag.StringVar(&params.metricsAddr, "metrics-bind-address", "0",
		"The address the metrics endpoint binds to. "+
			"Use :8443 for HTTPS or :8080 for HTTP, or leave as 0 to disable the metrics service.")
	flag.StringVar(&params.probeAddr,
		"health-probe-bind-address", ":8081", "The address the probe endpoint binds to.")
	flag.BoolVar(&params.enableLeaderElection, "leader-elect", false,
		"Enable leader election for controller manager. "+
			"Enabling this will ensure there is only one active controller manager.")
	flag.BoolVar(&params.secureMetrics, "metrics-secure", true,
		"If set, the metrics endpoint is served securely via HTTPS. Use --metrics-secure=false to use HTTP instead.")
	flag.StringVar(&params.metricsCertPath,
		"metrics-cert-path", "", "The directory that contains the metrics server certificate.")
	flag.StringVar(&params.metricsCertName,
		"metrics-cert-name", "tls.crt", "The name of the metrics server certificate file.")
	flag.StringVar(&params.metricsCertKey,
		"metrics-cert-key", "tls.key", "The name of the metrics server key file.")
	params.opts = zap.Options{
		Development: true,
	}
	params.opts.BindFlags(flag.CommandLine)
	flag.Parse()
}

func createMetricsCertWatcher(params *ControllerParams, metricsCertWatcher **certwatcher.CertWatcher) error {
	setupLog.Info("Initializing metrics certificate watcher using provided certificates",
		"metrics-cert-path", params.metricsCertPath,
		"metrics-cert-name", params.metricsCertName,
		"metrics-cert-key", params.metricsCertKey)

	var err error
	*metricsCertWatcher, err = certwatcher.New(
		filepath.Join(params.metricsCertPath, params.metricsCertName),
		filepath.Join(params.metricsCertPath, params.metricsCertKey),
	)
	if err != nil {
		setupLog.Error(err, "to initialize metrics certificate watcher", "error", err)
		return err
	}
	return nil
}

func createManager(params *ControllerParams, metricsCertWatcher *certwatcher.CertWatcher) (ctrl.Manager, error) {
	var tlsOpts []func(*tls.Config)

	// disable http/2
	disableHTTP2 := func(c *tls.Config) {
		setupLog.Info("disabling http/2")
		c.NextProtos = []string{"http/1.1"}
	}
	tlsOpts = append(tlsOpts, disableHTTP2)

	metricsServerOptions := server.Options{
		BindAddress: params.metricsAddr, SecureServing: params.secureMetrics, TLSOpts: tlsOpts}

	if params.secureMetrics {
		metricsServerOptions.FilterProvider = filters.WithAuthenticationAndAuthorization
	}

	if len(params.metricsCertPath) > 0 {
		metricsServerOptions.TLSOpts = append(metricsServerOptions.TLSOpts, func(config *tls.Config) {
			config.GetCertificate = metricsCertWatcher.GetCertificate
		})
	}

	mgr, err := ctrl.NewManager(ctrl.GetConfigOrDie(), ctrl.Options{
		Scheme:                        setupScheme,
		Metrics:                       metricsServerOptions,
		HealthProbeBindAddress:        params.probeAddr,
		LeaderElection:                params.enableLeaderElection,
		LeaderElectionID:              "a91c60cd.ascend.com",
		LeaderElectionReleaseOnCancel: true,
	})
	if err != nil {
		setupLog.Error(err, "unable to start manager")
		return nil, err
	}

	return mgr, nil
}

func main() {
	var params ControllerParams
	parseParams(&params)

	ctrl.SetLogger(zap.New(zap.UseFlagOptions(&params.opts)))
	var err error

	var metricsCertWatcher *certwatcher.CertWatcher
	if len(params.metricsCertPath) > 0 {
		if err = createMetricsCertWatcher(&params, &metricsCertWatcher); err != nil {
			os.Exit(1)
		}
	}

	var mgr ctrl.Manager
	if mgr, err = createManager(&params, metricsCertWatcher); err != nil {
		os.Exit(1)
	}

	if err = (&controller.MISServiceReconciler{
		Client: mgr.GetClient(),
		Scheme: mgr.GetScheme(),
	}).SetupWithManager(mgr); err != nil {
		setupLog.Error(err, "unable to create controller", "controller", "MISService")
		os.Exit(1)
	}

	if err = (&controller.MISModelReconciler{
		Client: mgr.GetClient(),
		Scheme: mgr.GetScheme(),
	}).SetupWithManager(mgr); err != nil {
		setupLog.Error(err, "unable to create controller", "controller", "MISModel")
		os.Exit(1)
	}

	if metricsCertWatcher != nil {
		setupLog.Info("Adding metrics certificate watcher to manager")
		if err := mgr.Add(metricsCertWatcher); err != nil {
			setupLog.Error(err, "unable to add metrics certificate watcher to manager")
			os.Exit(1)
		}
	}

	if err := mgr.AddHealthzCheck("healthz", healthz.Ping); err != nil {
		setupLog.Error(err, "unable to set up health check for mis-operator")
		os.Exit(1)
	}

	if err := mgr.AddReadyzCheck("readyz", healthz.Ping); err != nil {
		setupLog.Error(err, "unable to set up ready check for mis-operator")
		os.Exit(1)
	}

	setupLog.Info("starting mis-operator manager")
	if err := mgr.Start(ctrl.SetupSignalHandler()); err != nil {
		setupLog.Error(err, "problem running manager")
		os.Exit(1)
	}
}
