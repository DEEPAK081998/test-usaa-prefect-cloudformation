#!/usr/bin/env bash
while getopts ":b:k:f:z:p:r:h" opt; do
  case ${opt} in
  b) S3_BUCKET_NAME=$OPTARG ;;
  k) S3_KEY_NAME=$OPTARG ;;
  p) REQUIREMENT_FILE_PATH=$OPTARG ;;
  r) REQUIREMENT_ZIP_NAME=$OPTARG ;;
  h)
    echo "Use arguments -b [S3_BUCKET_NAME], -k [S3_KEY_NAME], -p [REQUIREMENT_FILE_PATH], -r [REQUIREMENT_ZIP_NAME]"
    exit 1
    ;;
  :)
    echo "Missing option argument for -$OPTARG" >&2
    exit 1
    ;;
  *)
    echo "Invalid option $OPTARG use -b [S3_BUCKET_NAME], -k [S3_KEY_NAME], -p [REQUIREMENT_FILE_PATH], -r [REQUIREMENT_ZIP_NAME]"
    exit 1
    ;;
  esac
done

if [ -z "$S3_BUCKET_NAME" ] || [ -z "$S3_KEY_NAME" ] || [ -z "$REQUIREMENT_FILE_PATH" ] || [ -z "$REQUIREMENT_ZIP_NAME" ]; then
  echo "Arguments -b,-k,-p,-r should be specified use -h for help"
  exit 1
fi

# install then zip and push the required packages
if [ -n "$REQUIREMENT_FILE_PATH" ] && [ -n "$REQUIREMENT_ZIP_NAME" ]; then
  pip3 install virtualenv
  virtualenv env
  source env/bin/activate
  pip3 install --upgrade pip
  mkdir python
  pip3 install --target python -r "$REQUIREMENT_FILE_PATH"
  zip -r "$REQUIREMENT_ZIP_NAME" python
  aws s3 cp "$REQUIREMENT_ZIP_NAME" "s3://$S3_BUCKET_NAME/$S3_KEY_NAME/$REQUIREMENT_ZIP_NAME"
  rm -r python
  rm "$REQUIREMENT_ZIP_NAME"
  deactivate
  rm -r env
fi
