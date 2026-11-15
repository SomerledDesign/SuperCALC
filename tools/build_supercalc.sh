#!/bin/sh
# SuperCalc.OG custom PicoCalc firmware build (POSIX sh).
#
# Produces ONE UF2 for the PicoCalc with a Pico 2 W (RP2350), board RPI_PICO2_W:
#   - MicroPython v1.25.0-preview (f187c77da), the same base as the stock LofiFren
#     picocalc_micropython_pico2w.uf2 (newer MicroPython has a USB-CDC regression on RP2350)
#   - LofiFren PicoCalc C drivers: picocalcdisplay, vtterminal, picosampler
#     (picocalc.py / boot.py stay on the device filesystem under /modules, as today),
#     built from a script-managed copy with firmware/patches/lofifren-*.patch applied
#     (timer/core1/DMA soft-reset safety). The LofiFren checkout itself is never edited.
#   - picocalc_math (src/math)            -> mp/lib/hybrid.py reports HAS_C_MATH True
#   - eigenmath (zenodante/eigenmath_micropython, plus firmware/patches/*.patch)
#   - Python floats: 64-bit double by default (Kevin's choice, 2026-11-13), via the
#     MP_CONFIGFILE overlay in firmware/config/ (the MicroPython tree is not edited).
#     SUPERCALC_FLOAT=single gives the stock rp2 32-bit floats instead.
#
# Usage:
#   tools/build_supercalc.sh            fetch sources if missing, build, copy UF2 to build/
#   tools/build_supercalc.sh --check    only check tools and source refs, do not build
#
# Environment (all optional):
#   SUPERCALC_FW_WORK    where third-party sources are cloned (default: ~/.cache/supercalc-fw)
#   MICROPYTHON_DIR      existing micropython checkout (default: $SUPERCALC_FW_WORK/micropython)
#   EIGENMATH_DIR        existing eigenmath_micropython checkout (default: $SUPERCALC_FW_WORK/eigenmath_micropython)
#   PICOCALC_DRIVER_DIR  LofiFren-PicoCalc/MicroPython (default: ../LofiFren-PicoCalc/MicroPython next to this project);
#                        read only, the patched copy is built instead
#   PICOCALC_DRIVER_BUILD_DIR  use your own already-patched driver dir as-is (never modified by
#                        this script); default: script-managed $SUPERCALC_FW_WORK/lofifren-supercalc/MicroPython
#   JOBS                 parallel make jobs (default 4)
#   SUPERCALC_FLOAT      double (default) or single
#
# Output: build/supercalc-og-pico2w-YYYYMMDD[TAG]-double.uf2 (or -single.uf2); never
#   overwrites an existing UF2 unless SUPERCALC_OVERWRITE=1. SUPERCALC_TAG adds a suffix (e.g. f).
# Frozen: firmware/frozen/manifest.py (stock board manifest + sc_splash startup splash;
#   regenerate the image asset with tools/make_splash.py SPLASH.png).
#
# Needs on PATH: git, make, cmake, python3, a host C/C++ compiler (cc, c++), and
# arm-none-eabi-gcc with newlib (Arm GNU Toolchain). macOS: brew install cmake and
# brew install --cask gcc-arm-embedded. The LofiFren Dockerfile in
# LofiFren-PicoCalc/MicroPython/firmware/ also provides all of these.
#
# This script never flashes anything. Flash the UF2 yourself with BOOTSEL.

set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

BOARD=RPI_PICO2_W
MPY_URL=https://github.com/micropython/micropython.git
MPY_REF=f187c77da8b0ff51927b62cd1f4efd78c03bdb7f
EIGEN_URL=https://github.com/zenodante/eigenmath_micropython.git
EIGEN_REF=ea94bc5a9565f0565e04218061237096f6e0ca54
LOFI_REF_TESTED=c711a366febe21061dbfff69a616cb22e0364ccd
# RPI_PICO2_W: 4 MB flash, MICROPY_HW_FLASH_STORAGE_BYTES = 4 MB - 1.5 MB,
# so the firmware image must stay under 1.5 MB or it would overlap the filesystem.
FW_MAX_BYTES=1572864

