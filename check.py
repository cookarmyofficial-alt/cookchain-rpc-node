#!/usr/bin/env python3
import json,urllib.request
from pathlib import Path
manifest=json.loads((Path(__file__).parent/'manifest.json').read_text())
def rpc(m,p=[]):
    r=urllib.request.Request('http://127.0.0.1:8545',data=json.dumps({'jsonrpc':'2.0','id':1,'method':m,'params':p}).encode(),headers={'Content-Type':'application/json'})
    j=json.load(urllib.request.urlopen(r,timeout=15))
    if 'error' in j:raise RuntimeError(j['error'])
    return j['result']
assert int(rpc('eth_chainId'),16)==20261001,'Wrong chain'
assert rpc('eth_getBlockByNumber',['0x0',False])['hash'].lower()==manifest['genesisHash'].lower(),'Wrong genesis'
print(json.dumps({'chainId':20261001,'height':int(rpc('eth_blockNumber'),16),'peers':int(rpc('net_peerCount'),16),'syncing':rpc('eth_syncing')},indent=2))
