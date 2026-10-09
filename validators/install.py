#!/usr/bin/env python3
"""Prepare a new candidate; never vote or change network consensus."""
import argparse, hashlib, ipaddress, json, os, subprocess
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description='Install a Cookchain validator candidate. Admission requires governance and validator voting.')
    parser.add_argument('--public-ip', required=True)
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args()
    ip = ipaddress.ip_address(args.public_ip)
    if ip.version != 4 or not ip.is_global:
        raise SystemExit('A public IPv4 address is required')
    if os.name != 'posix':
        raise SystemExit('Run this installer on Linux')
    manifest = json.loads((root / 'manifest.json').read_text())
    for name, digest in manifest['files'].items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest:
            raise SystemExit('Checksum mismatch: ' + name)
    if (root / 'compose.yaml').exists() or (root / 'data').exists():
        raise SystemExit('Existing installation found. Preserve its key; follow the upgrade runbook.')
    data = root / 'data'
    data.mkdir(mode=0o700)
    (data / 'static-nodes.json').write_bytes((root / 'config/static-nodes.json').read_bytes())
    template = (root / 'compose.template.yaml').read_text()
    (root / 'compose.yaml').write_text(template.replace('__USER__', str(os.getuid()) + ':' + str(os.getgid())).replace('__PUBLIC_IP__', str(ip)))
    (root / 'candidate.json').write_text(json.dumps({'publicIp':str(ip),'p2pPort':30303,'admission':'pending'}, indent=2)+'\n')
    subprocess.run(['docker','compose','config','--quiet'], cwd=root, check=True)
    if args.prepare_only:
        print('Prepared only. No identity generated and no node started.')
        return
    for command, filename in [('export-address','validator-address'), ('export','key.pub')]:
        subprocess.run(['docker','compose','run','--rm','--no-deps','node','--data-path=/data','public-key',command,'--to=/data/'+filename], cwd=root, check=True)
    subprocess.run(['docker','compose','up','-d','node'], cwd=root, check=True)
    print('Candidate started. Keep data/key private. Run python3 check.py when synchronized. Admission is still pending.')

if __name__ == '__main__':
    main()