WORK=${SUPERCALC_FW_WORK:-${XDG_CACHE_HOME:-$HOME/.cache}/supercalc-fw}
MPY=${MICROPYTHON_DIR:-$WORK/micropython}
EIGEN=${EIGENMATH_DIR:-$WORK/eigenmath_micropython}
LOFI=${PICOCALC_DRIVER_DIR:-$PROJECT_ROOT/../LofiFren-PicoCalc/MicroPython}
DRV=${PICOCALC_DRIVER_BUILD_DIR:-$WORK/lofifren-supercalc/MicroPython}
DRV_MARK=$DRV/.supercalc-managed
JOBS=${JOBS:-4}
FLOAT=${SUPERCALC_FLOAT:-double}
CONFIG_DIR=$PROJECT_ROOT/firmware/config
PATCH_DIR=$PROJECT_ROOT/firmware/patches
USERMODS=$PROJECT_ROOT/firmware/supercalc_usermods.cmake
# Frozen Python: stock board manifest + sc_splash (startup splash, asset from tools/make_splash.py)
FROZEN=$PROJECT_ROOT/firmware/frozen/manifest.py
# Output name tag, e.g. SUPERCALC_TAG=f -> supercalc-og-pico2w-YYYYMMDDf-double.uf2
TAG=${SUPERCALC_TAG:-}

say() { echo "[SuperCalc.OG] $*"; }
die() { echo "[SuperCalc.OG] ERROR: $*" >&2; exit 1; }

CHECK_ONLY=0
case "${1:-}" in
    --check) CHECK_ONLY=1 ;;
    "") ;;
    *) die "unknown option: $1 (use --check or nothing)" ;;
esac

case "$FLOAT" in
    double|single) ;;
    *) die "SUPERCALC_FLOAT must be double or single (got: $FLOAT)" ;;
esac
case "$CONFIG_DIR" in
    *" "*) die "project path contains a space; CFLAGS_EXTRA cannot carry it: $CONFIG_DIR" ;;
esac

# --- tools ---
for t in git make cmake python3 cc c++ arm-none-eabi-gcc patch cksum; do
    command -v "$t" >/dev/null 2>&1 || die "missing tool on PATH: $t"
done

# --- sources ---
[ -f "$LOFI/micropython.cmake" ] || die "PicoCalc driver dir not found: $LOFI (set PICOCALC_DRIVER_DIR)"
LOFI_HEAD=$(git -C "$LOFI" rev-parse HEAD 2>/dev/null || echo unknown)
if [ "$LOFI_HEAD" != "$LOFI_REF_TESTED" ]; then
    say "NOTE: LofiFren-PicoCalc is at $LOFI_HEAD; this build was verified with $LOFI_REF_TESTED"
fi

fetch() { # dir url ref
    if [ ! -d "$1/.git" ]; then
        [ "$CHECK_ONLY" = 1 ] && die "$1 missing (run without --check to fetch it)"
        say "cloning $2 -> $1"
        mkdir -p "$(dirname -- "$1")"
        git clone -q "$2" "$1"
        git -C "$1" checkout -q "$3"
    fi
    head=$(git -C "$1" rev-parse HEAD)
    [ "$head" = "$3" ] || die "$1 is at $head, expected $3 (check out $3 or point the env var elsewhere)"
}
fetch "$MPY" "$MPY_URL" "$MPY_REF"
fetch "$EIGEN" "$EIGEN_URL" "$EIGEN_REF"

# eigenmath safety patches (idempotent)
for p in "$PATCH_DIR"/eigenmath_micropython-*.patch; do
    [ -f "$p" ] || continue
    if git -C "$EIGEN" apply --reverse --check "$p" >/dev/null 2>&1; then
        say "patch already applied: $(basename -- "$p")"
    elif [ "$CHECK_ONLY" = 1 ]; then
        say "patch NOT applied yet: $(basename -- "$p")"
    elif git -C "$EIGEN" apply --check "$p" >/dev/null 2>&1; then
        git -C "$EIGEN" apply "$p"
        say "applied patch: $(basename -- "$p")"
    elif [ -z "${EIGENMATH_DIR:-}" ]; then
        # Our own managed checkout carries an older version of the patch: reset and re-apply.
        say "updating patch in managed checkout: $(basename -- "$p")"
        git -C "$EIGEN" checkout -q -- .
        git -C "$EIGEN" apply "$p" || die "could not apply $p"
    else
        die "$EIGEN has other local changes; reset it to $EIGEN_REF, then rerun to apply $p"
    fi
