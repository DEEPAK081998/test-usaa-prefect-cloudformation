"""
An example script to register prefect flow and use docker image as storage option

Usage:
python register_flow.py

Note:- the values provided here are just for reference and might need to be changed
according to the need and requirement
"""
from prefect import Flow
from prefect.run_configs import ECSRun
from prefect.storage import Docker

from hello_world import hello_world

# name with which flow will be registered
FLOW_NAME = 'hello-world'

# prefect will compile the docker image and push the image to provided registry_url
STORAGE = Docker(
    registry_url='<Account ID>.dkr.ecr.<Region>.amazonaws.com',  # aws ecr uri link
    base_image='prefecthq/prefect',  # any base image required for build
    image_name='<image name>',  # final image name
    image_tag='ver-0.1',  # image version
    stored_as_script=True,  # to store flow in script form rather than serializing the flow
    path='/modules/register_flow.py',  # absolute path to the flow script in docker image
    env_vars={
        # append modules directory to PYTHONPATH
        "PYTHONPATH": "$PYTHONPATH:/modules"
    },  # additional environment variable that needs to be passed in docker image
    files={
        '/home/USER/prefect-cloudformation/example/hello_world/hello_world.py': '/modules/hello_world.py',
        '/home/USER/prefect-cloudformation/example/hello_world/register_flow.py': '/modules/register_flow.py'
    }  # additional files that need to be passed in docker image with there absolute src and destination path
)

# run configs that are required to run the flow
RUN_CONFIG = ECSRun(
    # flow will run on only those agents who have these lables
    labels=['<label1>', '<label2>'],
    # task role arn generated in prefect cloudformation stack
    task_role_arn='<task role arn',
    # addition roles that are required for execution
    execution_role_arn='<execution role arn>',
    # defines the cluster and launch type of the flow
    run_task_kwargs=dict(cluster='<prefect cluster name>', launchType='FARGATE'),
)

# tasks that run in this flow
with Flow(FLOW_NAME, storage=STORAGE, run_config=RUN_CONFIG) as flow:
    hello_world()

# register the flow in project
flow.register('<project name>')
