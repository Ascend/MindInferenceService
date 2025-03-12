# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
from typing import List, Counter

import prometheus_client
from vllm.config import VllmConfig
from vllm.engine.metrics_types import Stats
from vllm.engine.metrics import PrometheusStatLogger as VllmPrometheusStatLogger
from vllm.engine.metrics import build_1_2_5_buckets, build_1_2_3_5_8_buckets, SupportsMetricsInfo


class MisMetrics:
    labelname_finish_reason = "finished_reason"
    _gauge_cls = prometheus_client.Gauge
    _counter_cls = prometheus_client.Counter
    _histogram_cls = prometheus_client.Histogram

    def __init__(self, labelnames: List[str], vllm_config: VllmConfig):
        max_model_len = vllm_config.model_config.max_model_len

        self._init_system_info(labelnames)
        self._init_iteration_info(labelnames)

        # Request stats
        #   Latency
        self._init_request_latency_info(labelnames)
        #   Metadata
        self._init_request_metadata_info(labelnames, max_model_len)

    def _init_system_info(self, labelnames: List[str]):
        # System stats
        #   Scheduler State
        self.gauge_scheduler_running = self._gauge_cls(
            name="mis:num_requests_running",
            documentation="Number of requests currently running on GPU.",
            labelnames=labelnames,
            multiprocess_mode="sum")
        self.gauge_scheduler_waiting = self._gauge_cls(
            name="mis:num_requests_waiting",
            documentation="Number of requests waiting to be processed.",
            labelnames=labelnames,
            multiprocess_mode="sum")
        self.gauge_scheduler_swapped = self._gauge_cls(
            name="mis:num_requests_swapped",
            documentation="Number of requests swapped to CPU.",
            labelnames=labelnames,
            multiprocess_mode="sum")
        #   KV Cache Usage in %
        self.gauge_gpu_cache_usage = self._gauge_cls(
            name="mis:gpu_cache_usage_perc",
            documentation="GPU KV-cache usage. 1 means 100 percent usage.",
            labelnames=labelnames,
            multiprocess_mode="sum")
        self.gauge_cpu_cache_usage = self._gauge_cls(
            name="mis:cpu_cache_usage_perc",
            documentation="CPU KV-cache usage. 1 means 100 percent usage.",
            labelnames=labelnames,
            multiprocess_mode="sum")
        #   Prefix caching block hit rate
        self.gauge_cpu_prefix_cache_hit_rate = self._gauge_cls(
            name="mis:cpu_prefix_cache_hit_rate",
            documentation="CPU prefix cache block hit rate.",
            labelnames=labelnames,
            multiprocess_mode="sum")
        self.gauge_gpu_prefix_cache_hit_rate = self._gauge_cls(
            name="mis:gpu_prefix_cache_hit_rate",
            documentation="GPU prefix cache block hit rate.",
            labelnames=labelnames,
            multiprocess_mode="sum")

    def _init_iteration_info(self, labelnames: List[str]):
        # Iteration stats
        self.counter_num_preemption = self._counter_cls(
            name="mis:num_preemptions_total",
            documentation="Cumulative number of preemption from the engines.",
            labelnames=labelnames)
        self.counter_prompt_tokens = self._counter_cls(
            name="mis:prompt_tokens_total",
            documentation="Number of prefill tokens processed.",
            labelnames=labelnames)
        self.counter_generation_tokens = self._counter_cls(
            name="mis:generation_tokens_total",
            documentation="Number of generation tokens processed.",
            labelnames=labelnames)
        buckets = [1, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8096]
        self.histogram_iteration_tokens = self._histogram_cls(
            name="mis:iteration_tokens_total",
            documentation="Histogram of number of tokens per engine_step.",
            labelnames=labelnames,
            buckets=buckets)
        self.histogram_time_to_first_token = self._histogram_cls(
            name="mis:time_to_first_token_seconds",
            documentation="Histogram of time to first token in seconds.",
            labelnames=labelnames,
            buckets=[0.001, 0.005, 0.01, 0.02, 0.04, 0.06, 0.08, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0])
        self.histogram_time_per_output_token = self._histogram_cls(
            name="mis:time_per_output_token_seconds",
            documentation="Histogram of time per output token in seconds.",
            labelnames=labelnames,
            buckets=[0.01, 0.025, 0.05, 0.075, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.75, 1.0, 2.5])

    def _init_request_latency_info(self, labelnames: List[str]):
        request_latency_buckets = [0.3, 0.5, 0.8, 1.0, 1.5, 2.0, 2.5, 5.0, 10.0, 15.0, 20.0, 30.0, 40.0, 50.0, 60.0]
        self.histogram_e2e_time_request = self._histogram_cls(
            name="mis:e2e_request_latency_seconds",
            documentation="Histogram of end to end request latency in seconds.",
            labelnames=labelnames,
            buckets=request_latency_buckets)
        self.histogram_queue_time_request = self._histogram_cls(
            name="mis:request_queue_time_seconds",
            documentation="Histogram of time spent in WAITING phase for request.",
            labelnames=labelnames,
            buckets=request_latency_buckets)
        self.histogram_inference_time_request = self._histogram_cls(
            name="mis:request_inference_time_seconds",
            documentation="Histogram of time spent in RUNNING phase for request.",
            labelnames=labelnames,
            buckets=request_latency_buckets)
        self.histogram_prefill_time_request = self._histogram_cls(
            name="mis:request_prefill_time_seconds",
            documentation="Histogram of time spent in PREFILL phase for request.",
            labelnames=labelnames,
            buckets=request_latency_buckets)
        self.histogram_decode_time_request = self._histogram_cls(
            name="mis:request_decode_time_seconds",
            documentation="Histogram of time spent in DECODE phase for request.",
            labelnames=labelnames,
            buckets=request_latency_buckets)
        self.histogram_time_in_queue_request = self._histogram_cls(
            name="mis:time_in_queue_requests",
            documentation="Histogram of time the request spent in the queue in seconds.",
            labelnames=labelnames,
            buckets=request_latency_buckets)
        self.histogram_model_forward_time_request = self._histogram_cls(
            name="mis:model_forward_time_milliseconds",
            documentation="Histogram of time spent in the model forward pass in ms.",
            labelnames=labelnames,
            buckets=build_1_2_3_5_8_buckets(3000))
        self.histogram_model_execute_time_request = self._histogram_cls(
            name="mis:model_execute_time_milliseconds",
            documentation="Histogram of time spent in the model execute function in ms.",
            labelnames=labelnames,
            buckets=build_1_2_3_5_8_buckets(3000))

    def _init_request_metadata_info(self, labelnames: List[str], max_model_len: int):
        self.histogram_num_prompt_tokens_request = self._histogram_cls(
            name="mis:request_prompt_tokens",
            documentation="Number of prefill tokens processed.",
            labelnames=labelnames,
            buckets=build_1_2_5_buckets(max_model_len))
        self.histogram_num_generation_tokens_request = self._histogram_cls(
            name="mis:request_generation_tokens",
            documentation="Number of generation tokens processed.",
            labelnames=labelnames,
            buckets=build_1_2_5_buckets(max_model_len))
        self.histogram_max_num_generation_tokens_request = self._histogram_cls(
            name="mis:request_max_num_generation_tokens",
            documentation="Histogram of maximum number of requested generation tokens.",
            labelnames=labelnames,
            buckets=build_1_2_5_buckets(max_model_len))
        self.histogram_n_request = self._histogram_cls(
            name="mis:request_params_n",
            documentation="Histogram of the n request parameter.",
            labelnames=labelnames,
            buckets=[1, 2, 5, 10, 20])
        self.histogram_max_tokens_request = self._histogram_cls(
            name="mis:request_params_max_tokens",
            documentation="Histogram of the max_tokens request parameter.",
            labelnames=labelnames,
            buckets=build_1_2_5_buckets(max_model_len))
        self.counter_request_success = self._counter_cls(
            name="mis:request_success_total",
            documentation="Count of successfully processed requests.",
            labelnames=labelnames + [MisMetrics.labelname_finish_reason])


