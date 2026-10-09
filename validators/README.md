# Cookchain validator candidate — 2026.10.09.1

This Linux package starts a new independent Cookchain Mainnet candidate. It does not admit the candidate into consensus. Existing validators must approve and vote for admission. No consensus transition, staking deployment or automatic vote is performed.

## Install and synchronize

Use a dedicated Linux host with Docker Engine, Compose v2 and Python 3. Start with 4 CPU cores, 8 GB RAM and 100 GB free SSD; storage requirements grow with the chain. Use a stable public IPv4, accurate time synchronization and reliable connectivity. Allow inbound TCP/UDP 30303. Do not expose 8545 or 8546 publicly. Run as a dedicated non-root operator with Docker access; Docker access itself is privileged.

Download the validator ZIP and its checksum from the release page, then:

```sh
sha256sum -c cookchain-validator-candidate-v2026.10.09.1-linux.zip.sha256
unzip cookchain-validator-candidate-v2026.10.09.1-linux.zip
cd cookchain-validator-candidate
python3 install.py --public-ip YOUR_PUBLIC_IPV4
docker compose logs --tail 50 node
python3 check.py
```

The node key is generated locally by Besu. Never send `data/key`, copy an existing validator identity or run the same key on two hosts. Back up the key privately. `data/key.pub` and `data/validator-address` are public. HTTP RPC is loopback-only and includes QBFT for local verification. WebSocket RPC is disabled. Do not place a public reverse proxy in front of this management RPC; operate a separate RPC node for public service.

`--prepare-only` renders and validates Compose without generating an identity or starting a node. After that, start the explicit export and Compose commands described in the operator runbook; do not rerun the installer over existing data.

## Apply for admission

Run `python3 check.py` after synchronization. It checks chain ID, exact genesis, block agreement against the reference RPC, sync status, peers, block progress and validator membership. A successful technical preflight is a point-in-time check, not a security audit or approval.

Open a validator application issue in this repository using the application template. Submit the public report, operator contact, hosting/network details, monitoring plan and upgrade availability. The report includes the public IP in the enode. Never attach private keys, passwords, full logs or backups.

Governance reviews the application, independently checks identity, peer connectivity and operational readiness, and coordinates admission with existing validators. Acceptance of an application alone does not activate the candidate. The candidate is active only after its address appears in the on-chain validator set. `check.py` reports `pending-governance`, `active-on-chain` or `unknown`; RPC failure never implies removal.

## Operation and exit

See `OPERATOR-RUNBOOK.md`. Monitor block progress, peers, sync lag, disk capacity, clock and consensus participation. Upgrade one validator at a time after confirming the previous validator recovered. Preserve the identity and database. Request coordinated removal before shutdown; confirm on-chain removal before retiring the identity.

## Current boundaries

This package retains the reviewed 2026.10.09.1 RPC package's pinned Besu 26.9.0 image and documented local lifecycle patch. It does not enable the prepared staking registry or promise rewards. Any deposit requirements and reward terms must be explicitly confirmed before admission. Public bootstrap admission and a fresh end-to-end synchronization test are still unconfirmed for this release; it is published as a prerelease.

Mainnet: chain ID 20261001, COOK (18 decimals). Explorer: https://cookscan.net/ . Technical information: https://swap.cookscan.net/technical-information.html .
