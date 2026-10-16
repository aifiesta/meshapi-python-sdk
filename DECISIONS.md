# Decisions

## contract-check baseline

The SDK trails the committed spec snapshot (`contract/openapi.public.json`, refreshed by the release orchestrator; CI never fetches a spec) by 504 surface members (whole resources and many fields). `contract-baseline.json` records that gap verbatim, so the contract-check job is green today and goes red only on new drift. The baseline is a backlog, not an exemption: shrink it as the SDK gains members, never grow it to silence a new spec change.