class MisPrometheusStatLogger(VllmPrometheusStatLogger):
    _metrics_cls = MisMetrics

    def log(self, stats: Stats):
        self._log_prometheus(stats)

    def _log_prometheus(self, stats: Stats) -> None:
        self._log_prometheus_system_info(stats)
        self._log_prometheus_iteration_info(stats)
        self._log_prometheus_request_info(stats)

    def _log_prometheus_system_info(self, stats: Stats):
        # System state data
        self._log_gauge(self.metrics.gauge_scheduler_running,
                        stats.num_running_sys)
        self._log_gauge(self.metrics.gauge_scheduler_swapped,
                        stats.num_swapped_sys)
        self._log_gauge(self.metrics.gauge_scheduler_waiting,
                        stats.num_waiting_sys)
        self._log_gauge(self.metrics.gauge_gpu_cache_usage,
                        stats.gpu_cache_usage_sys)
        self._log_gauge(self.metrics.gauge_cpu_cache_usage,
                        stats.cpu_cache_usage_sys)
        self._log_gauge(self.metrics.gauge_cpu_prefix_cache_hit_rate,
                        stats.cpu_prefix_cache_hit_rate)
        self._log_gauge(self.metrics.gauge_gpu_prefix_cache_hit_rate,
                        stats.gpu_prefix_cache_hit_rate)

    def _log_prometheus_iteration_info(self, stats: Stats):
        # Iteration level data
        self._log_counter(self.metrics.counter_num_preemption,
                          stats.num_preemption_iter)
        self._log_counter(self.metrics.counter_prompt_tokens,
                          stats.num_prompt_tokens_iter)
        self._log_counter(self.metrics.counter_generation_tokens,
                          stats.num_generation_tokens_iter)
        self._log_histogram(self.metrics.histogram_iteration_tokens,
                            [stats.num_tokens_iter])
        self._log_histogram(self.metrics.histogram_time_to_first_token,
                            stats.time_to_first_tokens_iter)
        self._log_histogram(self.metrics.histogram_time_per_output_token,
                            stats.time_per_output_tokens_iter)

    def _log_prometheus_request_info(self, stats: Stats):
        # Request level data
        # Latency
        self._log_histogram(self.metrics.histogram_e2e_time_request,
                            stats.time_e2e_requests)
        self._log_histogram(self.metrics.histogram_queue_time_request,
                            stats.time_queue_requests)
        self._log_histogram(self.metrics.histogram_inference_time_request,
                            stats.time_inference_requests)
        self._log_histogram(self.metrics.histogram_prefill_time_request,
                            stats.time_prefill_requests)
        self._log_histogram(self.metrics.histogram_decode_time_request,
                            stats.time_decode_requests)
        self._log_histogram(self.metrics.histogram_time_in_queue_request,
                            stats.time_in_queue_requests)
        self._log_histogram(self.metrics.histogram_model_forward_time_request,
                            stats.model_forward_time_requests)
        self._log_histogram(self.metrics.histogram_model_execute_time_request,
                            stats.model_execute_time_requests)
        # Metadata
        finished_reason_counter = Counter(stats.finished_reason_requests)
        self._log_counter_labels(self.metrics.counter_request_success,
                                 finished_reason_counter,
                                 MisMetrics.labelname_finish_reason)
        self._log_histogram(self.metrics.histogram_num_prompt_tokens_request,
                            stats.num_prompt_tokens_requests)
        self._log_histogram(self.metrics.histogram_num_generation_tokens_request,
                            stats.num_generation_tokens_requests)
        self._log_histogram(self.metrics.histogram_n_request,
                            stats.n_requests)
        self._log_histogram(self.metrics.histogram_max_num_generation_tokens_request,
                            stats.max_num_generation_tokens_requests)
        self._log_histogram(self.metrics.histogram_max_tokens_request,
                            stats.max_tokens_requests)
