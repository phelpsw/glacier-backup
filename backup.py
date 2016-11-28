#!/usr/bin/env python3

import boto3
from datetime import datetime
import os
import tarfile
import argparse
import tempfile
import gnupg

# TODO
# - Verbosity
# - Better crypto home dir selection
# - Better aws account selection
# - Region setting


def upload_file_list(filelist):
    archive_name = 'glacier_archive_{}'.format(
        datetime.utcnow().strftime('%Y%m%d%H%M%S'))
    print(archive_name)

    client = boto3.client('glacier')
    response = client.create_vault(vaultName=archive_name,
                                   accountId='-')
    print(response)
    for _file in filelist:
        name = os.path.basename(_file)
        response = client.upload_archive(vaultName=archive_name,
                                         archiveDescription=name,
                                         body=_file)
        print(response)
    hostname = open('/etc/hostname').read().rstrip()
    timestamp = datetime.utcnow().isoformat()
    client.add_tags_to_vault(vaultName=archive_name,
                             Tags={'hostname': hostname,
                                   'timestamp': timestamp})


def create_backups(directories, unencrypted, cryptokey, dry_run):
    with tempfile.TemporaryDirectory() as _dir:
        files_to_upload = []
        for bkupdir in directories:
            abspath = os.path.abspath(bkupdir)
            bkupfile = os.path.basename(abspath) + '.tar.xz'
            absbkfile = os.path.join(_dir, bkupfile)

            if not os.path.isdir(abspath):
                print('Unknown directory {}'.format(abspath))
                continue

            # Create compressed tar file of the target directory
            tar = tarfile.open(absbkfile, "w:xz")
            tar.add(abspath,
                    arcname=os.path.basename(abspath),
                    recursive=True)
            tar.close()

            if not unencrypted:
                # Encrypt archive file
                abscryptfile = '{}.gpg'.format(absbkfile)
                gpg = gnupg.GPG(gnupghome='~/.gnupg')
                with open(absbkfile, 'rb') as f:
                    status = gpg.encrypt_file(
                        f, recipients=[cryptokey],
                        output=abscryptfile,
                        armor=False)
                    print(abscryptfile)
                    if not status.ok:
                        print('Encryption error')
                        continue
                os.remove(absbkfile)

            # Add appropriate file to list of files to upload
            if not unencrypted:
                files_to_upload.append(abscryptfile)
            else:
                files_to_upload.append(absbkfile)

        # Upload archive to glacier
        print(files_to_upload)
        if not dry_run:
            upload_file_list(files_to_upload)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('directories', metavar='N', type=str, nargs='+',
                        help='List of directories to backup.')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--unencrypted', action='store_true')
    parser.add_argument('--cryptokey',
                        type=str,
                        default='phelps@williamslabs.com',
                        help='Encryption key to encrypt for.')
    args = parser.parse_args()
    start_time = datetime.utcnow()
    create_backups(args.directories,
                   args.unencrypted,
                   args.cryptokey,
                   args.dry_run)
    end_time = datetime.utcnow()
    print('Run duration {}'.format(end_time - start_time))
