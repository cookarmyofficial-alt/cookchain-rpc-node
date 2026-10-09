from pathlib import Path
import ast, hashlib, json, shutil, zipfile

base = Path(__file__).resolve().parent.parent
root = base/'dist/cookchain-validator-candidate'
root.mkdir(parents=True, exist_ok=True)
base_manifest = json.loads((base/'manifest.json').read_text())
for name, digest in base_manifest['files'].items():
    if name in ['README.md','install.py','check.py','nginx-rpc.conf.example']:
        continue
    data = (base/name).read_bytes()
    assert hashlib.sha256(data).hexdigest() == digest
    p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
for name in ['README.md','install.py','check.py','OPERATOR-RUNBOOK.md']:
    shutil.copy2(Path(__file__).resolve().parent/name,root/name)
shutil.copy2(base/'patch/manifest.json',root/'patch/manifest.json')
compose=(Path(__file__).resolve().parent/'compose.template.yaml').read_text()
compose=compose.replace('name: cookchain-public-node','name: cookchain-validator-candidate').replace('--rpc-http-api=ETH,NET,WEB3','--rpc-http-api=ETH,NET,WEB3,QBFT').replace('--rpc-ws-enabled=true','--rpc-ws-enabled=false')
compose='\n'.join(line for line in compose.splitlines() if not any(x in line for x in ['--rpc-http-cors-origins','--rpc-ws-host','--rpc-ws-port','--rpc-ws-api','--rpc-ws-max-active-connections','127.0.0.1:8546']))+'\n'
(root/'compose.template.yaml').write_text(compose)
(root/'.gitignore').write_text('data/\ncompose.yaml\ncandidate.json\ncandidate-report.json\n.env\n*.pem\n*.key\n__pycache__/\n*.zip\n')
for p in root.rglob('*.py'):ast.parse(p.read_text(),filename=str(p))
names=sorted(p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p.name!='manifest.json')
# patch/manifest.json is also a package file.
names.append('patch/manifest.json')
m={'version':'2026.10.09.1','chainId':20261001,'genesisHash':base_manifest['genesisHash'],'releaseStatus':'prerelease','admission':'controlled-qbft-voting','publicPeerOpening':'not-reconfirmed','files':{n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in sorted(set(names))}}
(root/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
archive=root.parent/'cookchain-validator-candidate-v2026.10.09.1-linux.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for name in list(m['files'])+['manifest.json']:
        assert not any(p in ['data','key','.env'] for p in Path(name).parts)
        z.write(root/name,'cookchain-validator-candidate/'+name)
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
archive.with_suffix('.zip.sha256').write_text(hashlib.sha256(archive.read_bytes()).hexdigest()+'  '+archive.name+'\n')
print(archive,archive.stat().st_size)
