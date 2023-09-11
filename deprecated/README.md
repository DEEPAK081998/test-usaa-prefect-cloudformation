## This folder contains all the files and folder which are not needed now

### Deprecated README Steps

### Jira Project Role Creation

Following are the steps to create project roles on Jira

1. From Jira console  
   `For all of the following procedures, you must be logged in as a user with the JIRA Administrators global
   permission.`
    1. Choose `Settings` > System.
    2. Select Project roles to open the Project Role Browser page.
    3. Click on Manage Default Members in the Operations column for the newly created Project Role.
    4. Click Edit under Default Users.
    5. Select the User Picker icon to the right of the Add user(s) to project role field.
    6. Click the Select button at the bottom of this dialog when you are finished adding users and then click
       the Add button. You now see a list of users on the right that are now included in this Project Role.

   Please follow
   https://confluence.atlassian.com/adminjiraserver075/managing-project-roles-935391162html#Managingprojectroles-project_role_add
   to add permission schemes etc. to project roles

2. Using rest api

   `For managing project roles via rest api, you must have an admin api token`

   Please follow
   https://developer.atlassian.com/cloud/jira/platform/rest/v2/api-group-project-roles/#api-rest-api-2-role-post
   to create a project role using rest api. It explains the request schema and response schema

### Jira API Token Generation

Following are the steps to generate a Jira api token

1. Log in to https://id.atlassian.com/manage/api-tokens.
2. Click Create API token.
3. From the dialog that appears, enter a memorable and concise Label for your token and click Create.
4. Click Copy to clipboard, then paste the token to your script, or elsewhere to save:

### Jira webhook Creation

Following are the steps to create a Jira webhook

1. From Jira console  
   `For all of the following procedures, you must be logged in as a user with the JIRA Administrators global
   permission.`
    1. Go to Jira administration console > System > Webhooks (in the Advanced section).
    2. You can also use the quick search (keyboard shortcut is .), then type 'webhooks'.
    3. Click Create a webhook.
    4. In the form that is shown, enter the details for your new webhook. For more information on this, see
       https://developer.atlassian.com/server/jira/platform/webhooks/#configuring-a-webhook.
    5. To register your webhook, click Create.

2. Using rest api  
   `For managing Jira webhooks via rest api, you must have an admin api token`  
   Please follow https://developer.atlassian.com/server/jira/platform/webhooks/#register-a-webhook to
   register webhooks on Jira.

### Push Prefect Base Image to ECR

   ```bash
   1. aws ecr create-repository --repository-name prefect-base

   2. docker pull prefecthq/prefect:0.15.13-python3.7

   3. aws ecr get-login-password --region 'region' | docker login --username AWS --password-stdin 'aws_account_id'.dkr.ecr.'region'.amazonaws.com

   4. docker tag prefecthq/prefect:0.15.13-python3.7 'aws_account_id'.dkr.ecr.'region'.amazonaws.com/prefect-base:0.15.13-python3.7

   'Please use the same image tag as downloaded from docker hub in order to maintain images on ECR easily.
   (as shown in the command above)'

   5. docker push 'aws_account_id'.dkr.ecr.'region'.amazonaws.com/prefect-base:0.15.13-python3.7
   ```

### Manual approval notification stack deployment steps [Deprecated]

Following are the steps to deploy a manual approval notification stack. This stack is not used anymore.

1. Upload the lambda functions zip files to S3 by following the steps below,
    ```bash
    bash scripts/lambdas/upload_lambda.sh -b 'prefect-{Environment}-bucket' -k 'lambda-functions' -f 'cloudformation/lambdas/create_approval_ticket_lambda' -z 'create-approval-ticket.zip' -p '/cloudformation/lambdas/requirements.txt' -r 'mdp-lambda-requirements.zip'

    bash scripts/lambdas/upload_lambda.sh -b 'prefect-{Environment}-bucket' -k 'lambda-functions' -f 'cloudformation/lambdas/update_codepipeline_status_lambda' -z 'update_codepipeline_status.zip'
    ```

