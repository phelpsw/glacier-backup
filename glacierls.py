#!/usr/bin/env python

import boto3
import botocore
import time
import json

# TODO:
#   - proper role creation (restrict)
#   - lambda permission creation (restrict)

hostname = 'quasar'

client = boto3.client('glacier', region_name='us-east-1')
paginator = client.get_paginator('list_vaults')
vaults = []
for page in paginator.paginate():
    vaults.extend(page['VaultList'])

for vault in vaults:
    tags_response = client.list_tags_for_vault(vaultName=vault['VaultName'])
    if 'hostname' in tags_response['Tags'].keys():
        if tags_response['Tags']['hostname'] == hostname:
            print('{name} {ts} {arn}'.format(name=vault['VaultName'],
                                             ts=tags_response['Tags']['timestamp'],
                                             arn=vault['VaultARN']))




'''
topic_name = 'test_topic'
paginator = client.get_paginator('list_topics')
topics = []
for page in pageinator:
    topics.extend(page['Topics'])

'''


sns_client = boto3.client('sns')
response = sns_client.create_topic(Name='test_topic')
topic_arn = response['TopicArn']
print topic_arn


# create lambda function here
import base64
import StringIO
import zipfile
mf = StringIO.StringIO()
with zipfile.ZipFile(mf, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
    zf.write('lambdatest.py')
    #encoded_string = base64.b64encode(mf.getvalue())


# TODO: see if function already exists?


#from botocore.errorfactory import NoSuchEntity

iam_client = boto3.client('iam')
response = iam_client.get_role(RoleName='lambda_basic_execution')
print response
'''
# TODO: AssumeRolePolicyDocument seems to be premade roles only
# AmazonS3FullAccess etc
# https://developmentseed.org/blog/2016/03/08/aws-lambda-functions/
try:
    response = iam_client.get_role(RoleName='lambda_test_role')
except botocore.exceptions.ClientError:
    policy_dict = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": "arn:aws:logs:*:*:*"
            }
            #{
            #    "Action" : [
            #        "sns:Publish",
            #        "sns:Subscribe"
            #    ],
            #    "Effect" : "Allow",
            #    "Resource" : "arn:aws:sns:*:*:test_topic"
            #},
            #{
            #    "Effect": "Allow",
            #    "Action": "s3:*",
            #    "Resource": [
            #        "arn:aws:s3:::test_bucket",
            #        "arn:aws:s3:::test_bucket/*"
            #    ]
            #},
            #{
            #    "Effect": "Allow",
            #    "Action": "s3:ListAllMyBuckets",
            #    "Resource": "arn:aws:s3:::*"
            #},
            #{
            #    "Effect": "Allow",
            #    "Action": "ses:*",
            #    "Resource": "*"
            #}
        ]
    }
    response = iam_client.create_role(RoleName='lambda_test_role',
                                  AssumeRolePolicyDocument=json.dumps(policy_dict))
    print response
'''
role_arn = response['Role']['Arn']

lambda_client = boto3.client('lambda')

try:
    response = lambda_client.get_function(FunctionName='test_lambda')
    function_arn = response['Configuration']['FunctionArn']
except botocore.exceptions.ClientError:
    response = lambda_client.create_function(FunctionName='test_lambda',
                                             Runtime='python2.7',
                                             Role=role_arn,
                                             Handler='lambdatest.my_handler',
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



# Create test sns message and see lambda function trigger
'''
import json
message = {"foo": "bar"}
response = sns_client.publish(
    TargetArn=topic_arn,
    Message=json.dumps({'default': json.dumps(message)}),
    MessageStructure='json'
)
print response
'''

# Create glacier inventory request
vault_name = 'glacier_archive_20170201051302'
response = client.initiate_job(vaultName=vault_name,
                               jobParameters={'Format': 'JSON',
                                              'Type': 'inventory-retrieval',
                                              'SNSTopic': topic_arn
                                             }
                              )
print(response)
job_id = response['jobId']
'''

# Create glacier archive retrieval request
vault_name = 'glacier_archive_20161229184309'
archive_id = 'fcl45PEjjuAn0EGDKSQJXcB9ZFzu2MJo5CesQxZCSXAZGyL6sGZVn0c0fS8cZ_8AIRvpsMPbawXeXDfdhWxktES8pC_FbvuKPp-rbzlqigjGDAJnWwkQ6phPYxj05r7z_28PEtw1rA'
response = client.initiate_job(vaultName=vault_name,
                               jobParameters={'Type': 'archive-retrieval',
                                              'ArchiveId': archive_id,
                                              'SNSTopic': topic_arn
                                             }
                              )
print(response)
job_id = response['jobId']
'''
'''
response = client.describe_job(vaultName=vault_name, jobId=job_id)
while not response['Completed']:
    print('waiting 60 sec')
    time.sleep(60)
    response = client.describe_job(vaultName=vault_name, jobId=job_id)
    print(response)


response = client.get_job_output(vaultName=vault_name, jobId=job_id)
print(response)
'''
