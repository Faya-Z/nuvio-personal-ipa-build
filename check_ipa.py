#!/usr/bin/env python3
"""Reject malformed/non-device/incompatible archives; not a LiveContainer test."""
import argparse, plistlib, struct, zipfile

def version(s):
    v = tuple(int(x) for x in str(s).split('.'))
    return v + (0,)*(max(0,3-len(v)))

def arm64(data):
    if len(data) < 8: return False
    magic = data[:4]
    if magic in (b'\xcf\xfa\xed\xfe', b'\xfe\xed\xfa\xcf'):
        endian = '<' if magic == b'\xcf\xfa\xed\xfe' else '>'
        return len(data) >= 32 and struct.unpack_from(endian+'I',data,4)[0] == 0x0100000c
    if magic in (b'\xca\xfe\xba\xbe',b'\xbe\xba\xfe\xca',b'\xca\xfe\xba\xbf',b'\xbf\xba\xfe\xca'):
        e = '>' if magic[0] == 0xca else '<'
        n = struct.unpack_from(e+'I',data,4)[0]
        step = 32 if magic in (b'\xca\xfe\xba\xbf',b'\xbf\xba\xfe\xca') else 20
        if n > 64 or len(data) < 8+n*step: return False
        return any(struct.unpack_from(e+'I',data,8+i*step)[0]==0x0100000c for i in range(n))
    return False

def verify(path, max_min_os):
    with zipfile.ZipFile(path) as z:
        if z.testzip() is not None: raise ValueError('Corrupt ZIP member')
        names = z.namelist()
        roots = [n for n in names if n.startswith('Payload/') and n.endswith('.app/Info.plist') and n.count('/')==2]
        if len(roots)!=1: raise ValueError('Expected exactly one top-level app')
        root=roots[0].rsplit('/',1)[0]
        p=plistlib.loads(z.read(roots[0]))
        exe=p.get('CFBundleExecutable','')
        if not exe or '/' in exe or '\\' in exe: raise ValueError('Invalid executable name')
        if 'iPhoneOS' not in p.get('CFBundleSupportedPlatforms',[]): raise ValueError('Not an iOS device build')
        minimum=p.get('MinimumOSVersion')
        if not minimum or version(minimum)>version(max_min_os): raise ValueError(f'Minimum iOS {minimum} exceeds or is unknown for {max_min_os}')
        with z.open(root+'/'+exe) as f:
            if not arm64(f.read(4096)): raise ValueError('Missing arm64 device executable')
        if any(n.startswith(root+'/_CodeSignature/') for n in names): raise ValueError('Expected unsigned application')
        print(f"Archive checks passed: {p.get('CFBundleIdentifier')} {p.get('CFBundleShortVersionString')}, minimum iOS {minimum}, arm64")
        print('This checks package structure, not LiveContainer compatibility.')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('ipa');p.add_argument('--max-min-os',default='18.3');a=p.parse_args();verify(a.ipa,a.max_min_os)
