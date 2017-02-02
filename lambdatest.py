import boto3
import botocore
import json

def upload_to_bucket(obj, filename):
    bucket_name = 'phelps-testbucket'
    s3 = boto3.client('s3')
    try:
        response = s3.get_bucket_location(Bucket=bucket_name)
        print 'upload_to_bucket', response
    except botocore.exceptions.ClientError:
        response = s3.create_bucket(ACL='private',
                                    Bucket=bucket_name)
        print 'upload_to_bucket', response
    response = s3.upload_fileobj(obj, bucket_name, filename)

def my_handler(event, context):
    print event, type(event)
    #print context # LambdaContext type
    inventory = 'fake inventory'
    for record in event['Records']:
        if 'Sns' in record:
            msg = json.loads(record['Sns']['Message'])
            print msg
            glacier_client = boto3.client('glacier')
            vault_name = msg['VaultARN'].split('/')[1]
            if msg['Action'] == 'InventoryRetrieval':
                response = glacier_client.get_job_output(vaultName=vault_name,
                                                         jobId=msg['JobId'])
                inventory = response['body']
                upload_to_bucket(inventory, 'inventory.txt')
            elif msg['Action'] == 'ArchiveRetrieval':
                response = glacier_client.get_job_output(vaultName=vault_name,
                                                         jobId=msg['JobId'])
                print response
                inventory = response['body']
                upload_to_bucket(inventory, 'archive.tar.xz.gpg')
            else:
                print 'Unknown action {}'.format(msg['Action'])
    '''
    sns = boto3.client('sns')
    number = '+12345678901'
    response = sns.publish(PhoneNumber=number, Message='example text message' )
    print response
    '''
    # Add DKIM key registration to your sending domain before running this code.
    # http://docs.aws.amazon.com/ses/latest/DeveloperGuide/verify-addresses-and-domains.html

    ses = boto3.client('ses')
    me = 'no-reply@williamslabs.com'
    you = ['boto3@williamslabs.com']
    subject = 'Lambda Job Report'
    bodytext = 'This is the message body'
    destination = {'ToAddresses' : you,
                   'CcAddresses' : [],
                   'BccAddresses' : []}

    paginator = ses.get_paginator('list_identities')
    response_iterator = paginator.paginate()

    identities = []
    for page in response_iterator:
        identities.extend(page['Identities'])

    for addr in you:
        if addr not in identities and \
           addr.split('@')[1] not in identities:
            # This is only needed while in the sandbox environment.  Once SES
            # sending limit has been increased, destination verification is no
            # longer required
            print 'verifying {}'.format(addr)
            ses.verify_email_identity(EmailAddress=addr)

    message = {'Subject' : {'Data' : subject},
               'Body': {'Text' : {'Data' : bodytext}}}
    result = ses.send_email(Source = me,
                            Destination = destination,
                            Message = message)
    print result
    return True

