workdir=$(
  cd $(dirname $0)
  pwd
)

export PYTHONPATH=$PYTHONPATH:$workdir

if [ -v MIS_LOG_LEVEL ]; then
  export VLLM_LOGGING_LEVEL=$MIS_LOG_LEVEL
fi

function run_vllm() {
  source /usr/local/Ascend/ascend-toolkit/set_env.sh
  source /usr/local/Ascend/nnal/atb/set_env.sh

  python3 -m mis.llm.entrypoints.launcher
}

run_vllm
