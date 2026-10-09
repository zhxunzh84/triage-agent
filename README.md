# triage-agent

![CI](https://github.com/zhxunzh84/triage-agent/actions/workflows/ci.yml/badge.svg)

An LLM-assisted incident triage agent for a simulated banking platform,
built with the controls a regulated bank expects: audit logging,
human approval, and automatic fallback.

## Status

Sprint 1 of 4 — in progress. No LLM code yet; this sprint builds the
foundations (data model, rules baseline, audit trail).

## Quickstart

Prerequisites: [uv](https://docs.astral.sh/uv/) and `make`.
uv will install Python 3.12 automatically if it is missing.

```bash
git clone https://github.com/zhxunzh84/triage-agent.git
cd triage-agent
uv sync
make lint && make test
```

## Disclaimer

Synthetic data only. Designed with reference to the MAS Guidelines on
AI Risk Management (October 2026); this is a portfolio project, not a
compliance claim.
