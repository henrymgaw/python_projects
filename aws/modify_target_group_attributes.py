#!/usr/bin/python3

try:
    # we need boto3 to create ALBs
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

# this is used internally for salt to identify this execution module by name.
# we can change this to a duplicate name of another salt uses to expand upon
# it and share the name space
__virtualname__ = 'eb_boto3_elbv2'


def __virtual__():
    if HAS_BOTO3:
      return __virtualname__
    else:
      return False, 'The eb_boto3_elbv2 execution module cannot be loaded: \
boto3 unavailable'

def _find_arn(arn_field_name='Arn', **kwargs):
    '''
    Find ARN value from a provided data set
    '''
    # sometimes the data contains a dictionary containing a key called "data"
    # with its value being the data we care about. this helps extract that
    if 'data' in kwargs:
        data = kwargs['data']
    # this is a recursive function. this allows us to descend through a
    # dictionary and through any nested dictionaries
    if isinstance(data, dict):
        for k, v in data.items():
            # we only care about 1 value here, so we return it once it's
            # found
            if arn_field_name in k:
                return v
            else:
                if isinstance(v, dict):
                    exists_in_recursive_func = _find_arn(arn_field_name=arn_field_name, data=v)
                    if exists_in_recursive_func:
                        return exists_in_recursive_func
        return False
    else:
        return False, 'Parameter must be a dict'

def describe_target_health(**kwargs):
    '''
    Describes Targets in Target Group including thier Health

    If target group is not found, returns False
    Else returns list of TargetHealthDescription (empty list if none)

    Example:
        eb_boto3_elbv2.describe_target_health \
            name='example-target-group'

    Required parameters:
        name   : Target Group Name (str)

    Optional parameters:
        region : AWS region (str)
    '''
    # create boto3 connection
    if 'region' in kwargs:
        region = kwargs['region']

    else:
        # we use _get_region() to populate this value. it should either return the
        # configured region or say 'Not configured'
        region = _get_region()

    # we want this to error out if the region is not configured at all
    if region == 'Not configured':
        raise CommandExecutionError(
            "AWS region is not currently configured. Please use 'set_region' \
to set current and/or default AWS region.")
    # set alb_client as a global variable, only if boto3 imports successfully
    alb_client = boto3.client('elbv2', region_name=region)

    # check that all required params are present
    required_params = ['name']
    _check_params(required_params, kwargs, 'describe_target_health')

    # get ARN for target group
    target_group_name = kwargs['name']
    target_group_data = describe_target_group(
        name=[kwargs['name']],
        region=region
    )
    if target_group_data:
        target_group_arn = _find_arn(
            arn_field_name='TargetGroupArn',
            data=target_group_data[0]
        )

        # get targets for arn
        target_health_properties = {}
        target_health_properties['TargetGroupArn'] = target_group_arn

        try:
            response = alb_client.describe_target_health(**target_health_properties)[
                'TargetHealthDescriptions']
            return response
        except:
            return False

    else:
        # target group not found
        return False

def modify_target_group_attributes(**kwargs):
    '''
    Used to modify target group attributes like deregistration delay 
    Example:
        eb_boto3_elbv2.modify_target_group_attributes targetgroupname='example-target-group'
    Required parameters:
        targetgroupname   : Target Group Name (str)
    Optional parameters:
        region : AWS region (str)
        attributesKeys: default(deregistration_delay.timeout_seconds,Value=30) 
    '''
    # create boto3 connection
    if 'region' in kwargs:
        region = kwargs['region']
    else:
        # we use _get_region() to populate this value. it should either return the
        # configured region or say 'Not configured'
        region = _get_region()

    # we want this to error out if the region is not configured at all
    if region == 'Not configured':
        raise CommandExecutionError(
            "AWS region is not currently configured. Please use 'set_region' \
to set current and/or default AWS region.")

    if 'attributesKey' in kwargs:
        attributesKey = kwargs['attributesKey']
    else:
        attributesKey = deregistration_delay.timeout_seconds,Value=30

    # check that all required params are present
    required_params = ['targetgroupname','attributesKey']
    _check_params(required_params, kwargs, 'modify_target_group_attributes')

    # first check targetgroup health
    target_group_name = kwargs['targetgroupname']
    target_group_data = describe_target_group(
        name=[kwargs['targetgroupname']],
        region=region
    )
    if target_group_data:
        target_group_arn = _find_arn(
            arn_field_name='TargetGroupArn',
            data=target_group_data[0]
        )

        # get targets for arn
        target_health_properties = {}
        target_health_properties['TargetGroupArn'] = target_group_arn

    try:
        health = alb_client.describe_target_health(**target_health_properties)['TargetHealthDescriptions']
        return health
    except:
        raise CommandExecutionError('Failed to get targetgroup health status from: {}'.format(kwargs['targetgroupname']))
