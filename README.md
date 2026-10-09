# triage-agent

![CI](https://github.com/zhxunzh84/triage-agent/actions/workflows/ci.yml/badge.svg)

An LLM-assisted incident triage agent for a simulated banking platform,
built with the controls a regulated bank expects: audit logging,
human approval, and automatic fallback.

## Status

Sprint 1 of 4 — in progress. No LLM code yet; this sprint builds the
foundations (data model, rules baseline, audit trail).

## Quickstart

Prerequisites: [uv](https://docs.astral.sh/uv/), `make`, and
[Docker Desktop](https://www.docker.com/products/docker-desktop/).

```bash
git clone https://github.com/zhxunzh84/triage-agent.git
cd triage-agent
uv sync
cp .env.example .env        # then set your own POSTGRES_PASSWORD
make up                     # Postgres 16 on localhost:5433, waits until healthy
make lint && make test
```

| Command | What it does |
| --- | --- |
| `make up` / `make down` | Start / stop the local database (data is kept) |
| `make psql` | Open a psql shell in the database container |
| `make reset-db` | Delete all local DB data and start fresh (asks to confirm) |

## Disclaimer

Synthetic data only. Designed with reference to the MAS Guidelines on
AI Risk Management (October 2026); this is a portfolio project, not a
compliance claim.
