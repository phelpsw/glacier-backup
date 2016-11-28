Default AWS credentials are assumed to be in ~/.aws/configure

GPG keys are assumed to be in ~/.gnupg/

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