done

# LofiFren driver safety patches: applied to a build copy, never to $LOFI itself.
lofi_patches() { for p in "$PATCH_DIR"/lofifren-*.patch; do [ -f "$p" ] && echo "$p"; done; return 0; }
lofi_stamp() { # cksum of the pristine driver sources + our patches
    cat "$LOFI/micropython.cmake" "$LOFI"/picocalcdisplay/* "$LOFI"/vtterminal/* "$LOFI"/picosampler/* \
        $(lofi_patches) 2>/dev/null | cksum
}
if [ -n "${PICOCALC_DRIVER_BUILD_DIR:-}" ]; then
    # User-supplied: use as-is, only verify the patches are already in it.
    [ -f "$DRV/micropython.cmake" ] || die "PICOCALC_DRIVER_BUILD_DIR has no micropython.cmake: $DRV"
    for p in $(lofi_patches); do
        patch -p1 -s -R --dry-run -f -d "$DRV" < "$p" >/dev/null 2>&1 \
            || die "$DRV does not contain $(basename -- "$p"); apply it there or unset PICOCALC_DRIVER_BUILD_DIR"
    done
    say "using your patched driver dir as-is: $DRV"
else
    for p in $(lofi_patches); do
        patch -p1 -s --dry-run -f -d "$LOFI" < "$p" >/dev/null 2>&1 \
            || die "$(basename -- "$p") does not apply to $LOFI (LofiFren at $LOFI_HEAD, tested $LOFI_REF_TESTED)"
    done
    STAMP=$(lofi_stamp)
    if [ -f "$DRV_MARK" ] && [ "$(cat "$DRV_MARK")" = "$STAMP" ]; then
        say "patched driver copy up to date: $DRV"
    elif [ "$CHECK_ONLY" = 1 ]; then
        say "patched driver copy will be (re)created: $DRV"
    else
        if [ -e "$DRV" ]; then
            # Only ever delete a directory this script created (it carries our marker file).
            [ -f "$DRV_MARK" ] || die "$DRV exists but was not created by this script; move it away or set PICOCALC_DRIVER_BUILD_DIR"
            rm -rf "$DRV"
        fi
        mkdir -p "$DRV"
        cp -R "$LOFI/micropython.cmake" "$LOFI/picocalcdisplay" "$LOFI/vtterminal" "$LOFI/picosampler" "$DRV/"
        for p in $(lofi_patches); do
            patch -p1 -s -f -d "$DRV" < "$p" || die "could not apply $p to $DRV"
            say "applied driver patch to build copy: $(basename -- "$p")"
        done
        echo "$STAMP" > "$DRV_MARK"
    fi
fi

if [ "$CHECK_ONLY" = 1 ]; then
    say "check OK: board $BOARD, floats $FLOAT, micropython $MPY_REF, eigenmath $EIGEN_REF, drivers $LOFI_HEAD (build copy $DRV)"
    exit 0
fi

# --- submodules + mpy-cross (only what rp2 / RPI_PICO2_W needs) ---
if [ ! -f "$MPY/lib/pico-sdk/src/rp2_common/pico_cyw43_driver/CMakeLists.txt" ]; then
    say "fetching MicroPython submodules (one time)"
    git -C "$MPY" submodule update --init --depth 1 lib/pico-sdk lib/tinyusb lib/mbedtls \
        lib/micropython-lib lib/cyw43-driver lib/lwip lib/btstack
    git -C "$MPY/lib/pico-sdk" submodule update --init --depth 1
fi
make -C "$MPY/mpy-cross" -j"$JOBS" >/dev/null

# --- build ---
# Separate build dir per float mode: CFLAGS_EXTRA is only read when cmake configures.
BUILD_NAME=build-supercalc-$BOARD-$FLOAT
if [ "$FLOAT" = double ]; then
    FLOAT_CFLAGS="-I$CONFIG_DIR -include supercalc_float_double.h"
else
    FLOAT_CFLAGS="-I$CONFIG_DIR -include supercalc_float_single.h"
fi
# The driver dir is baked in when cmake configures: reconfigure if it changed.
OUT_DIR=$MPY/ports/rp2/$BUILD_NAME
CFG_KEY="$DRV|$FROZEN"
if [ -d "$OUT_DIR" ] && [ "$(cat "$OUT_DIR/.supercalc-drivers" 2>/dev/null)" != "$CFG_KEY" ]; then
    say "driver dir or frozen manifest changed; reconfiguring $BUILD_NAME"
    rm -rf "$OUT_DIR"
fi
say "building $BOARD with $FLOAT-precision floats (a few minutes the first time)"
(
    cd "$MPY/ports/rp2"
    CFLAGS_EXTRA="$FLOAT_CFLAGS" PICOCALC_DRIVER_DIR="$DRV" EIGENMATH_DIR="$EIGEN" \
        make BOARD="$BOARD" BUILD="$BUILD_NAME" USER_C_MODULES="$USERMODS" FROZEN_MANIFEST="$FROZEN" -j"$JOBS"
)
echo "$CFG_KEY" > "$OUT_DIR/.supercalc-drivers"
[ -f "$OUT_DIR/firmware.uf2" ] || die "build finished but $OUT_DIR/firmware.uf2 is missing"

BIN_BYTES=$(wc -c < "$OUT_DIR/firmware.bin" | tr -d ' ')
[ "$BIN_BYTES" -lt "$FW_MAX_BYTES" ] || die "firmware.bin is $BIN_BYTES bytes, over the $FW_MAX_BYTES-byte code region"

# --- sanity: the modules must be in the image ---
for m in picocalc_math eigenmath EigenMath picocalcdisplay vtterminal picosampler rpn_eval stats_stdev sc_splash sc_splash_data; do
    LC_ALL=C grep -a -q "$m" "$OUT_DIR/firmware.bin" || die "module string '$m' not found in firmware.bin"
done
# --- sanity: the patched drivers and the soft-reset hook are in the image ---
if [ -n "$(lofi_patches)" ]; then
    LC_ALL=C grep -a -q "vtterminal buffer must be" "$OUT_DIR/firmware.bin" \
        || die "patched LofiFren drivers not in firmware.bin (delete $OUT_DIR and rebuild)"
fi
grep -q "supercalc_float_$FLOAT.h" "$OUT_DIR/CMakeFiles/firmware.dir/flags.make" \
    || die "config overlay supercalc_float_$FLOAT.h missing from compile flags (delete $OUT_DIR and rebuild)"

# --- sanity: the float mode really took effect ---
if [ "$FLOAT" = double ]; then
    grep -q "supercalc_float_double.h" "$OUT_DIR/CMakeFiles/firmware.dir/flags.make" \
        || die "double-float overlay missing from compile flags (delete $OUT_DIR and rebuild)"
else
    if grep -q "supercalc_float_double.h" "$OUT_DIR/CMakeFiles/firmware.dir/flags.make"; then
        die "single build dir has the double overlay (delete $OUT_DIR and rebuild)"
    fi
fi

mkdir -p "$PROJECT_ROOT/build"
DEST=$PROJECT_ROOT/build/supercalc-og-pico2w-$(date +%Y%m%d)$TAG-$FLOAT.uf2
if [ -e "$DEST" ] && [ "${SUPERCALC_OVERWRITE:-0}" != 1 ]; then
    die "$DEST already exists; set SUPERCALC_TAG (e.g. f) or SUPERCALC_OVERWRITE=1"
fi
cp -f "$OUT_DIR/firmware.uf2" "$DEST"
UF2_BYTES=$(wc -c < "$DEST" | tr -d ' ')
say "UF2: $DEST ($UF2_BYTES bytes)"
say "floats: $FLOAT precision"
say "firmware.bin: $BIN_BYTES of $FW_MAX_BYTES bytes in the code region; filesystem region unchanged"
say "Flash with BOOTSEL (hold BOOTSEL, plug USB, copy the .uf2 to the RP2350 drive). Not flashed by this script."

# legacy marker kept for older notes/tests
touch "$PROJECT_ROOT/build/supercalc-hybrid-proof.stamp"
