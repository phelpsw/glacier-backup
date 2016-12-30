#!/usr/bin/env python

import boto3
import time

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


vault_name = 'glacier_archive_20161211000256'

response = client.initiate_job(vaultName=vault_name,
                               jobParameters={'Format': 'JSON',
                                              'Type': 'inventory-retrieval',
                                             }
                              )
print(response)
job_id = response['jobId']

response = client.describe_job(vaultName=vault_name, jobId=job_id)
while not response['Completed']:
    print('waiting 60 sec')
    time.sleep(60)
    response = client.describe_job(vaultName=vault_name, jobId=job_id)
    print(response)


response = client.get_job_output(vaultName=vault_name, jobId=job_id)
print(response)

'''
{'StatusMessage': 'Succeeded', 'CompletionDate': '2016-12-29T23:49:16.115Z', 'CreationDate': '2016-12-29T19:32:13.166Z', 'ResponseMetadata': {'RetryAttempts': 0, 'HTTPStatusCode': 200, 'RequestId': 'JtIwcZtDVBwEgMQigjEq6zr7HSv2bRkej9y-oPopxDVhK60', 'HTTPHeaders': {'content-length': '685', 'x-amzn-requestid': 'JtIwcZtDVBwEgMQigjEq6zr7HSv2bRkej9y-oPopxDVhK60', 'date': 'Thu, 29 Dec 2016 23:49:36 GMT', 'content-type': 'application/json'}}, 'InventorySizeInBytes': 476, 'Action': 'InventoryRetrieval', 'StatusCode': 'Succeeded', 'InventoryRetrievalParameters': {'Format': 'JSON'}, 'VaultARN': 'arn:aws:glacier:us-east-1:316132619292:vaults/glacier_archive_20161211000256', 'JobId': 't_c1a_ykbEo_Rs_-LbFzoVN4ybboVwhMAG9z5D2FxyI9sfWf-mDwpzlh-GDqSyThDKknOOibNdIK2Od6PR7zTrEDF1UU', 'Completed': True}
{'status': 200, 'ResponseMetadata': {'RetryAttempts': 0, 'HTTPStatusCode': 200, 'RequestId': '1b0Oicjftf7FOAs2DdoXbSFBxvtAYiW_5R-mMC0y9J1y_PQ', 'HTTPHeaders': {'accept-ranges': 'bytes', 'content-length': '476', 'x-amzn-requestid': '1b0Oicjftf7FOAs2DdoXbSFBxvtAYiW_5R-mMC0y9J1y_PQ', 'date': 'Thu, 29 Dec 2016 23:49:36 GMT', 'content-type': 'application/json'}}, 'body': <botocore.response.StreamingBody object at 0x7fe83507cbe0>, 'acceptRanges': 'bytes', 'contentType': 'application/json'}
'''

