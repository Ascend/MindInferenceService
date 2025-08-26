/*
Copyright 2025 Huawei Technologies Co., Ltd.
*/

// Package main is the entrypoint of mis operator
package main

import (
	"flag"
	"os"
	"strings"

	// Import all Kubernetes client auth plugins (e.g. Azure, GCP, OIDC, etc.)
	// to ensure that exec-entrypoint and run can make use of them.
	_ "k8s.io/client-go/plugin/pkg/client/auth"

	"github.com/prometheus-operator/prometheus-operator/pkg/apis/monitoring/v1"
	"k8s.io/apimachinery/pkg/runtime"
	utilruntime "k8s.io/apimachinery/pkg/util/runtime"
	"k8s.io/client-go/kubernetes/scheme"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/healthz"
	"sigs.k8s.io/controller-runtime/pkg/log/zap"
	"sigs.k8s.io/controller-runtime/pkg/metrics/server"

	"hiascend.com/mis-operator/api/apps/alphav1"
	"hiascend.com/mis-operator/internal/controller"
	"hiascend.com/mis-operator/internal/utils"
)

// ControllerParams indicates all params need for start mis-controller
type ControllerParams struct {
	enableLeaderElection bool
	probeAddr            string
	networkInterface     string
	opts                 zap.Options
}

var (
	// BuildName show app name
	BuildName string
	// BuildVersion show app version
	BuildVersion string
)

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
	flag.StringVar(&params.probeAddr,
		"health-probe-bind-address", ":8081", "The address the probe endpoint binds to.")
	flag.StringVar(&params.networkInterface,
		"network-interface", "eth0", "The network interface to query ipv4 ip.")
	flag.BoolVar(&params.enableLeaderElection, "leader-elect", false,
		"Enable leader election for controller manager. "+
			"Enabling this will ensure there is only one active controller manager.")
	params.opts = zap.Options{}
	params.opts.BindFlags(flag.CommandLine)
	flag.Parse()
}

func createManager(params *ControllerParams) (ctrl.Manager, error) {
	// BindAddress set to "0" to disable metrics service
	metricsServerOptions := server.Options{
		BindAddress: "0",
	}

	mgr, err := ctrl.NewManager(ctrl.GetConfigOrDie(), ctrl.Options{
		Scheme:                        setupScheme,
		Metrics:                       metricsServerOptions,
		HealthProbeBindAddress:        params.probeAddr,
		LeaderElection:                params.enableLeaderElection,
		LeaderElectionID:              "a91c60cd.hiascend.com",
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

	setupLog.Info("Start %s version: %s", BuildName, BuildVersion)

	if strings.HasPrefix(params.probeAddr, ":") {
		if ip, err := utils.GetIPv4ByInterface(params.networkInterface); err != nil {
			setupLog.Error(err, "unable to query a valid ipv4 address, "+
				"Please specify a valid address using the `--health-prob-bind-address` flag in the format `ip:port`, "+
				"or set a valid network interface using the `--network-interface` flag.")
			os.Exit(1)
		} else {
			params.probeAddr = ip + params.probeAddr
		}
	}

	var err error

	var mgr ctrl.Manager
	if mgr, err = createManager(&params); err != nil {
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

	if err := mgr.AddHealthzCheck("healthz", healthz.Ping); err != nil {
		setupLog.Error(err, "unable to set up health check for mis-operator")
		os.Exit(1)
	}

	if err := mgr.AddReadyzCheck("readyz", healthz.Ping); err != nil {
		setupLog.Error(err, "unable to set up ready check for mis-operator")
		os.Exit(1)
	}

	if err := mgr.Start(ctrl.SetupSignalHandler()); err != nil {
		setupLog.Error(err, "problem running manager")
		os.Exit(1)
	}
}
