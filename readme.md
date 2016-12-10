Default AWS credentials are assumed to be in ~/.aws/configure

GPG keys are assumed to be in ~/.gnupg/

```
sudo apt-get install python3-dev python3-pip awscli gnupg
pip3 install setuptools wheel
pip3 install boto3 gnupg
```

Configure aws credentials
```
aws configure
```

Key configuration
```
gpg --gen-key
# Select RSA (sign only) (4)
# 4096 bits long
# Does not expire
# Enter name and email
# No passphrase b/c we need to run this in a daemon with no agent available
# wait a while
gpg --edit-key backup@williamslabs.com
# Elgamal (5)
# 4096
# Does not expire
save
```

### Backup
```
python3 backup.py testdir/ ~/projects/test/
```

### Decrypt
```
gpg --decrypt-files test.tar.xz.gpg
```

### Test Compression and tarball
```
tar -Jtvf testdir.tar.xz
```

TODO:
 - Create S3 bucket if one doesn't exist
 - Add index file to bucket with hashes and timestamps for each backup file
 - If hash doesn't change, don't bother backing up
 - If hash does change, upload new file to glacier 
http://stackoverflow.com/questions/3431825/generating-an-md5-checksum-of-a-file#3431835


Alt approach not requring index file
 - Create volume for a given directory - host combo
 - tag with hash of file, timestamp, host, directory

