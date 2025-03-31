workdir=$(
  cd $(dirname $0)
  pwd
)

export PYTHONPATH=$PYTHONPATH:$workdir

function run_vllm() {
  python3 -m mis.run
}

run_vllm
