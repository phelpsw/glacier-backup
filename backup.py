#!/usr/bin/env python3

import boto3
from datetime import datetime
import os
import tarfile
import argparse
import tempfile
import gnupg
from multiprocessing import Pool

# TODO
# - Verbosity
# - Better crypto home dir selection
# - Better aws account selection
# - Region setting


def upload_file(archive, _file):
    name = os.path.basename(_file)
    client = boto3.client('glacier')
    response = client.upload_archive(vaultName=archive,
                                     archiveDescription=name,
                                     body=_file)
    print(response)
    hostname = open('/etc/hostname').read().rstrip()
    timestamp = datetime.utcnow().isoformat()
    client.add_tags_to_vault(vaultName=archive_name,
                             Tags={'hostname': hostname,
                                   'timestamp': timestamp})


def create_backup(args):
    path, scratch, cryptokey, archive, dry_run = args

    abspath = os.path.abspath(path)
    bkupfile = os.path.basename(abspath) + '.tar.xz'
    absbkfile = os.path.join(scratch, bkupfile)

    if not os.path.isdir(abspath):
        print('Unknown directory {}'.format(abspath))
        return

    # Create compressed tar file of the target directory
    tar = tarfile.open(absbkfile, "w:xz")
    tar.add(abspath,
	    arcname=os.path.basename(abspath),
	    recursive=True)
    tar.close()

    # Encrypt archive file
    abscryptfile = '{}.gpg'.format(absbkfile)
    gpg = gnupg.GPG(homedir=os.path.join(scratch, 'gnupg'))
    gpg.recv_keys(cryptokey, keyserver='hkp://pgp.mit.edu')
    with open(absbkfile, 'rb') as f:
        status = gpg.encrypt(
            f, cryptokey,
            output=abscryptfile,
            armor=False)
        print(abscryptfile)
        if not status.ok:
            print('Encryption error')
            return
    os.remove(absbkfile)

    if not dry_run:
        upload_file(archive, abscryptfile)
    os.remove(abscryptfile)
    

def create_backups(directories, scratch, cryptokey, threads, dry_run):
    archive = 'glacier_archive_{}'.format(
        datetime.utcnow().strftime('%Y%m%d%H%M%S'))
    client = boto3.client('glacier')
    response = client.create_vault(vaultName=archive,
                                   accountId='-')
    if scratch:
        process_args = [(x, scratch, cryptokey, archive, dry_run) for x in directories]
        pool = Pool(threads)
        pool.map(create_backup, process_args)
    else:
        with tempfile.TemporaryDirectory() as _dir:
            process_args = [(x, _dir, cryptokey, archive, dry_run) for x in directories]
            pool = Pool(threads)
            pool.map(create_backup, process_args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('directories', metavar='N', type=str, nargs='+',
                        help='List of directories to backup.')
    parser.add_argument('--scratch', type=str)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--threads', type=int, default=1)
    parser.add_argument('--cryptokey',
                        type=str,
                        help='Encryption key to encrypt for.')
    args = parser.parse_args()
    start_time = datetime.utcnow()
    create_backups(args.directories,
                   args.scratch,
                   args.cryptokey,
                   args.threads,
                   args.dry_run)
    end_time = datetime.utcnow()
    print('Run duration {}'.format(end_time - start_time))
