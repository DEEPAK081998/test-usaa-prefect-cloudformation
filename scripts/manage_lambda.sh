#!/bin/bash

# Script to manage lambdas

upload_lambda_layer() {
  echo "[INFO] Uploading Lambda layer for file $req_file"
  /bin/bash scripts/lambdas/upload_layer.sh -b "${MDP_BUCKET}" -k "${LAMBDA_LAYER_S3_PATH}" -p "$req_file" -r "${base_dir}_layer.zip"
  aws s3 cp $req_file s3://"$s3_req_file_path"/"$s3_req_file"
  echo "[INFO] Lambda layer uploaded successfully"
}

for dir in ${CODEBUILD_SRC_DIR}/lambdas/*; do
  if [ -d $dir ]; then
    base_dir=$(basename $dir)
    req_file="lambdas/$base_dir/requirements.txt"
    s3_req_file="${base_dir}_requirements.txt"
    s3_req_file_path="${MDP_BUCKET}/${LAMBDA_LAYER_S3_PATH}/requirement-files"
    echo "[INFO] Uploading Lambda code for folder $base_dir"
    /bin/bash scripts/lambdas/upload_lambda.sh -b ${MDP_BUCKET} -k ${LAMBDA_CODE_S3_PATH} -f "lambdas/$base_dir" -z "$base_dir.zip"
    echo "[INFO] Lambda code uploaded successfully"
    if [ -f "$req_file" ]; then
      if aws s3 cp s3://"$s3_req_file_path"/"$s3_req_file" /tmp/"$s3_req_file" 2>&1 | grep -q "404"; then
        upload_lambda_layer
      else
        if [ "$(diff $req_file /tmp/$s3_req_file)" != "" ]; then
          upload_lambda_layer
        else
          echo "[INFO] Skipping layer upload because of no change in requirement file $req_file"
        fi
      fi
    fi
  fi
done
