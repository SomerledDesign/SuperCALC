# Bring-Up Guide — Getting a Working Base on Your PicoCalc + Pico 2 W

This document will be updated as we go. Goal: get you from "I have the assembled kit" to "I can flash, push files, and run hybrid code" with minimal pain.

## Hardware You Need

- ClockworkPi PicoCalc (v2.0 board) fully assembled with the Raspberry Pi **Pico 2 W** installed in the headers (instead of the stock Pico 1 H).
- At least one good 18650 battery (protected or unprotected — follow the PicoCalc battery guidelines: Ø18 ±0.5 mm, 65-69 mm length). Two is better for runtime.
- USB-C cable for flashing and development.
- microSD card (the kit one is fine; format FAT32 if you reformat).

**Important**: Install the Pico module **before** fully assembling into the case if you haven't already (per the official assembly videos).

## Recommended Base Firmware (Phase 0)

We are starting from the **LofiFren/PicoCalc** port because it is explicitly built for the **Pico 2 W** and has outstanding developer tools.

Repo: https://github.com/LofiFren/PicoCalc

Key assets:
- Prebuilt UF2: `MicroPython/firmware/picocalc_micropython_pico2w.uf2` (v1.25.0-preview is the stable recommendation in their docs).
- Excellent **dashboard** for USB file sync, diff, REPL, etc.
- On-device menu, editor, examples.

Alternative strong foundation (many shared roots): zenodante/PicoCalc-micropython-driver (has explicit ulab + eigenmath builds).

## Step-by-Step Flashing

1. **Power off** the PicoCalc completely (remove USB, power switch if present).
2. Hold the **BOOTSEL** button on the Pico 2 W module.
3. While holding BOOTSEL, plug in the USB-C cable to your computer.
4. A drive named `RP2350` (or similar) should appear.
5. Copy the chosen `picocalc_micropython_pico2w.uf2` onto that drive.
6. The device should reboot automatically into the new firmware. You can now unplug or keep connected.

After first boot you should see a splash / menu. The LofiFren port gives a nice arrow-key navigable menu of apps + REPL access.

## Developer Workflow (Strongly Recommended)

### Option A — LofiFren Dashboard (best during active development)

From the repo root on your host machine:

```bash
cd /path/to/LofiFren-PicoCalc-clone
python3 MicroPython/tools/dashboard.py
```

This opens a local web UI that lets you:
- Deploy all files or individual ones
- See side-by-side diffs
- Run Python directly on the device (REPL)
- Browse device + SD files
- Safe eject

It is extremely fast for the "write → push → test on hardware → repeat" loop.

### Option B — mpremote or Thonny

- `mpremote` (recommended for scripting): `pip install mpremote`
- Thonny: Use the special `boot_thonny.py` variant if you want the REPL only on the host side (see LofiFren docs). For normal work the standard `boot.py` + dashboard is better.

### SD Card Preparation

- Format as FAT32 (4–32 GB is ideal).
- Create a `py_scripts` folder (or follow the exact layout in the base port you chose).
- The base ports auto-discover scripts in certain folders.

## Adding Our Custom C Modules (The Hybrid Part — Future Steps)

This is how we will inject the high-speed math, plotting, and language VM.

In the base port's build system (they use Docker + `micropython.cmake` + `USER_C_MODULES`):

1. Add our `src/core`, `src/math`, `src/plot` directories (or symlinks) into the build tree.
2. Create small `micropython.cmake` files that register the new modules (e.g. `picocalc_math`, `picocalc_plot`, `picocalc_vm`).
3. Rebuild the UF2 with the extra modules frozen in.
4. From MicroPython you will be able to `import picocalc_math` (or whatever names we choose) and call fast C functions.

**For Phase 0 / early Phase 1** we can often prototype many things in pure MicroPython first (using the existing ulab/eigenmath), then move hot paths into C once the interface is stable. This is classic Ralph Loop — validate the shape quickly, then optimize.

## Useful Commands & Checks (once base is running)

- Check firmware / board: In REPL `import sys; print(sys.implementation); print(sys.platform)`
- Memory: `import gc; gc.mem_free(); gc.mem_alloc()`
- Display access (in LofiFren/zenodante ports): usually `import picocalc; picocalc.display...` or similar — check the exact module in your chosen base.
- Keyboard is handled; you get normal input in the terminal/REPL.
- SD: usually mounted at `/sd`

**Numeric precision note (Phase 1+)**: Our C math (picocalc_math) and hybrid assume `MICROPY_FLOAT_IMPL_DOUBLE` (double precision) in the base MicroPython build for RP2350. The LofiFren Pico 2 W recommended UF2 uses this; if you roll a custom build, verify `mpconfigport.h` or build flags set it (otherwise single-precision will silently reduce accuracy for the hybrid math kernel). See DECISIONS.md "Numeric Baseline".

**C API hygiene (Phase 1 fix2)**: The rpn_eval implementation now uses the documented public iterator pattern (`mp_obj_iter_buf_t iter_buf; mp_obj_t iter = mp_obj_get_iter(..., &iter_buf); mp_iternext(iter)`) + `mp_raise_msg_varg`. This resolves the compile-time blocker against real MicroPython headers from the base ports. The module skeleton is ready for inclusion in a LofiFren/zenodante USER_C_MODULES build. Full UF2 + on-device verification remains a human-performed step (no base firmware tree in this workspace).

## Battery & Power Notes

- The STM32 on the board can report battery status in many custom firmwares (LofiFren port has examples).
- For long sessions, two 18650s are nice.
- The device is designed for very good runtime — treat it like a classic HP.

## Common Gotchas

- Make sure you flashed the **RPI_PICO2_W** board variant, not the plain RPI_PICO.
- Some MicroPython versions have USB regressions on RP2350 — the LofiFren port documents the known-good versions and patches.
- Display and WiFi sometimes share SPI resources in these ports; when we add WiFi features later we will pause display refresh (already documented in the base ports).
- Always safely eject or use the dashboard's eject button before unplugging if you're doing heavy file work.

## Next for SuperCalc.OG

Once the base is running and the dashboard works:

1. We will create a minimal "hello from C" custom module (even if it just returns a constant) so we prove the hybrid extension path.
2. Then we start Phase 1 math kernel work.

---

**User note**: You said you have the kit and are "ready for upload". When you're at a computer with the device, run through the flashing steps above using the LofiFren UF2 and try the dashboard. Let me know the result (any errors, what menu you see, etc.) and we can debug together or move straight to adding our first custom module.

If you prefer a different base port (e.g. one of the eigenmath-heavy zenodante builds), say the word and we'll pivot the bring-up notes.