2. Create a Jira Project Role to only allow a set of users to approve/reject a pipeline execution. Follow
   [Jira Project Role Steps](#jira-project-role-creation) to create a Jira project role

3. Deploy manual-approval-notification stack by using the following command
   #### Sandbox

    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name manual-approval-sandbox-stack --template-file cloudformation/manual_approval_notification/manual-approval-notification-stack.yml --parameter-overrides file://cloudformation/manual_approval_notification/manual-approval-notification-sandbox-parameters.json --capabilities CAPABILITY_IAM
    ```

   #### Beta

    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name manual-approval-beta-stack --template-file cloudformation/manual_approval_notification/manual-approval-notification-stack.yml --parameter-overrides file://cloudformation/manual_approval_notification/manual-approval-notification-beta-parameters.json --capabilities CAPABILITY_IAM
    ```

   #### Prod

    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name manual-approval-prod-stack --template-file cloudformation/manual_approval_notification/manual-approval-notification-stack.yml --parameter-overrides file://cloudformation/manual_approval_notification/manual-approval-notification-prod-parameters.json --capabilities CAPABILITY_IAM
    ```

4. Create a Jira api token by following [Jira api token generation steps](#jira-api-token-generation)

5. Fill in Jira Secrets (userEmail, apiToken) manually from AWS console in the AWSSecretsManager. The name of
   secret created while deployment above would be `{Environment}-manual-approval-jira-creds` where
   'Environment' is the deployment environment.

6. Create a Jira webhook to recieve events from jira.
   The url to be used while registering the webhook will be the URL of the API gateway created while
   deployment above. You can get the API gateway URL from console. The name of the gateway would be
   `${Environment}-manual-approval-rest-api` and the event for which Jira webhook should be registered is
   `comment_created`. Follow the steps mentioned in [Jira Webhook steps](#jira-webhook-creation) to create a
   jira webhook.

7. (Optional) If you want to update lambda functions any time after deployment, follow the steps below.

    1. Upload lambdas by following step 1 of the [pre deployment steps](#pre-deployment-steps).
    2. Update the lambda code by using the following CLI command,
    ```bash
    aws lambda update-function-code --function-name '<Lambda function name>' --s3-bucket '<S3 bucket name>' --s3-key '<Complete key including the zip file name>' --profile '<AWS profile to be used>'

    For example, aws lambda update-function-code --function-name 'sandbox-update-codepipeline-status-lambda' --s3-bucket 's3-bucket-name' --s3-key 'lambda-functions/update-codepipeline-status.zip'
    ```

   Function name of create-approval-ticket lambda is: "{Environment}-create-approval-ticket-lambda"  
   Function name of update-codepipeline-status lambda is: "{Environment}-update-codepipeline-status-lambda"  
   where 'Environment' is Deployment environment eg. 'sandbox'

### Main Deployment Steps

### Sandbox

#### Prefect [Deprecated]

1. Open the [prefect_config.yaml](cloudformation/prefect/prefect_config.yaml) and replace the subnets defined in them
   with subnets provided in `VPCPrivateServiceSubnetList` parameter value
2. Run the given command to deploy the application stack and execute the change set
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name prefect-sandbox-stack --template-file cloudformation/prefect/prefect-application-stack.yml --parameter-overrides file://cloudformation/prefect/prefect-application-sandbox-parameters.json --no-execute-changeset --capabilities CAPABILITY_IAM

    ```

3. Wait for stack to complete and then run the given command to
   copy [prefect_config.yaml](cloudformation/prefect/prefect_config.yaml) file in s3 bucket after stack is deployed
    ```bash
    aws s3 cp cloudformation/prefect/prefect_config.yaml s3://<S3_Bucket_Name>/configs/prefect_config.yaml
    ```

### Beta

#### Prefect [Deprecated]

1. Open the [prefect_config.yaml](cloudformation/prefect/prefect_config.yaml) and replace the subnets defined in them
   with subnets provided in `VPCPrivateServiceSubnetList` parameter value
2. Run the given command to deploy the application stack and execute the change set
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name prefect-beta-stack --template-file cloudformation/prefect/prefect-application-stack.yml --parameter-overrides file://cloudformation/prefect/prefect-application-beta-parameters.json --no-execute-changeset --capabilities CAPABILITY_IAM
    ```
3. Wait for stack to complete and then run the given command to
   copy [prefect_config.yaml](cloudformation/prefect/prefect_config.yaml) file in s3 bucket after stack is deployed
    ```bash
    aws s3 cp cloudformation/prefect/prefect_config.yaml s3://<S3_Bucket_Name>/configs/prefect_config.yaml
    ```

### Prod

#### Prefect [Deprecated]

1. Open the [prefect_config.yaml](cloudformation/prefect/prefect_config.yaml) and replace the subnets defined in them
   with subnets provided in `VPCPrivateServiceSubnetList` parameter value
2. Run the given command to deploy the application stack and execute the change set
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name prefect-prod-stack --template-file cloudformation/prefect/prefect-application-stack.yml --parameter-overrides file://cloudformation/prefect/prefect-application-prod-parameters.json --no-execute-changeset --capabilities CAPABILITY_IAM
    ```
3. Wait for stack to complete and then run the given command to
   copy [prefect_config.yaml](cloudformation/prefect/prefect_config.yaml) file in s3 bucket after stack is deployed
    ```bash
    aws s3 cp cloudformation/prefect/prefect_config.yaml s3://<S3_Bucket_Name>/configs/prefect_config.yaml
    ```

## Code Pipeline Deployment Steps

### Sandbox

#### Prefect Flows [Deprecated]

Before deploying prefect flows stack on any environment, make sure that the environment has a ECR repository
containing a prefect base image as prefect flows pipeline requires a 'PrefectBaseImageUri' parameter for
deployment. If there is no prefect base image, follow steps to
[push prefect base image to ECR](#push-prefect-base-image-to-ecr)

1. Run the given command to deploy the pipeline stack and execute the change set
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name prefect-flows-sandbox-pipeline --template-file cloudformation/code_pipeline/prefect_flows/prefect-flows-pipeline-stack.yml --parameter-overrides file://cloudformation/code_pipeline/prefect_flows/prefect-flows-sandbox-pipeline-parameters.json --capabilities CAPABILITY_IAM
    ```

### Beta

#### Prefect Flows [Deprecated]

Before deploying prefect flows stack on any environment, make sure that the environment has a ECR repository
containing a prefect base image as prefect flows pipeline requires a 'PrefectBaseImageUri' parameter for
deployment. If there is no prefect base image, follow steps to
[push prefect base image to ECR](#push-prefect-base-image-to-ecr)

1. Run the given command to deploy the pipeline stack and execute the change set
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name prefect-flows-beta-pipeline --template-file cloudformation/code_pipeline/prefect_flows/prefect-flows-pipeline-stack.yml --parameter-overrides file://cloudformation/code_pipeline/prefect_flows/prefect-flows-beta-pipeline-parameters.json --capabilities CAPABILITY_IAM
    ```

### Prod

#### Prefect Flows [Deprecated]

Before deploying prefect flows stack on any environment, make sure that the environment has a ECR repository
containing a prefect base image as prefect flows pipeline requires a 'PrefectBaseImageUri' parameter for
deployment. If there is no prefect base image, follow steps to
[push prefect base image to ECR](#push-prefect-base-image-to-ecr)

1. Run the given command to deploy the pipeline stack and execute the change set
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name prefect-flows-prod-pipeline --template-file cloudformation/code_pipeline/prefect_flows/prefect-flows-pipeline-stack.yml --parameter-overrides file://cloudformation/code_pipeline/prefect_flows/prefect-flows-prod-pipeline-parameters.json --capabilities CAPABILITY_IAM
    ```