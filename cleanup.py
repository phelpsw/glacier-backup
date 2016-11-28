#!/usr/bin/env python3
'''
This program looks through glacier backups in a particular region and applies a
backup policy to cull unnecessary backup volumes.
'''

import boto3
import argparse
import yaml

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--policy', type=str,
                        help='Path to yaml policy file to apply.',
                        default='policy.yml')
    parser.add_argument('--hostname', type=str,
                        help='Hostname to cleanup backups for.',
                        default=open('/etc/hostname').read().rstrip())
    parser.add_argument('--region', type=str,
                        help='Glacier region to cleanup',
                        default='us-west-2')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    client = boto3.client('glacier')
    vaults = client.list_vaults()
    print(vaults)
    print(yaml.load(open(args.policy, 'r')))
    for v in vaults['VaultList']:
        print(v['CreationDate'])
