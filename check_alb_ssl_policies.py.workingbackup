#!/usr/bin/env python3

import boto3
import re
import sys

def show_albs(**kwargs):
    '''
    Gets the SSL Policy of an ALB Listener
    Example:
        show_albs \
            region='...'
            identifier='...'

    Required parameters:
        region     : AWS region (str)
        identifier : Regex identifier in ALB name to use when filtering ALBs
    '''
    # check parameters
    if 'identifier' in kwargs:
        identifier = re.compile(kwargs['identifier'])
    else:
        raise Exception('"identifier" is a required parameter!')

    if 'region' in kwargs:
        region = kwargs['region']
    else:
        raise Exception('"region" is a required parameter!')

    alb_client = boto3.client('elbv2', region_name=region)

    albs = {}

    # a try/except block is probably not necessary here, but it may be useful if you wanted to handle different types of exceptions in particular ways
    try:
        alb_data_all = alb_client.describe_load_balancers()['LoadBalancers']
    except Exception as e:
        raise Exception("Exception occured: {}".format(e))

    for alb_data in alb_data_all:
        if identifier.match(alb_data['LoadBalancerName']):
            get_listener_ssl_policy(alb_data['LoadBalancerArn'], alb_data['LoadBalancerName'], region)


def get_listener_ssl_policy(alb_arn, alb_name, region):
    '''
    Gets the SSL Policy of an ALB Listener
    Example:
        get_listener_ssl_policy \
            alb_arn='...'

    Required parameters:
        alb_arn : ALB ARN value to filter results (str)
        region  : AWS region (str)
    '''
    alb_client = boto3.client('elbv2', region_name=region)

    listener_properties = {}

    # a try/except block is probably not necessary here, but it may be useful if you wanted to handle different types of exceptions in particular ways
    try:
        listener_properties['LoadBalancerArn'] = alb_arn
        response = alb_client.describe_listeners(**listener_properties)['Listeners']
    except Exception as e:
        raise Exception("Exception occured: {}".format(e))

    # now that we have our listener data, let's get the SSL policy. note: since we are only passing a single alb_arn, we only care about the first/only item in the list
    if 'SslPolicy' in response[0].keys():
        if response[0]['SslPolicy'] != 'ELBSecurityPolicy-TLS-1-2-Ext-2018-06':
            print('Found out of date SSL Policy! ALB: {} // Current Policy: {}'.format(alb_name, response[0]['SslPolicy']))

if __name__ == '__main__':
    # call function. we are parsing kwargs passed via command line so the downstream function can parse them as kwargs. we could just change these to args for both functions if we want
    show_albs(**dict(arg.split('=') for arg in sys.argv[1:]))
