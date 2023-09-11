#!/bin/bash

# Script to update all/selected pipelines

# Defaults
environment="sandbox"
project="vast_re"
region="us-east-1"
pipeline_stacks=""
extra_kwargs=""
s3_bucket_name=""
s3_prefix="cloudformation_stacks/templates"
usage="
Bash script to update all/selected pipelines
/bin/bash pipelines_deploy.sh [OPTIONS]
--environment    Environment in which to deploy
--project        Project to use
--region         AWS region
--pipline_stack  List of stacks to deploy
                 Note: Provide either environment or list of stacks not BOTH
                       if provided pipeline_stack will be picked on priority
--extra_kwargs   Extra AWS kwargs needed for deployment
"

# parse all additional arguments
while (($# >= 1)); do
  case $1 in
  --environment) environment="$2" ;;
  --project) project="$2" ;;
  --region) region="$2" ;;
  --pipeline-stacks) pipeline_stacks="$2" ;;
  --extra-kwargs) extra_kwargs="$2" ;;
  --s3-bucket-name) s3_bucket_name="$2" ;;
  --s3-prefix) s3_prefix="$2" ;;  
  --help)
    echo "${usage}"
    exit 0
    ;;
  *)
    echo "${usage}"
    exit 1
    ;;
  esac
  shift 2
done

# adds stack names to list based on environment or pipeline-stacks
if [[ -z "${pipeline_stacks}" ]]; then
  stack_names_array=("mdp-workflow-${environment}-pipeline" "mdp-${environment}-pipeline" "airbyte-connectors-${environment}-pipeline" "airbyte-updates-${environment}-pipeline")
else
  stack_names_array=($pipeline_stacks)
fi

# loop over array and deploy selected stacks
for stack_name in "${stack_names_array[@]}"; do
  echo "Triggering ${stack_name} stack"
  if [[ "${stack_name}" == "mdp-workflow-${environment}-pipeline" ]]; then
    aws cloudformation deploy --region "${region}" --stack-name "${stack_name}" --template-file cloudformation/code_pipeline/mdp_workflow_stack/mdp-workflow-pipeline-stack.yml --parameter-overrides file://cloudformation/code_pipeline/mdp_workflow_stack/"${project}"/mdp-workflow-pipeline-"${environment}"-parameters.json --s3-bucket $s3_bucket_name --s3-prefix $s3_prefix --capabilities CAPABILITY_IAM $extra_kwargs
  elif [[ "${stack_name}" == "mdp-${environment}-pipeline" ]]; then
    aws cloudformation deploy --region "${region}" --stack-name "${stack_name}" --template-file cloudformation/code_pipeline/cloudformation_stack/mdp-pipeline-stack.yml --parameter-overrides file://cloudformation/code_pipeline/cloudformation_stack/"${project}"/mdp-"${environment}"-pipeline-parameters.json --s3-bucket $s3_bucket_name --s3-prefix $s3_prefix --capabilities CAPABILITY_IAM $extra_kwargs
  elif [[ "${stack_name}" == "airbyte-connectors-${environment}-pipeline" ]]; then
    aws cloudformation deploy --region "${region}" --stack-name "${stack_name}" --template-file cloudformation/code_pipeline/airbyte_connectors/airbyte-connectors-pipeline-stack.yml --parameter-overrides file://cloudformation/code_pipeline/airbyte_connectors/"${project}"/airbyte-connectors-"${environment}"-pipeline-parameters.json --s3-bucket $s3_bucket_name --s3-prefix $s3_prefix --capabilities CAPABILITY_IAM $extra_kwargs
  elif [[ "${stack_name}" == "airbyte-updates-${environment}-pipeline" ]]; then
    aws cloudformation deploy --region "${region}" --stack-name airbyte-updates-"${environment}"-pipeline --template-file cloudformation/code_pipeline/airbyte_updates/airbyte-updates-pipeline-stack.yml --parameter-overrides file://cloudformation/code_pipeline/airbyte_updates/"${project}"/airbyte-updates-"${environment}"-pipeline-parameters.json --s3-bucket $s3_bucket_name --s3-prefix $s3_prefix --capabilities CAPABILITY_IAM $extra_kwargs
  fi
  echo "================================================================="
done
