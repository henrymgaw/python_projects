#!/usr/bin/env python3

import boto3
import re
import sys

def get_listener_ssl_policy(**kwargs):
    '''
    Gets the SSL Policy of an ALB Listener
    Example:
        AWS_PROFILE=saml ./get_listener_ssl_policy alb_arn='...'

    Required parameters:
        alb_arn : ALB ARN value to filter results (str)
        region  : AWS region (str)
    '''
    # check parameters
    if 'alb_arn' in kwargs:
        alb_arn = kwargs['alb_arn']
    else:
        raise Exception('"alb_arn" is a required parameter!')

    if 'region' in kwargs:
        region = kwargs['region']
    else:
        raise Exception('"region" is a required parameter!')

    alb_client = boto3.client('elbv2', region_name=region)

    listener_properties = {}

    # a try/except block is probably not necessary here, but it may be useful if you wanted to handle different types of exceptions in particular ways
    try:
        listener_properties['LoadBalancerArn'] = alb_arn
        response = alb_client.describe_listeners(**listener_properties)['Listeners']
    except Exception as e:
        raise Exception("Exception occured: {}".format(e))

    # now that we have our listener data, let's get the SSL policy. note: since we are only passing a single alb_arn, we only care about the first/only item in the list
    ssl_policy = response[0]['SslPolicy']
    print(ssl_policy)

if __name__ == '__main__':
    # call function. we are parsing kwargs passed via command line so the downstream function can parse them as kwargs. we could just change these to args for both functions if we want
    get_listener_ssl_policy(**dict(arg.split('=') for arg in sys.argv[1:]))
