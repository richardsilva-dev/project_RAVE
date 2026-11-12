# Benchmark laboratory architecture

## Separation

The SOLO baseline is an independent Python package under `comparison_a` (currently staged at `src/solo_baseline`). It does not import the RAVE package and does not instantiate additional agents.

Open Deep Research remains an upstream project in a separate Python environment. It is not reimplemented or rewritten.

The RAVE runtime remains in its own repository and branch. The lab reads exported run JSON through an adapter; it must not change RAVE behavior during an experiment.

## Data flow

Research request contract -> selected system runner -> native raw output + telemetry -> system-specific adapter -> normalized result contract -> later evaluation environment.

The evaluator is deliberately not implemented in this preparation phase.

## Experimental separation

Comparison A is intended to control the individual-vs-collective question. Comparison B is a reference-system comparison and cannot isolate architecture alone. Model, search tool, prompt, token/runtime budget, versions and configuration differences must be recorded for every run.
