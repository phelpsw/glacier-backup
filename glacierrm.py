#!/usr/bin/env python

import boto3
import botocore
import time
import json

sns_client = boto3.client('sns')
response = sns_client.create_topic(Name='delete_topic')
topic_arn = response['TopicArn']
print topic_arn

# create lambda function here
import base64
import StringIO
import zipfile
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
    response = lambda_client.create_function(FunctionName='vault_deletion_lambda',
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

response = sns_client.subscribe(
        TopicArn=topic_arn,
        Protocol='lambda',
        Endpoint=function_arn
)
print response

glacier = boto3.client('glacier', region_name='us-east-1')
# Create glacier inventory request but with special delete lambda
vault_name = 'glacier_archive_20161201071932'
response = glacier.initiate_job(vaultName=vault_name,
                               jobParameters={'Format': 'JSON',
                                              'Type': 'inventory-retrieval',
                                              'SNSTopic': topic_arn
                                             }
                              )
print(response)
job_id = response['jobId']
