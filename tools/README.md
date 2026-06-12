# Tools for SuperCalc.OG Development

This directory contains scripts and helpers for building, flashing, syncing, and testing.

## Current / Planned

- `dashboard.py` — We will integrate with (or extend) the excellent LofiFren dashboard rather than reinvent.
- `build_graphingcalc.sh` — Wrapper that clones or mounts the base port and adds our `src/` USER_C_MODULES for a custom UF2 build.
- `test_harness.py` (planned) — Host-side Python that mirrors the on-device hybrid math/plot/vm APIs so we can develop and unit-test large parts of the logic without constant flashing.
- `tests/test_hybrid.py` (Phase 0) — Concrete runnable host harness for the hybrid boundary proof (exercises fallback; documents C path).
- `program_uploader.py` — Helper to package user programs + examples onto SD images or push them cleanly.
- `accuracy_bench.py` — Compare our C math results against high-precision references (mpmath on host, etc.).

## Usage (once implemented)

See `docs/BRINGUP.md` for the immediate flashing and dashboard steps using the base port.

For custom firmware builds we will document the exact Docker or native commands here and in the main docs.

## For Ralph Loop

Any new tool should come with a tiny test or usage example so Claude (or future reviewers) can verify it quickly.
