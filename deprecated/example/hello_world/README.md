# README #

A sample hello-world script that register the flow and use Docker image as storage

## Prerequisites

1. **Softwares:**
    1. docker: see [here](https://docs.docker.com/engine/install/) on how to install [docker](https://www.docker.com/)
    2. prefect aws: use given command to install prefect aws `pip install prefect[aws]`
2. **Authentication:**
    1. prefect: log in to prefect cloud using command `prefect auth login -k <API Key>`, if api key not present
       see [how to generate api key](https://docs.prefect.io/orchestration/concepts/api_keys.html#api-keys)
    2. docker with aws ecr: use the given command to login docker with aws ecr
       `aws ecr get-login-password --region <Region> | docker login --username AWS --password-stdin <Account ID>.dkr.ecr.<Region>.amazonaws.com`

## Usage:

register flow with command

```bash
python register_flow.py
```
