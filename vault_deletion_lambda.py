import boto3
import botocore
import json


def send_mail(to, bodytext):
    ses = boto3.client('ses')
    me = 'no-reply@williamslabs.com'
    you = to
    subject = 'Lambda Job Report'
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

def my_handler(event, context):
    print event, type(event)
    for record in event['Records']:
        if 'Sns' in record:
            msg = json.loads(record['Sns']['Message'])
            print msg
            glacier = boto3.client('glacier')
            vault_name = msg['VaultARN'].split('/')[1]
            if msg['Action'] == 'InventoryRetrieval':
                response = glacier.get_job_output(vaultName=vault_name,
                                                         jobId=msg['JobId'])
                data = json.loads(response['body'].read())
                archives = data['ArchiveList']
                for archive in archives:
                    glacier.delete_archive(vaultName=vault_name,
                                                  archiveId=archive['ArchiveId'])

                # Try to delete the vault, if this fails because archives were
                # too recently deleted, request another inventory (with this
                # lambda function as the callback)
                try:
                    glacier.delete_vault(vaultName=vault_name)
                except botocore.exceptions.ClientError:
                    print 'Unable to delete vault, scheduling inventory'
                    # Create glacier inventory request
                    print record['EventSubscriptionArn']
                    print msg['SNSTopic']
                    topic_arn = ':'.join(record['EventSubscriptionArn'].split(':')[:-1])
                    print vault_name, topic_arn
                    glacier.initiate_job(vaultName=vault_name,
                                         jobParameters={'Format': 'JSON',
                                                        'Type': 'inventory-retrieval',
                                                        'SNSTopic': topic_arn
                                                       })
            else:
                print 'Unknown action {}'.format(msg['Action'])
    send_mail(['boto3@williamslabs.com'], 'deletion job running')
    return True

