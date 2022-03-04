#!/usr/local/bin/python3
'''

This will be used to update AMI-IDs in aws Elastic Container Service
https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecs.html

'''
import boto3
import json

def describe_task_definition(**kwargs):
    '''
    Example:
        AWS_PROFILE=saml ./ecs_control.py taskDefinition="honeycomb-proxy-service"

    Required parameters:
        taskDefinition     : (str) The family for the latest ACTIVE revision, family and revision (family:revision ) for a specific revision in the family, or full Amazon Resource Name (ARN) of the task definition to describe.

    Optional parameters:
        include            : (list) Determines whether to see the resource tags for the task definition. If TAGS is specified, the tags are included in the response. If this field is omitted, tags aren't included in the response.
    '''
    # check required parameters
    if 'taskDefinition' in kwargs:
        taskDefinition = kwargs['taskDefinition']
    else:
        raise Exception('"taskDefinition" is a required parameter!')
    if 'region' in kwargs:
        region = kwargs['region']
    else:
        raise Exception('"region" is a required parameter!')

    #include=kwargs['include']

    client = boto3.client('ecs', region_name="us-east-1")

    try:
        response = client.describe_task_definition(
            taskDefinition='string',
            include=[
                'TAGS',
            ]
         )
    except Exception as e:
        raise Exception("Exception occured: {}".format(e))

    return response

out=describe_task_definition(region="us-east-1", taskDefinition="honeycomb-proxy-service")
print(out)
