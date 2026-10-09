#!/usr/bin/env python3
"""Read-only candidate checks; report includes public identity only."""
import argparse, datetime, json, re, time, urllib.request
from pathlib import Path

def rpc(url, method, params=None):
    req = urllib.request.Request(url, data=json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params or []}).encode(), headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req, timeout=15) as response:
        result = json.load(response)
    if 'error' in result:
        raise RuntimeError(method + ': ' + str(result['error']))
    return result['result']

def assess(local, reference, address, expected_genesis):
    reasons = []
    if local['chainId'] != 20261001 or reference['chainId'] != 20261001:
        reasons.append('Wrong chain ID')
    if local['genesis'].lower() != expected_genesis.lower() or reference['genesis'].lower() != expected_genesis.lower():
        reasons.append('Wrong genesis hash')
    if local['syncing'] is not False:
        reasons.append('Node is still synchronizing')
    if local['peers'] < 2:
        reasons.append('At least two peers required for this technical preflight')
    if abs(reference['height'] - local['height']) > 5:
        reasons.append('Node differs from reference height by more than five blocks')
    if local['heightAfter'] <= local['height']:
        reasons.append('No block progress observed')
    if local['commonHash'].lower() != reference['commonHash'].lower():
        reasons.append('Block hash differs from reference at the same height')
    active = address.lower() in [a.lower() for a in local['validators']]
    return {'technicalPreflightPassed':not reasons,'issues':reasons,'admission':'active-on-chain' if active else 'pending-governance','validatorAddress':address}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--reference-rpc', default='https://rpc.cookscan.net/evm')
    parser.add_argument('--observe-seconds', type=int, default=6)
    args = parser.parse_args()
    if not 3 <= args.observe_seconds <= 60:
        raise SystemExit('Observation must be between 3 and 60 seconds')
    root = Path(__file__).resolve().parent
    try:
        manifest = json.loads((root / 'manifest.json').read_text())
        candidate = json.loads((root / 'candidate.json').read_text())
        address = (root / 'data/validator-address').read_text().strip()
        public_key = (root / 'data/key.pub').read_text().strip().removeprefix('0x')
        if not re.fullmatch(r'0x[0-9a-fA-F]{40}', address) or not re.fullmatch(r'[0-9a-fA-F]{128}', public_key):
            raise RuntimeError('Invalid exported public identity')
        local_url = 'http://127.0.0.1:8545'
        def snapshot(url):
            return {'chainId':int(rpc(url,'eth_chainId'),16),'genesis':rpc(url,'eth_getBlockByNumber',['0x0',False])['hash'],'height':int(rpc(url,'eth_blockNumber'),16)}
        local, reference = snapshot(local_url), snapshot(args.reference_rpc)
        common = hex(min(local['height'], reference['height']))
        for data, url in [(local,local_url),(reference,args.reference_rpc)]:
            data['commonHash'] = rpc(url,'eth_getBlockByNumber',[common,False])['hash']
        local.update(syncing=rpc(local_url,'eth_syncing'), peers=int(rpc(local_url,'net_peerCount'),16), validators=rpc(local_url,'qbft_getValidatorsByBlockNumber',['latest']))
        time.sleep(args.observe_seconds)
        local['heightAfter'] = int(rpc(local_url,'eth_blockNumber'),16)
        result = assess(local, reference, address, manifest['genesisHash'])
        result.update(checkedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),chainId=20261001,enode='enode://'+public_key+'@'+candidate['publicIp']+':'+str(candidate['p2pPort']),height=local['heightAfter'],peers=local['peers'],referenceHeight=reference['height'],commonHeight=int(common,16))
    except Exception as exc:
        result = {'technicalPreflightPassed':False,'admission':'unknown','issues':[str(exc)],'checkedAt':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    (root / 'candidate-report.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    if not result['technicalPreflightPassed']:
        raise SystemExit(1)

if __name__ == '__main__':
    main()
