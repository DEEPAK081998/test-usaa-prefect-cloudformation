import constants
from managers import dag_manager


def lambda_handler(event, context):
    """
    Main Driver function
    """
    dag_manager_obj = dag_manager.DagsManager()
    # process dags params from dynamodb
    for record in event[constants.RECORDS]:
        dag_manager_obj.manage_dag(record=record)
