# README

This Repo is for managing manage-data-pipeline resources using cloudformation stack.

## Local Setup

1. **Python Installation:**
    - **Option 1:**
        1. Update local repositories:
            ```bash
            sudo apt update
            ```
        2. Install the supporting software:
            ```bash
            sudo apt install build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev
            libreadline-dev libffi-dev
            ```
        3. Download Gzipped source tarball of python version 3.10.9
           from [here](https://www.python.org/downloads/release/python-3109/)
        4. Extract the file using tar:
            ```bash
            tar -xf Python-3.10.9.tgz
            ```
        5. Test System and Optimize Python:
            ```bash
            cd Python-3.10.9
            ./configure --enable-optimizations
            ```
           Note: This step can take up to 30 minutes to complete.
        6. Install the Python binaries by running the following command:
            ```bash
            sudo make altinstall
            ```
        7. Check python version:
            ```bash
            python3.10 --version
            ```
    - **Option 2:**
        1. Update local repositories:
            ```bash
            sudo apt update
            ```
        2. Install the supporting software:
            ```bash
            sudo apt install software-properties-common
            ```
        3. Add Deadsnakes PPA:

            ```bash
            sudo add-apt-repository ppa:deadsnakes/ppa

            sudo apt update
            ```
        4. Install Python:
            ```bash
            sudo apt install python3.10
            ```
           Note: This step can take up to 30 minutes to complete.
        5. Check python version:
            ```bash
            python3.10 --version
            ```

2. **Environment Setup:**  
   Use below set of commands to create virtual environment or use any other preferred method
    1. `sudo pip install virtualenv`
    2. `sudo pip install virtualenvwrapper`
    3. `export WORKON_HOME=~/Envs`
    4. `mkdir -p $WORKON_HOME`
    5. `source /usr/local/bin/virtualenvwrapper.sh`
    6. `mkvirtualenv -p python3.7 env1`
    7. `workon env1`
    8. `deactivate`

    - **Note:** Put line 3 and 5 in ~/.bashrc

3. **Project Setup:**
    1. Install requirements.txt :`pip install -r requirments.txt`
    2. Install [aws cli](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html)
    3. download
       [chrome extension]
       (https://chrome.google.com/webstore/detail/saml-to-aws-sts-keys-conv/ekniobabpcnfjgfbphhcolcinmnbehde?hl=en)
       or [firefox extension](https://addons.mozilla.org/en-US/firefox/addon/saml-to-aws-sts-keys/) to download the
       aws [credentials](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html) file on your
       system (optional)

## Stack Deployment Steps

### Token Generation

The Airbyte application stack parameters needs client id and secret, Follow below steps to generate them:

1. Go to the Google [API Console](https://console.developers.google.com) and switch to the HSR account if not already
2. On the left panel choose *Credentials*
3. on the top panel choose to *Create Credentials*
4. Select *OAuth client ID*
5. Select *Web application* in the Application type
6. In *Authorized JavaScript origins* add the following URLs:
    1. `https://airbyte-<Environment>.<Hosted Zone Name>`
7. In Authorized redirect URIs add the following URLs:
    1. `https://airbyte-<Environment>.<Hosted Zone Name>/oauth2/idpresponse`
    2. `https://airbyte-infra-<BusinessUnit>-<Environment>-airbyte.auth.<AWS Region>.amazoncognito.com/oauth2/idpresponse`
8. Choose Save.
9. Download the OAuth client json file
10. The Json fill will contain the client id and secret

Note: The variable define above are as follows

1. Environment: The environment in which the stack is deployed
2. Hosted Zone Name: The `HostedZoneName` parameter value define in airbyte parameter file for that particular
   environment
3. AWS Region: The AWS Region where stack is deployed
4. BusinessUnit: Business unit

### EC2 Initial Configuration

To set up Airbyte in EC2 instance ssh into machine and follow below steps:

1. make sure that user data has fully run. to make sure that run the given command and check for final output it should
   be similar to `All initial setup Done!!`. Wait till the command give the required output.
    ```bash
    sudo cat /var/log/cloud-init-output.log
    ```
2. run the following command `sudo usermod -a -G docker $USER`.
3. logout of ec2 instance and login again for docker to register user.
4. change directory to airbyte `cd airbyte`.
5. `.env` file in airbyte directory needs to be configured to use external postgres rds instance:
    1. open the `.env` file with root privileges in any text editor
    2. locate the below values and change them to following
       ```text 
       DATABASE_USER=postgres 
       DATABASE_PASSWORD=<RDSPassword>
       DATABASE_HOST=<AirbyteRDSInstanceDomainName>
       DATABASE_PORT=5432 DATABASE_DB=airbyte
       ```
       where `RDSPassword` is the parameter value set in cloudformation parameter file and
       `AirbyteRDSInstanceDomainName` is the Output
       parameter value in cloudformation stack
    3. also locate the below values and change them to following
       ```text 
       DATABASE_URL=jdbc:postgresql://<AirbyteRDSInstanceDomainName>:5432/airbyte
       ```
       where `AirbyteRDSInstanceDomainName` is the Output parameter value in cloudformation stack
    4. run the following command to start airbyte `docker-compose up -d`
    5. now to start and register nginx run the below commands
        ```text
        sudo systemctl start nginx
        sudo systemctl status nginx
        sudo systemctl enable nginx
        ```

### Airbyte RDS instance update steps

If you want to update property(s) of RDS instance that require replacement, you need to follow the steps below:

1. Turn delete protection off for that RDS instance from console or CLI using the following command,
   ```bash
   aws rds modify-db-instance --db-instance-identifier <database_identifier> --region <AWS_REGION> 
   --no-deletion-protection
   ```
2. Take a snapshot of the original RDS instance using console or from CLI using the following command,
   ```bash
   aws rds create-db-snapshot --region <AWS_REGION> --db-snapshot-identifier <value> --db-instance-identifier 
   <database_identifier>
   ```
3. Pass the snapshot name or ARN in the pipeline parameters and update stack. Don't change the parameter's
   value in future unless you want to restore database from a different snapshot (Doing this will create a new
   instance). For more info, follow 'Updating DB instances' from
   (https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-rds-database-instance.html)

### Main Deployment Steps

### Sandbox

#### MDP Utils

##### VAST_RE

1. Run the given command to deploy the utils stack
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name mdp-utils-sandbox-stack --template-file cloudformation/resource_stacks/mdp_utils/mdp-utils-stack.yml --parameter-overrides file://cloudformation/resource_stacks/mdp_utils/vast_re/mdp-utils-sandbox-parameters.json --s3-bucket mdp-sandbox-bucket --s3-prefix cloudformation_stacks/templates --capabilities CAPABILITY_NAMED_IAM
    ```

##### CHASE

1. Run the given command to deploy the secrets stack
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name mdp-utils-sandbox-stack --template-file cloudformation/resource_stacks/mdp_utils/mdp-utils-stack.yml --parameter-overrides file://cloudformation/resource_stacks/mdp_utils/chase/mdp-utils-sandbox-parameters.json --s3-bucket mdp-sandbox-chase-bucket --s3-prefix cloudformation_stacks/templates --capabilities CAPABILITY_NAMED_IAM
    ```

#### MDP Secrets

##### VAST_RE

1. Run the given command to deploy the secrets stack
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name mdp-secrets-sandbox-stack --template-file cloudformation/resource_stacks/secrets/mdp-secrets-stack.yml --parameter-overrides file://cloudformation/resource_stacks/secrets/vast_re/mdp-secrets-sandbox-parameters.json --s3-bucket mdp-sandbox-bucket --s3-prefix cloudformation_stacks/templates
    ```

##### CHASE

1. Run the given command to deploy the secrets stack
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name mdp-secrets-sandbox-stack --template-file cloudformation/resource_stacks/secrets/mdp-secrets-stack.yml --parameter-overrides file://cloudformation/resource_stacks/secrets/chase/mdp-secrets-sandbox-parameters.json --s3-bucket mdp-sandbox-chase-bucket --s3-prefix cloudformation_stacks/templates
    ```

2. Wait for stack to complete and then run the given command to put th the secret values in the secret manager
    ```bash
    python cloudformation/resource_stacks/secrets/update_secrets.py --stack-name mdp-secrets-sandbox-stack --mappings '{"<key>":"<value>"}' (if value is string)
      or
    python cloudformation/resource_stacks/secrets/update_secrets.py --stack-name mdp-secrets-sandbox-stack --mappings '{"<key>":{"<key2>":"<value>"}}' (if value is json type)
    ```
   where mappings take the dict in json string form which contains the resource `logical id` as key
   and `secret to put` as the value

#### Airbyte

1. Follow [Token Generation](#token-generation) to get client id and secret

##### VAST_RE

1. Run the given command to deploy the application stack
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name airbyte-sandbox-stack --template-file cloudformation/resource_stacks/airbyte/airbyte-application-stack.yml --parameter-overrides file://cloudformation/resource_stacks/airbyte/vast_re/airbyte-application-sandbox-parameters.json --s3-bucket mdp-sandbox-bucket --s3-prefix cloudformation_stacks/templates --no-execute-changeset --capabilities CAPABILITY_IAM
    ```

##### CHASE

1. Run the given command to deploy the application stack
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name airbyte-sandbox-stack --template-file cloudformation/resource_stacks/airbyte/airbyte-application-stack.yml --parameter-overrides file://cloudformation/resource_stacks/airbyte/chase/airbyte-application-sandbox-parameters.json --s3-bucket mdp-sandbox-chase-bucket --s3-prefix cloudformation_stacks/templates --no-execute-changeset --capabilities CAPABILITY_IAM
    ```

2. After stack is successfully created Follow [EC2 Initial Configuration](#ec2-initial-configuration) to set up Airbyte
   on EC2 instance
3. Airbyte is successfully deployed and can be accessed using homestoryrewards vpn
4. To prevent any mishappening on rds instance follow below command to deny deletion/replacement of rds instance
    ```bash
    aws cloudformation set-stack-policy --stack-name airbyte-sandbox-stack --stack-policy-body file://cloudformation/resource_stacks/airbyte/airbyte-application-stack-policy.json
    ```

#### Airflow

##### VAST_RE

1. Run the given command to deploy the application stack
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name airflow-sandbox-stack --template-file cloudformation/resource_stacks/airflow/airflow-application-stack.yml --parameter-overrides file://cloudformation/resource_stacks/airflow/vast_re/airflow-application-sandbox-parameters.json --s3-bucket mdp-sandbox-bucket --s3-prefix cloudformation_stacks/templates --capabilities CAPABILITY_IAM
    ```

##### CHASE

1. Run the given command to deploy the application stack
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name airflow-sandbox-stack --template-file cloudformation/resource_stacks/airflow/airflow-application-stack.yml --parameter-overrides file://cloudformation/resource_stacks/airflow/chase/airflow-application-sandbox-parameters.json --s3-bucket mdp-sandbox-chase-bucket --s3-prefix cloudformation_stacks/templates --capabilities CAPABILITY_IAM
    ```

#### MDP Notifications

##### VAST_RE

1. Run the given command to deploy the application stack
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name mdp-notifications-sandbox-stack --template-file cloudformation/resource_stacks/notifications/mdp-notifications-stack.yml --parameter-overrides file://cloudformation/resource_stacks/notifications/vast_re/mdp-notifications-sandbox-parameters.json --s3-bucket mdp-sandbox-bucket --s3-prefix cloudformation_stacks/templates --capabilities CAPABILITY_IAM
    ```

##### CHASE

1. Run the given command to deploy the application stack
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name mdp-notifications-sandbox-stack --template-file cloudformation/resource_stacks/notifications/mdp-notifications-stack.yml --parameter-overrides file://cloudformation/resource_stacks/notifications/chase/mdp-notifications-sandbox-parameters.json --s3-bucket mdp-sandbox-chase-bucket --s3-prefix cloudformation_stacks/templates --capabilities CAPABILITY_IAM
    ```

### Beta

#### MDP Secrets

##### VAST_RE

1. Run the given command to deploy the secrets stack
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name mdp-secrets-beta-stack --template-file cloudformation/resource_stacks/secrets/mdp-secrets-stack.yml --parameter-overrides file://cloudformation/resource_stacks/secrets/vast_re/mdp-secrets-beta-parameters.json --s3-bucket mdp-beta-bucket --s3-prefix cloudformation_stacks/templates
    ```

2. Wait for stack to complete and then run the given command to put th the secret values in the secret manager
    ```bash
    python cloudformation/resource_stacks/secrets/update_secrets.py --stack-name mdp-secrets-beta-stack --mappings '{"<key>":"<value>"}' (if value is string)
      or
    python cloudformation/resource_stacks/secrets/update_secrets.py --stack-name mdp-secrets-beta-stack --mappings '{"<key>":{"<key2>":"<value>"}}' (if value is json type)
    ```
   where mappings take the dict in json string form which contains the resource `logical id` as key
   and `secret to put` as the value

#### Airbyte

1. Follow [Token Generation](#token-generation) to get client id and secret

##### VAST_RE

1. Run the given command to deploy the application stack
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name airbyte-beta-stack --template-file cloudformation/resource_stacks/airbyte/airbyte-application-stack.yml --parameter-overrides file://cloudformation/resource_stacks/airbyte/vast_re/airbyte-application-beta-parameters.json --s3-bucket mdp-beta-bucket --s3-prefix cloudformation_stacks/templates --no-execute-changeset --capabilities CAPABILITY_IAM
    ```

2. After stack is successfully created Follow [EC2 Initial Configuration](#ec2-initial-configuration) to set up Airbyte
   on EC2 instance
3. Airbyte is successfully deployed and can be accessed using homestoryrewards vpn
4. To prevent any mishappening on rds instance follow below command to deny deletion/replacement of rds instance
    ```bash
    aws cloudformation set-stack-policy --stack-name airbyte-beta-stack --stack-policy-body file://cloudformation/resource_stacks/airbyte/airbyte-application-stack-policy.json
    ```

#### Airflow

##### VAST_RE

1. Run the given command to deploy the application stack
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name airflow-beta-stack --template-file cloudformation/resource_stacks/airflow/airflow-application-stack.yml --parameter-overrides file://cloudformation/resource_stacks/airflow/vast_re/airflow-application-beta-parameters.json --s3-bucket mdp-beta-bucket --s3-prefix cloudformation_stacks/templates --capabilities CAPABILITY_IAM
    ```

### Prod

#### MDP Utils

##### VAST_RE

1. Run the given command to deploy the utils stack
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name mdp-utils-prod-stack --template-file cloudformation/resource_stacks/mdp_utils/mdp-utils-stack.yml --parameter-overrides file://cloudformation/resource_stacks/mdp_utils/vast_re/mdp-utils-prod-parameters.json --s3-bucket mdp-prod-bucket --s3-prefix cloudformation_stacks/templates --capabilities CAPABILITY_NAMED_IAM
    ```

##### CHASE

1. Run the given command to deploy the secrets stack
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name mdp-utils-prod-stack --template-file cloudformation/resource_stacks/mdp_utils/mdp-utils-stack.yml --parameter-overrides file://cloudformation/resource_stacks/mdp_utils/chase/mdp-utils-prod-parameters.json --s3-bucket mdp-prod-chase-bucket --s3-prefix cloudformation_stacks/templates --capabilities CAPABILITY_NAMED_IAM
    ```

#### MDP Secrets

##### VAST_RE

1. Run the given command to deploy the secrets stack
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name mdp-secrets-prod-stack --template-file cloudformation/resource_stacks/secrets/mdp-secrets-stack.yml --parameter-overrides file://cloudformation/resource_stacks/secrets/vast_re/mdp-secrets-prod-parameters.json --s3-bucket mdp-prod-bucket --s3-prefix cloudformation_stacks/templates
    ```

##### CHASE

1. Run the given command to deploy the secrets stack
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name mdp-secrets-prod-stack --template-file cloudformation/resource_stacks/secrets/mdp-secrets-stack.yml --parameter-overrides file://cloudformation/resource_stacks/secrets/chase/mdp-secrets-prod-parameters.json --s3-bucket mdp-prod-chase-bucket --s3-prefix cloudformation_stacks/templates
    ```

2. Wait for stack to complete and then run the given command to put the secret values in the secret manager
    ```bash
    python cloudformation/resource_stacks/secrets/update_secrets.py --stack-name mdp-secrets-prod-stack --mappings '{"<key>":"<value>"}' (if value is string)
      or
    python cloudformation/resource_stacks/secrets/update_secrets.py --stack-name mdp-secrets-prod-stack --mappings '{"<key>":{"<key2>":"<value>"}}' (if value is json type)
    ```
   where mappings take the dict in json string form which contains the resource `logical id` as key
   and `secret to put` as the value

#### Airbyte

1. Follow [Token Generation](#token-generation) to get client id and secret

##### VAST_RE

1. Run the given command to deploy the application stack
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name airbyte-prod-stack --template-file cloudformation/resource_stacks/airbyte/airbyte-application-stack.yml --parameter-overrides file://cloudformation/resource_stacks/airbyte/vast_re/airbyte-application-prod-parameters.json --s3-bucket mdp-prod-bucket --s3-prefix cloudformation_stacks/templates --no-execute-changeset --capabilities CAPABILITY_IAM
    ```

##### CHASE

1. Run the given command to deploy the application stack
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name airbyte-prod-stack --template-file cloudformation/resource_stacks/airbyte/airbyte-application-stack.yml --parameter-overrides file://cloudformation/resource_stacks/airbyte/chase/airbyte-application-prod-parameters.json --s3-bucket mdp-prod-chase-bucket --s3-prefix cloudformation_stacks/templates --no-execute-changeset --capabilities CAPABILITY_IAM
    ```

2. After stack is successfully created Follow [EC2 Initial Configuration](#ec2-initial-configuration) to set up Airbyte
   on EC2 instance
3. Airbyte is successfully deployed and can be accessed using homestoryrewards vpn
4. To prevent any mishappening on rds instance follow below command to deny deletion/replacement of rds instance
    ```bash
    aws cloudformation set-stack-policy --stack-name airbyte-prod-stack --stack-policy-body file://cloudformation/resource_stacks/airbyte/airbyte-application-stack-policy.json
    ```

#### Airflow

##### VAST_RE

1. Run the given command to deploy the application stack
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name airflow-prod-stack --template-file cloudformation/resource_stacks/airflow/airflow-application-stack.yml --parameter-overrides file://cloudformation/resource_stacks/airflow/vast_re/airflow-application-prod-parameters.json --s3-bucket mdp-prod-bucket --s3-prefix cloudformation_stacks/templates --capabilities CAPABILITY_IAM
    ```

##### CHASE

1. Run the given command to deploy the application stack
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name airflow-prod-stack --template-file cloudformation/resource_stacks/airflow/airflow-application-stack.yml --parameter-overrides file://cloudformation/resource_stacks/airflow/chase/airflow-application-prod-parameters.json --s3-bucket mdp-prod-chase-bucket --s3-prefix cloudformation_stacks/templates --capabilities CAPABILITY_IAM
    ```

#### MDP Notifications

##### VAST_RE

1. Run the given command to deploy the application stack
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name mdp-notifications-prod-stack --template-file cloudformation/resource_stacks/notifications/mdp-notifications-stack.yml --parameter-overrides file://cloudformation/resource_stacks/notifications/vast_re/mdp-notifications-prod-parameters.json --s3-bucket mdp-prod-bucket --s3-prefix cloudformation_stacks/templates --capabilities CAPABILITY_IAM
    ```

##### CHASE

1. Run the given command to deploy the application stack
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name mdp-notifications-prod-stack --template-file cloudformation/resource_stacks/notifications/mdp-notifications-stack.yml --parameter-overrides file://cloudformation/resource_stacks/notifications/chase/mdp-notifications-prod-parameters.json --s3-bucket mdp-prod-chase-bucket --s3-prefix cloudformation_stacks/templates --capabilities CAPABILITY_IAM
    ```

## Code Pipeline Deployment Steps

### Sandbox

#### MDP Workflow Stack Pipeline

##### VAST_RE

1. Run the given command to deploy the pipeline stack and execute the change set
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name mdp-workflow-sandbox-pipeline --template-file cloudformation/code_pipeline/mdp_workflow_stack/mdp-workflow-pipeline-stack.yml --parameter-overrides file://cloudformation/code_pipeline/mdp_workflow_stack/vast_re/mdp-workflow-pipeline-sandbox-parameters.json --s3-bucket mdp-sandbox-bucket --s3-prefix cloudformation_stacks/templates --capabilities CAPABILITY_IAM
    ```

##### CHASE

1. Run the given command to deploy the pipeline stack and execute the change set
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name mdp-workflow-sandbox-pipeline --template-file cloudformation/code_pipeline/mdp_workflow_stack/mdp-workflow-pipeline-stack.yml --parameter-overrides file://cloudformation/code_pipeline/mdp_workflow_stack/chase/mdp-workflow-pipeline-sandbox-parameters.json --s3-bucket mdp-sandbox-chase-bucket --s3-prefix cloudformation_stacks/templates --capabilities CAPABILITY_IAM
    ``

#### Cloudformation Stack Pipeline

##### VAST_RE

1. Run the given command to deploy the pipeline stack and execute the change set
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name mdp-sandbox-pipeline --template-file cloudformation/code_pipeline/cloudformation_stack/mdp-pipeline-stack.yml --parameter-overrides file://cloudformation/code_pipeline/cloudformation_stack/vast_re/mdp-sandbox-pipeline-parameters.json --s3-bucket mdp-sandbox-bucket --s3-prefix cloudformation_stacks/templates --capabilities CAPABILITY_IAM
    ```

##### CHASE

1. Run the given command to deploy the pipeline stack and execute the change set
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name mdp-sandbox-pipeline --template-file cloudformation/code_pipeline/cloudformation_stack/mdp-pipeline-stack.yml --parameter-overrides file://cloudformation/code_pipeline/cloudformation_stack/chase/mdp-sandbox-pipeline-parameters.json --s3-bucket mdp-sandbox-chase-bucket --s3-prefix cloudformation_stacks/templates --capabilities CAPABILITY_IAM
    ```

#### Airbyte Connectors Flows

##### VAST_RE

1. Run the given command to deploy the pipeline stack and execute the change set
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name airbyte-connectors-sandbox-pipeline --template-file cloudformation/code_pipeline/airbyte_connectors/airbyte-connectors-pipeline-stack.yml --parameter-overrides file://cloudformation/code_pipeline/airbyte_connectors/vast_re/airbyte-connectors-sandbox-pipeline-parameters.json --s3-bucket mdp-sandbox-bucket --s3-prefix cloudformation_stacks/templates --capabilities CAPABILITY_IAM
    ```

##### CHASE

1. Run the given command to deploy the pipeline stack and execute the change set
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name airbyte-connectors-sandbox-pipeline --template-file cloudformation/code_pipeline/airbyte_connectors/airbyte-connectors-pipeline-stack.yml --parameter-overrides file://cloudformation/code_pipeline/airbyte_connectors/chase/airbyte-connectors-sandbox-pipeline-parameters.json --s3-bucket mdp-sandbox-chase-bucket --s3-prefix cloudformation_stacks/templates --capabilities CAPABILITY_IAM
    ```

#### Airbyte Update Pipeline

##### VAST_RE

1. Run the given command to deploy the pipeline stack and execute the change set
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name airbyte-updates-sandbox-pipeline --template-file cloudformation/code_pipeline/airbyte_updates/airbyte-updates-pipeline-stack.yml --parameter-overrides file://cloudformation/code_pipeline/airbyte_updates/vast_re/airbyte-updates-sandbox-pipeline-parameters.json --s3-bucket mdp-sandbox-bucket --s3-prefix cloudformation_stacks/templates --capabilities CAPABILITY_IAM
    ```

##### CHASE

1. Run the given command to deploy the pipeline stack and execute the change set
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name airbyte-updates-sandbox-pipeline --template-file cloudformation/code_pipeline/airbyte_updates/airbyte-updates-pipeline-stack.yml --parameter-overrides file://cloudformation/code_pipeline/airbyte_updates/chase/airbyte-updates-sandbox-pipeline-parameters.json --s3-bucket mdp-sandbox-chase-bucket --s3-prefix cloudformation_stacks/templates --capabilities CAPABILITY_IAM
    ```

### Beta

#### MDP Workflow Stack Pipeline

##### VAST_RE

1. Run the given command to deploy the pipeline stack and execute the change set
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name mdp-workflow-beta-pipeline --template-file cloudformation/code_pipeline/mdp_workflow_stack/mdp-workflow-pipeline-stack.yml --parameter-overrides file://cloudformation/code_pipeline/mdp_workflow_stack/vast_re/mdp-workflow-pipeline-beta-parameters.json --s3-bucket mdp-beta-bucket --s3-prefix cloudformation_stacks/templates --capabilities CAPABILITY_IAM
    ```

#### Cloudformation Stack Pipeline

##### VAST_RE

1. Run the given command to deploy the pipeline stack and execute the change set
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name mdp-beta-pipeline --template-file cloudformation/code_pipeline/cloudformation_stack/mdp-pipeline-stack.yml --parameter-overrides file://cloudformation/code_pipeline/cloudformation_stack/vast_re/mdp-beta-pipeline-parameters.json --s3-bucket mdp-beta-bucket --s3-prefix cloudformation_stacks/templates --capabilities CAPABILITY_IAM
    ```

#### Airbyte Connectors Flows

##### VAST_RE

1. Run the given command to deploy the pipeline stack and execute the change set
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name airbyte-connectors-beta-pipeline --template-file cloudformation/code_pipeline/airbyte_connectors/airbyte-connectors-pipeline-stack.yml --parameter-overrides file://cloudformation/code_pipeline/airbyte_connectors/vast_re/airbyte-connectors-beta-pipeline-parameters.json --s3-bucket mdp-beta-bucket --s3-prefix cloudformation_stacks/templates --capabilities CAPABILITY_IAM
    ```

#### Airbyte Update Pipeline

##### VAST_RE

1. Run the given command to deploy the pipeline stack and execute the change set
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name airbyte-updates-beta-pipeline --template-file cloudformation/code_pipeline/airbyte_updates/airbyte-updates-pipeline-stack.yml --parameter-overrides file://cloudformation/code_pipeline/airbyte_updates/vast_re/airbyte-updates-beta-pipeline-parameters.json --s3-bucket mdp-beta-bucket --s3-prefix cloudformation_stacks/templates --capabilities CAPABILITY_IAM
    ```

### Prod

#### MDP Workflow Stack Pipeline

##### VAST_RE

1. Run the given command to deploy the pipeline stack and execute the change set
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name mdp-workflow-prod-pipeline --template-file cloudformation/code_pipeline/mdp_workflow_stack/mdp-workflow-pipeline-stack.yml --parameter-overrides file://cloudformation/code_pipeline/mdp_workflow_stack/vast_re/mdp-workflow-pipeline-prod-parameters.json --s3-bucket mdp-prod-bucket --s3-prefix cloudformation_stacks/templates --capabilities CAPABILITY_IAM
    ```

##### CHASE

1. Run the given command to deploy the pipeline stack and execute the change set
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name mdp-workflow-prod-pipeline --template-file cloudformation/code_pipeline/mdp_workflow_stack/mdp-workflow-pipeline-stack.yml --parameter-overrides file://cloudformation/code_pipeline/mdp_workflow_stack/chase/mdp-workflow-pipeline-prod-parameters.json --s3-bucket mdp-prod-chase-bucket --s3-prefix cloudformation_stacks/templates --capabilities CAPABILITY_IAM
    ```

#### Cloudformation Stack Pipeline

##### VAST_RE

1. Run the given command to deploy the pipeline stack and execute the change set
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name mdp-prod-pipeline --template-file cloudformation/code_pipeline/cloudformation_stack/mdp-pipeline-stack.yml --parameter-overrides file://cloudformation/code_pipeline/cloudformation_stack/vast_re/mdp-prod-pipeline-parameters.json --s3-bucket mdp-prod-bucket --s3-prefix cloudformation_stacks/templates --capabilities CAPABILITY_IAM
    ```

##### CHASE

1. Run the given command to deploy the pipeline stack and execute the change set
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name mdp-prod-pipeline --template-file cloudformation/code_pipeline/cloudformation_stack/mdp-pipeline-stack.yml --parameter-overrides file://cloudformation/code_pipeline/cloudformation_stack/chase/mdp-prod-pipeline-parameters.json --s3-bucket mdp-prod-chase-bucket --s3-prefix cloudformation_stacks/templates --capabilities CAPABILITY_IAM
    ```

#### Airbyte Connectors Flows

##### VAST_RE

1. Run the given command to deploy the pipeline stack and execute the change set
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name airbyte-connectors-prod-pipeline --template-file cloudformation/code_pipeline/airbyte_connectors/airbyte-connectors-pipeline-stack.yml --parameter-overrides file://cloudformation/code_pipeline/airbyte_connectors/vast_re/airbyte-connectors-prod-pipeline-parameters.json --s3-bucket mdp-prod-bucket --s3-prefix cloudformation_stacks/templates --capabilities CAPABILITY_IAM
    ```

##### CHASE

1. Run the given command to deploy the pipeline stack and execute the change set
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name airbyte-connectors-prod-pipeline --template-file cloudformation/code_pipeline/airbyte_connectors/airbyte-connectors-pipeline-stack.yml --parameter-overrides file://cloudformation/code_pipeline/airbyte_connectors/chase/airbyte-connectors-prod-pipeline-parameters.json --s3-bucket mdp-prod-chase-bucket --s3-prefix cloudformation_stacks/templates --capabilities CAPABILITY_IAM
    ```

#### Airbyte Update Pipeline

##### VAST_RE

1. Run the given command to deploy the pipeline stack and execute the change set
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name airbyte-updates-prod-pipeline --template-file cloudformation/code_pipeline/airbyte_updates/airbyte-updates-pipeline-stack.yml --parameter-overrides file://cloudformation/code_pipeline/airbyte_updates/vast_re/airbyte-updates-prod-pipeline-parameters.json --s3-bucket mdp-prod-bucket --s3-prefix cloudformation_stacks/templates --capabilities CAPABILITY_IAM
    ```

##### CHASE

1. Run the given command to deploy the pipeline stack and execute the change set
    ```bash
    aws cloudformation deploy --region us-east-1 --stack-name airbyte-updates-prod-pipeline --template-file cloudformation/code_pipeline/airbyte_updates/airbyte-updates-pipeline-stack.yml --parameter-overrides file://cloudformation/code_pipeline/airbyte_updates/chase/airbyte-updates-prod-pipeline-parameters.json --s3-bucket mdp-prod-chase-bucket --s3-prefix cloudformation_stacks/templates --capabilities CAPABILITY_IAM
    ```

### Post Deployment Steps

* **Adding ssh key to EC2 instance**: If needed one can add the ssh key in ec2 instance given the conditions that the
  new ssh key is stored in parameter store and user has another ssh key which has access to the ec2 instance, if the
  conditions are met run the given command to add new ssh key to the ec2 instance
  ```bash
  python scripts/attach_ssh_key.py --parameter-name <PARAMETER_NAME> --ssh-path <SSH_PATH>  --username <USERNAME> --ip-address <IP_ADDRESS> [--region <REGION>] [--aws-profile <AWS_PROFILE>] [--name <NAME>] [--debug] [--generate-pem-file] [--pem-file-path <PEM_FILE_PATH>]
  ```
  or run the command with `-h` for more help

### Local Parameters Generation Steps

* **Generating Testing Parameters For Stack**: If you want to generate a local parameters file for 
  testing purposes, run the given command:
  ```bash
  python scripts/stack_params_manager.py -p <path to the stack you want to generate the parameters For>
  ```
  or run the command with `-h` or `--help` for more help

### Testing Build Spec files on local:

For using the local codebuild agent .
* Change the current working directory to the scripts/aws_codebuild_local_agent.
   ```shell
   cd scripts/aws_codebuild_local_agent
   ```
* Create a .local dir and cd into it.
   ```shell
   mkdir .local && cd .local
   ```
* Clone the github repositories containing the dockerfiles for codebuild. 
   ```shell
   git clone https://github.com/aws/aws-codebuild-docker-images.git
   ```
* cd into the folder containing the image. 
  ```shell
  cd aws-codebuild-docker-images/ubuntu/standard/6.0
  ```
* Build the image using the DockerFile present in that folder
  ```shell
  docker build -t aws/codebuild/standard:6.0 .
  ```
* Download the CodeBuild agent.
  ```shell
  docker pull public.ecr.aws/codebuild/local-builds:latest
  ```
* Change to the prefect-cloudformation directory and from the root of the project
   * Change the permissions on codebuild_build.sh script:
      ```
      chmod +x scripts/aws_codebuild_local_agent/codebuild_build.sh
      ```
   * Run the codebuild_build.sh script and specify your container image and the output directory
      ```shell
      scripts/aws_codebuild_local_agent/codebuild_build.sh -i aws/codebuild/standard:6.0 -a <output_directory> -e <path_to_env_file> -b <path_to_build_spec_file> -c
      ```
* Environment variable file format:

    * Expects each line to be in VAR=VAL format
    * Lines beginning with # are processed as comments and ignored
    * Blank lines are ignored
    * File can be of type .env or .txt
    * There is no special handling of quotation marks, meaning they will be part of the VAL

* A sample command that would work if above steps are performed correctly is:
    ```shell
   scripts/aws_codebuild_local_agent/codebuild_build.sh -i aws/codebuild/standard:6.0 -a scripts/aws_codebuild_local_agent/results -e scripts/aws_codebuild_local_agent/.env -b build_specs/lambdas/test-buildspec.yml -c
    ```
    * where scripts/aws_codebuild_local_agent/.env is your environment variable file
    * scripts/aws_codebuild_local_agent/results is your artifact output directory.
    * build_specs/lambdas/test-buildspec.yml is the build-spec file you want to test
    
* For more about how to use codebuild_build.sh refer [this](https://github.com/aws/aws-codebuild-docker-images/blob/master/local_builds/README.md)