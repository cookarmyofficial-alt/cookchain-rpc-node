#!/usr/bin/env python3
import argparse,hashlib,ipaddress,json,os,subprocess
from pathlib import Path
root=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description='Install a Cookchain non-validator node. No validator key or stake is required.')
parser.add_argument('--public-ip',required=True);parser.add_argument('--prepare-only',action='store_true');args=parser.parse_args()
ip=ipaddress.ip_address(args.public_ip)
if ip.version!=4 or not ip.is_global:raise SystemExit('A public IPv4 address is required')
manifest=json.loads((root/'manifest.json').read_text())
for name,digest in manifest['files'].items():
    if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise SystemExit('Checksum mismatch: '+name)
target=root/'compose.yaml'
if target.exists():raise SystemExit('Already configured. Keep the existing data/key and use the upgrade procedure.')
data=root/'data';data.mkdir(mode=0o700,exist_ok=True)
peers=json.loads((root/'config/static-nodes.json').read_text())
(data/'static-nodes.json').write_text(json.dumps(peers,indent=2))
target.write_text((root/'compose.template.yaml').read_text().replace('__USER__',str(os.getuid())+':'+str(os.getgid())).replace('__PUBLIC_IP__',str(ip)))
subprocess.run(['docker','compose','config','--quiet'],cwd=root,check=True)
if not args.prepare_only:subprocess.run(['docker','compose','up','-d'],cwd=root,check=True)
print('Non-validator node configured. Keep data/key private; do not share or overwrite it. Run python3 check.py after synchronization.')
