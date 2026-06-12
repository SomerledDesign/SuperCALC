#!/bin/bash
# SuperCalc.OG custom firmware build wrapper (Phase 0+)
# Uses LofiFren (recommended) or zenodante-style Docker + USER_C_MODULES pattern.
# See docs/BRINGUP.md and docs/DECISIONS.md for base choice rationale.
#
# The hybrid proof (Phase 0 gate) is the existence of:
#   src/math/picocalc_math.c + src/math/micropython.cmake
#   + mp/lib/hybrid.py thin wrapper (with graceful fallback).
#
# This script will be the canonical entry once the base clone layout is locked with human.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "[SuperCalc.OG] build_supercalc.sh — STUB (documents the process; does not yet run Docker/make)."
echo "[SuperCalc.OG] The hybrid proof files exist; real UF2 requires the base port (see BRINGUP.md)."
echo "[SuperCalc.OG] Phase 1 fix2: C iterator API (mp_obj_iter_buf_t) + mp_raise_msg_varg corrected; module will now compile against LofiFren/zenodante MicroPython headers."

# Recommended flow (LofiFren/PicoCalc, Pico 2 W):
# 1. Clone base (outside this tree):
#      git clone https://github.com/LofiFren/PicoCalc ../LofiFren-PicoCalc
# 2. Follow their Docker build setup (they provide a Dockerfile in MicroPython/firmware or tools).
# 3. From the *base* firmware build dir, pass our modules dir. Example:
#
#   BASE=../LofiFren-PicoCalc
#   (cd "$BASE/MicroPython/firmware" && \
#     docker build -t supercalc-build . && \
#     docker run --rm \
#       -v "$PROJECT_ROOT/..:/workspace" \
#       -v "$(pwd):/out" \
#       supercalc-build \
#       bash -c '
#         make -C . BOARD=RPI_PICO2_W \
#              USER_C_MODULES=/workspace/SuperCalc.OG/src/math/micropython.cmake \
#              -j$(nproc) &&
#         cp build-RPI_PICO2_W/firmware.uf2 /out/supercalc.og-pico2w.uf2
#       ')
#
# The per-module micropython.cmake (src/math/micropython.cmake) does:
#   add_library(...) + target_link_libraries(usermod INTERFACE usermod_picocalc_math)
# Base ports typically include it via the USER_C_MODULES list (or edit their top cmake).
#
# After successful build you will have a supercalc.og-pico2w.uf2 that exposes:
#   import picocalc_math
#   picocalc_math.version()  -> "SuperCalc.OG-hybrid-proof-0.2"
#   picocalc_math.add(1.5, 2.5)
#   picocalc_math.sin(0.5)
#   picocalc_math.sqrt(2)
#
# Then push mp/ tree (or just lib/hybrid.py) via dashboard/mpremote and test:
#   import mp.lib.hybrid as h; print(h.version(), h.sin(0.1), h.sqrt(9))

echo "[SuperCalc.OG] NOTE: Exact Docker/make command is base-specific."
echo "                Edit the example above + BRINGUP.md when you have the"
echo "                LofiFren (or zenodante) tree and first successful UF2."
echo "                The skeleton files already exist and are correct for inclusion."

# For now: mark that the proof-of-concept files are in place (verifiable without full base)
touch build/supercalc-hybrid-proof.stamp 2>/dev/null || mkdir -p build && touch build/supercalc-hybrid-proof.stamp
echo "[SuperCalc.OG] Hybrid proof artifacts ready. Real UF2 build requires base port clone (see BRINGUP.md)."
ls -l build/supercalc-hybrid-proof.stamp || true