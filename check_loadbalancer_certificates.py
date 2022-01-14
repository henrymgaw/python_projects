#!/usr/bin/env python3

import boto3
import re
import sys

def show_albs(**kwargs):
    '''
    Gets the SSL Policy of an ALB Listener
    Example:
    AWS_PROFILE=saml ./check_loadbalancer_certificates.py region=us-west-2 identifier='.*dev3.*'

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
            check_loadbalancer_certificates(alb_data['LoadBalancerArn'], alb_data['LoadBalancerName'], region)

def check_loadbalancer_certificates(alb_arn, alb_name, region):
    '''
    Checks a loadbalancer to see if it is matches certificate arn of a wildcard certificate *.cep.us-west-2.dev3.neo.evbg.io if so return name of loadbalancer
    Example:
    AWS_PROFILE=saml ./check_loadbalancer_certificates.py region=us-west-2 identifier='.*dev3.*'

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
        #print(response)
    except Exception as e:
        raise Exception("Exception occured: {}".format(e))

  # now that we have our listener data, let's get the SSL policy. note: since we are only passing a single alb_arn, we only care about the first/only item in the list
    if 'Certificates' in  response[0].keys():
        certificatearn = response[0]['Certificates'][0]['CertificateArn']
        lb_name = response[0]['ListenerArn']
        #*.cep.us-west-2.dev3.neo.evbg.io cert arn
        if certificatearn == 'arn:aws:acm:us-west-2:360915197767:certificate/cb9586d1-76c4-4c30-ba23-2c6e3e095c6d':
           print(lb_name.split('/')[2])
        #*.dev3.dev.evbg.io cert arn
        elif certificatearn == 'arn:aws:acm:us-west-2:360915197767:certificate/3b034735-49f7-423c-a5c3-3c3e8dafaaaf':
           print(lb_name.split('/')[2])

# call above function. we are parsing kwargs passed via command line so the downstream function can parse them as kwargs. we could just change these to args for both functions if we want
if __name__ == '__main__':
    #check_loadbalancer_certificates(**dict(arg.split('=') for arg in sys.argv[1:]))
    show_albs(**dict(arg.split('=') for arg in sys.argv[1:]))
