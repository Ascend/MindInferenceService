workdir=$(
  cd $(dirname $0)
  pwd
)

model_name=$1
version=$2

typeset -l model_name_lower
model_name_lower=$model_name

echo "building image ${model_name_lower}:${version}"

docker_build_dir=$workdir/dockerfiles/llm/build
mkdir -p $docker_build_dir
cp -r $workdir/mis $docker_build_dir
cp -r $workdir/requirements.txt $docker_build_dir
cp -r $workdir/run.sh $docker_build_dir

cd $workdir/dockerfiles/llm

raw_model_name="\"MIS_MODEL\": lambda: \"MindSDK/DeepSeek-R1-Distill-Qwen-7B\""
new_model_name="\"MIS_MODEL\": lambda: \"MindSDK/${model_name}\""
sed -i "s|${raw_model_name}|${new_model_name}|g" build/mis/envs.py

docker build --build-arg MODEL=$model_name -t $model_name_lower:$version .