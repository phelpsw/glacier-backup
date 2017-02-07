#!/usr/bin/env python

import boto3
import botocore
import time
import json
import base64
import StringIO
import zipfile
import argparse


def create_topic_arn():
    sns_client = boto3.client('sns')
    response = sns_client.create_topic(Name='delete_topic')
    topic_arn = response['TopicArn']
    return topic_arn


def setup_lambda_and_permissions(topic_arn):
    mf = StringIO.StringIO()
    with zipfile.ZipFile(mf, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write('vault_deletion_lambda.py')

    iam_client = boto3.client('iam')
    response = iam_client.get_role(RoleName='lambda_basic_execution')
    print response

    role_arn = response['Role']['Arn']

    lambda_client = boto3.client('lambda')

    try:
        response = lambda_client.get_function(FunctionName='vault_deletion_lambda')
        function_arn = response['Configuration']['FunctionArn']
    except botocore.exceptions.ClientError:
        response = lambda_client.create_function(
            FunctionName='vault_deletion_lambda',
            Runtime='python2.7',
            Role=role_arn,
            Handler='vault_deletion_lambda.my_handler',
            Code={'ZipFile': bytes(mf.getvalue())},
            Timeout=10,
            MemorySize=128)
        print response
        function_arn = response['FunctionArn']

    print 'function arn {}'.format(function_arn)

    try:
        response = lambda_client.add_permission(
                FunctionName=function_arn,
                StatementId='test_perm',
                Action='lambda:*', # lambda.invoke?
                Principal='sns.amazonaws.com')
        print response
    except botocore.exceptions.ClientError:
        # This error is thrown in the event the permission already exists
        pass

    sns_client = boto3.client('sns')
    response = sns_client.subscribe(
            TopicArn=topic_arn,
            Protocol='lambda',
            Endpoint=function_arn
    )
    print response


def create_delete_inventory(vault_name, topic_arn):
    glacier = boto3.client('glacier', region_name='us-east-1')
    metadata = json.dumps({'foo': 1, 'bar': '2'})
    response = glacier.initiate_job(vaultName=vault_name,
                                   jobParameters={'Format': 'JSON',
                                                  'Type': 'inventory-retrieval',
                                                  'SNSTopic': topic_arn,
                                                  'Description': metadata})
    print(response)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='''
    Delete AWS Glacier vaults using lambda functions to handle lengthy job
    completion.  Vaults do not need to be empty as the lambda function handling
    the initial inventory will delete each inner archive before eventually
    deleting the entire vault in a subsequent self scheduled lambda
    callback.''')
    '''
    parser.add_argument("--region",
                        help="Which AWS region to perform in",
                        type=str)
    '''

    parser.add_argument("--email",
                        help="Email address to send notification of completion",
                        type=str)
    parser.add_argument("--sms",
                        help="Phone number to send SMS notification of completion",
                        type=str)
    parser.add_argument('vaults', metavar='vault', type=str, nargs='+',
                        help='A list of vault names to delete')
    args = parser.parse_args()

    topic_arn = create_topic_arn()
    setup_lambda_and_permissions(topic_arn)
    for vault in args.vaults:
        create_delete_inventory(vault, topic_arn)

