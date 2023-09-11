#!/usr/bin/env bash
while getopts ":b:k:f:z:p:r:h" opt; do
  case ${opt} in
  b) S3_BUCKET_NAME=$OPTARG ;;
  k) S3_KEY_NAME=$OPTARG ;;
  f) LAMBDA_FOLDER_NAME=$OPTARG ;;
  z) LAMBDA_ZIP_NAME=$OPTARG ;;
  h)
    echo "Use arguments -b [S3_BUCKET_NAME], -k [S3_KEY_NAME], -f [LAMBDA_FOLDER_NAME], -z [LAMBDA_ZIP_NAME]"
    exit 1
    ;;
  :)
    echo "Missing option argument for -$OPTARG" >&2
    exit 1
    ;;
  *)
    echo "Invalid option $OPTARG use -b [S3_BUCKET_NAME], -k [S3_KEY_NAME], -f [LAMBDA_FOLDER_NAME], -z [LAMBDA_ZIP_NAME]"
    exit 1
    ;;
  esac
done

if [ -z "$S3_BUCKET_NAME" ] || [ -z "$S3_KEY_NAME" ] || [ -z "$LAMBDA_FOLDER_NAME" ] || [ -z "$LAMBDA_ZIP_NAME" ]; then
  echo "Arguments -b,-k,-f,-z should be specified use -h for help"
  exit 1
fi

## zip and push all lambda code
cd "$LAMBDA_FOLDER_NAME" || exit 1
zip -r "../$LAMBDA_ZIP_NAME" ./* -x ./requirements.txt
cd ..
aws s3 cp "$LAMBDA_ZIP_NAME" "s3://$S3_BUCKET_NAME/$S3_KEY_NAME/$LAMBDA_ZIP_NAME"
rm "$LAMBDA_ZIP_NAME"
