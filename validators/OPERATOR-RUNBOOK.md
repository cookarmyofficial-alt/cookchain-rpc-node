# Controlled validator admission and operation

## Prepare-only completion

In the prepared package directory, these commands generate only the candidate's new local identity and start its node:

```sh
docker compose run --rm --no-deps node --data-path=/data public-key export-address --to=/data/validator-address
docker compose run --rm --no-deps node --data-path=/data public-key export --to=/data/key.pub
docker compose up -d node
python3 check.py
```

If installation fails, inspect the error and retain generated files and keys. Validate `docker compose config --quiet`, finish only the missing export/start steps and rerun the preflight. Do not delete `data` to retry an established node.

## Governance checklist

1. Review operator identity and contact, independent hosting, monitoring, incident response and availability for coordinated upgrades.
2. Independently check chain/genesis, synchronized height and same-height hash, peer reachability and the candidate's public identity. Observe sustained health, not just one successful report.
3. Confirm the actual current validator-selection mode and active set on trusted management RPC. This package assumes block-header QBFT voting. If contract selection is activated later, use its separately reviewed procedure.
4. Record approval and coordinate existing operators. The commands below are manual references, not a script that runs automatically.
5. Existing validators vote via their own local management RPC. More than half of existing validators must publish matching votes; proposal submission is not confirmation of admission.
6. Verify the new identity in `qbft_getValidatorsByBlockNumber("latest")` and confirm sustained consensus participation using signer metrics and operator monitoring. Discard obsolete proposals after confirmation.

On each approving existing validator's authorized local management endpoint (replace the candidate address; do not expose QBFT to the internet):

```sh
curl http://127.0.0.1:8545 -H 'Content-Type: application/json' --data '{"jsonrpc":"2.0","id":1,"method":"qbft_proposeValidatorVote","params":["CANDIDATE_ADDRESS",true]}'
curl http://127.0.0.1:8545 -H 'Content-Type: application/json' --data '{"jsonrpc":"2.0","id":1,"method":"qbft_getValidatorsByBlockNumber","params":["latest"]}'
curl http://127.0.0.1:8545 -H 'Content-Type: application/json' --data '{"jsonrpc":"2.0","id":1,"method":"qbft_discardValidatorVote","params":["CANDIDATE_ADDRESS"]}'
```

Some existing nodes deliberately do not expose QBFT. Do not broaden their RPC permissions as part of candidate installation. Governance must arrange reviewed local management access separately. No existing validator is restarted or reconfigured by this package.

## Monitoring, upgrades and exit

Run `check.py` periodically through your monitoring system; nonzero exit means attention is required. Alert on stalled height, sync lag, lost peers, disk exhaustion and clock problems. Confirm signer participation separately: membership alone does not prove the validator signs blocks.

For upgrades, obtain a reviewed compatible release, verify hashes, preserve the existing key/database, review network transitions and coordinate with governance. Recreate one node, confirm resumed participation, then proceed to the next. Do not rerun the fresh installer over existing data, change genesis unilaterally or start a second instance with the same key.

For exit, coordinate replacement and removal votes (`false` instead of `true`) while maintaining required quorum and redundancy. Confirm removal on-chain before planned shutdown. Discard stale votes. There is no automatic collateral release in this package.

Official Besu reference: https://github.com/besu-eth/besu-docs/blob/main/docs/private-networks/how-to/configure/consensus/qbft.md
