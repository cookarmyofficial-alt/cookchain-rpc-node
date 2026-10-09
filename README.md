# Cookchain RPC node — 2026.10.09.1

This installs a new non-validator Besu node for Cookchain Mainnet (chain ID 20261001, native COOK, 18 decimals). It downloads and independently verifies the existing chain. It does not create a new network or confer validator status.

## Installation

Use Linux with Docker Engine, Docker Compose v2, Python 3, a public IPv4 address and reliable storage. Start with at least 4 CPU cores, 8 GB RAM and 100 GB free SSD; these are initial sizing recommendations, not a guaranteed long-term storage requirement. Allow inbound TCP and UDP 30303. HTTP and WebSocket RPC bind only to loopback. Configure your own HTTPS reverse proxy if offering RPC publicly.

Verify the archive SHA-256, extract into a new directory, then run:

```sh
python3 install.py --public-ip YOUR_PUBLIC_IPV4
docker compose logs --tail 50 node
python3 check.py
```

Do not install over an existing node directory. The installer verifies package file hashes and generates a unique node key on first startup. Never distribute data/key. Synchronization can take time. check.py verifies the chain ID and exact genesis hash and reports height, peers and sync status.

Public peer opening is pending operator approval at publication time. The existing Cookscan static peer is included; full bootstrap availability will be confirmed after the public gateway is opened.

## RPC

The package exposes ETH, NET and WEB3 only. ADMIN, DEBUG, QBFT, account unlocking and signing are not exposed. nginx-rpc.conf.example contains locations for an existing TLS virtual host. Apply suitable rate limits for your service. Your node is independently operated; listing its RPC on Cookscan is a separate review of availability and chain identity.

## Updates

Peers propagate blocks and transactions, not software or configuration updates. This release pins Besu 26.9.0 by Docker image digest. It includes the tested local HTTP/WebSocket lifecycle correction, described in patch/README.md; this is not an official Besu release.

Download reviewed releases manually and verify checksums. Back up configuration and preserve data/key. Do not delete or reset the database. For a software-only update, use the reviewed compose/patch from the release and recreate your node. For a consensus/fork update, all operators must install the matching network configuration before the announced activation block. No automatic pull of latest images is installed. Validators must be upgraded one at a time and checked for resumed participation before another validator is restarted.

Do not blindly replace a genesis file or run this installer again on an existing installation. New releases must provide specific migration instructions.

## Release status

This distribution repackages the existing reviewed node configuration and local Besu patch. It does not change consensus. Public bootstrap admission and a fresh end-to-end synchronization test have not yet been confirmed for this release. Treat the release as a prerelease until these checks are completed.

## Public network endpoint

Public HTTPS JSON-RPC: https://rpc.cookscan.net/evm
Explorer: https://cookscan.net/
Chain ID: 20261001 (0x1352889). Native asset: COOK, 18 decimals.

```sh
curl https://rpc.cookscan.net/evm -H 'Content-Type: application/json' --data '{"jsonrpc":"2.0","id":1,"method":"eth_chainId","params":[]}'
```

Only public configuration, installation tools and patch references are distributed. Node identities are generated locally. The package contains no validator keys, wallets or production databases.

## Validator candidates

A separate controlled-admission validator package and operator guide are available in [validators/](validators/README.md). Installing it does not grant validator status. Download the validator ZIP and checksum from the [release page](https://github.com/cookarmyofficial-alt/cookchain-rpc-node/releases/tag/validator-v2026.10.09.1). Apply through the validator application issue template after technical preflight.
