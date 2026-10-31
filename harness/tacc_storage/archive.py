#!/usr/bin/env python3
"""Non-destructive archive creation and content verification for new jobs."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import tarfile


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def inventory(root):
    result={'.':dict(kind='directory')};stack=[root]
    while stack:
        directory=stack.pop()
        with os.scandir(directory) as entries:
            for entry in entries:
                p=Path(entry.path);rel=str(p.relative_to(root))
                if entry.is_symlink():result[rel]=dict(kind='symlink',target=os.readlink(p))
                elif entry.is_dir(follow_symlinks=False):result[rel]=dict(kind='directory');stack.append(p)
                elif entry.is_file(follow_symlinks=False):
                    s=entry.stat(follow_symlinks=False)
                    result[rel]=dict(kind='file',sha256=sha(p),size=s.st_size)
                else:raise RuntimeError('Special entry; preserve original: '+str(p))
    return result

def pack(source,original,archive):
    # Explicit TarInfo avoids following links or implicit hard-link aliases.
    with archive.open('xb') as stream:
        with tarfile.open(fileobj=stream,mode='w:gz',compresslevel=1) as tar:
            for rel,row in sorted(original.items()):
                path=source if rel=='.' else source/rel
                name='output' if rel=='.' else 'output/'+rel
                s=path.lstat()
                info=tarfile.TarInfo(name);info.mode=stat.S_IMODE(s.st_mode)
                info.mtime=s.st_mtime;info.uid=s.st_uid;info.gid=s.st_gid
                if row['kind']=='directory':info.type=tarfile.DIRTYPE;tar.addfile(info)
                elif row['kind']=='symlink':
                    info.type=tarfile.SYMTYPE;info.linkname=row['target'];tar.addfile(info)
                else:
                    if path.is_symlink():raise RuntimeError('File type changed during packing')
                    info.size=row['size'];info.type=tarfile.REGTYPE
                    with path.open('rb') as f:tar.addfile(info,f)

def verify(archive,original):
    names=set()
    with tarfile.open(archive,'r:gz') as tar:
        for member in tar:
            path=PurePosixPath(member.name)
            if path.is_absolute() or '..' in path.parts or not path.parts or path.parts[0]!='output':
                raise RuntimeError('Unsafe archive name')
            rel='.' if len(path.parts)==1 else str(PurePosixPath(*path.parts[1:]))
            if rel in names or rel not in original:raise RuntimeError('Duplicate/unexpected archive entry')
            names.add(rel);row=original[rel]
            if row['kind']=='directory':
                if not member.isdir():raise RuntimeError('Directory type differs')
            elif row['kind']=='symlink':
                if not member.issym() or member.linkname!=row['target']:raise RuntimeError('Symlink differs')
            else:
                if not member.isfile() or member.size!=row['size']:raise RuntimeError('File type/size differs')
                h=hashlib.sha256()
                with tar.extractfile(member) as f:
                    for b in iter(lambda:f.read(1048576),b''):h.update(b)
                if h.hexdigest()!=row['sha256']:raise RuntimeError('Extracted stream hash differs: '+rel)
    if names!=set(original):raise RuntimeError('Archive does not list every original entry')
