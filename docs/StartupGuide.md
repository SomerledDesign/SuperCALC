# SuperCalc.OG Startup Guide — Fresh PicoCalc + Pico 2 W (RP2350)

**Goal**: Get a brand-new (or freshly reset) ClockworkPi PicoCalc with Raspberry Pi **Pico 2 W** running the full SuperCalc.OG calculator environment with the smallest number of steps.

This guide covers:
- Downloading the correct base firmware and tools.
- Preparing the SD card (the "SD card img" part — manual preparation is simplest and most reliable).
- Flashing via drag-and-drop UF2 (BOOTSEL method — true drag & drop, no special tools required for basic flash).
- Adding the SuperCalc.OG software.
- Two paths: Quick dev setup (push files) vs. ideal self-contained custom UF2 (everything baked in for true "one file, drag and drop" experience).
- Running the calculator.

**Primary recommendation (as of 2026)**: Start with the **LofiFren/PicoCalc** MicroPython port. It has excellent Pico 2 W support, a great web dashboard for development, and is actively maintained for this hardware.

**Alternative** (especially if you want strong built-in eigenmath/CAS): Bases derived from **zenodante/PicoCalc-micropython-driver**.

All core SuperCalc features (hybrid C math, RPN + infix, programs, solver, stats, REPL, CAS surface) work on top of these bases.

---

## 1. Prerequisites & Hardware

- ClockworkPi PicoCalc kit (v2.0 board recommended), **fully assembled with Raspberry Pi Pico 2 W** installed in the headers (install the Pico 2 W *before* closing the case if not already done).
- 1–2 good 18650 batteries (protected recommended; follow ClockworkPi guidelines: Ø18 ±0.5 mm, 65–69 mm length).
- USB-C cable (data + power).
- microSD card (the one that came with the kit is fine; 4–32 GB recommended). You will reformat/prep it.
- A computer (Linux/macOS/Windows) with Python 3 and a web browser.
- (Optional but strongly recommended for development) Git.

**Safety note**: Power off the device completely before flashing or handling the SD card. Always safely eject before unplugging.

---

## 2. Download the Right Repos & Files

### Main Repos You Need

1. **LofiFren/PicoCalc** (base firmware + tools + dashboard — **primary**)
   - `git clone https://github.com/LofiFren/PicoCalc`
   - Key files you will use:
     - `MicroPython/firmware/picocalc_micropython_pico2w.uf2` (the drag-and-drop firmware)
     - `MicroPython/tools/dashboard.py` (the fantastic dev web UI)
     - `MicroPython/sd/py_scripts/` (files to copy to your SD card)

2. **This SuperCalc.OG repo** (the calculator itself)
   - `git clone https://github.com/kmurphy/GROK/iWasCodeing/PicoCalc/SuperCalc.OG` (or however you have it)
   - Contains:
     - `mp/` — All the Python code (ui/calc_repl, lang/, lib/ with hybrid/cas/solver, etc.)
     - `src/` — C modules (picocalc_math, picocalc_vm, picocalc_plot) for speed
     - `tools/build_supercalc.sh` — Helper for custom firmware builds
     - Tests, docs, examples

3. **(Strongly recommended alternative base / for better eigenmath)**  
   zenodante/PicoCalc-micropython-driver (the foundation many ports, including LofiFren, build on). Some community builds include eigenmath out of the box, which makes Phase 7+ CAS features use real symbolic math instead of the host stub.

---

## 3. Prepare the SD Card ("SD Card Image")

The SD card is used for:
- Additional scripts/apps (auto-discovered in many ports).
- User programs, data, saved plots, etc. (SuperCalc can use `/sd` for storage in the future).
- In some workflows, holding extra UF2s for the UF2 loader.

### Recommended Preparation (LofiFren style)

1. **Backup** anything on the SD card first (the kit SD is often preloaded with samples).

2. **Format** the card as **FAT32** (use your OS formatter; 4–32 GB is ideal; use a 32 GB or smaller card if you have issues).
   - On macOS: Disk Utility → Erase → MS-DOS (FAT) → Master Boot Record.
   - On Windows: Right-click → Format → FAT32.
   - On Linux: `mkfs.fat -F 32 /dev/sdX1` (be very careful with the device name!).

3. Create these folders at the **root** of the SD card:
   - `py_scripts/` (required for LofiFren base scripts and many user scripts)

4. Copy base support files (from the cloned LofiFren repo):
   ```
   MicroPython/sd/py_scripts/*     →   SD:/py_scripts/
   ```
   (Copy the `.py` files that provide examples, helpers, Tetris, etc.)

5. (Optional but nice) Create additional folders for future use:
   - `apps/` or `picoware/` (if using community app ecosystems)
   - `supercalc/` (for your own programs/data)

6. Safely eject the SD card and insert it into the PicoCalc.

**Alternative "SD image" approach**: Once you have one perfectly prepared card, you can create a disk image of it (`dd if=/dev/sdX of=picocalc-sd.img bs=1M` on Linux/macOS) and later restore it to other cards. Most people just re-copy the small set of files.

**Note on UF2 Loader** (pelrun/uf2loader — popular in the community): If you want to flash firmware/apps *from the SD card itself* (no constant USB tether), also copy the appropriate `BOOT2350.uf2` + create `pico2-apps/` folders and place UF2s there. This is advanced but excellent for a finished device.

---

## 4. Flash the Base Firmware (True Drag-and-Drop)

Use the **LofiFren prebuilt UF2** first — this gets the display, keyboard, REPL, SD mounting, and dashboard working immediately.

1. Power the PicoCalc **completely off** (remove batteries or use the power switch if present; unplug USB).

2. **Hold the BOOTSEL button** on the Pico 2 W module.

3. While still holding BOOTSEL, plug in the USB-C cable to your computer.

4. A new drive named **`RP2350`** (or similar) should appear on your desktop.

5. **Drag and drop** the file:
   ```
   <LofiFren clone>/MicroPython/firmware/picocalc_micropython_pico2w.uf2
   ```
   onto that drive.

6. The device will automatically detect the UF2, program itself, and reboot.

7. You should see a splash/menu (LofiFren gives a nice arrow-key navigable menu with REPL access and apps).

8. Insert your prepared SD card if it isn't already.

**Verify it is working**:
- Use the on-device menu/REPL.
- From a computer: Use the Dashboard (next step) or `mpremote` to connect and run `import sys; print(sys.implementation)`.

**Gotcha**: Make sure you are using a **Pico 2 W** compatible UF2 (RPI_PICO2_W board variant). The LofiFren `picocalc_micropython_pico2w.uf2` is the one you want.

---

## 5. Developer Tools — The LofiFren Dashboard (Highly Recommended)

After the base is flashed:

```bash
cd /path/to/your/LofiFren-PicoCalc-clone
python3 MicroPython/tools/dashboard.py
```

- Opens a local web UI in your browser.
- Push individual files or whole directories from host → device (internal flash or SD).
- Side-by-side diffs.
- Built-in REPL.
- Browse device + SD card.
- Safe eject button.

This is by far the fastest way to iterate while developing SuperCalc.

Alternative CLI tools:
- `pip install mpremote` → `mpremote`
- Thonny (with care for the right interpreter).

---

## 6. Add SuperCalc.OG (Quick / Dev Path)

With the base running and Dashboard (or mpremote) connected:

1. Clone this SuperCalc.OG repo if you haven't already.

2. Push the Python layer (`mp/`) to the device. Typical deployment (adjust paths per your dashboard):
   - The `mp/` tree can be pushed so you can do:
     ```python
     from mp.ui.calc_repl import CalcREPL, run_demo
     run_demo()
     ```
   - Or push into `/modules/` or a `supercalc/` folder depending on the base's module search path.

3. (During active development) Also push any examples or your own test scripts to `py_scripts/` on the SD card.

4. Test in the REPL (via Dashboard REPL or serial):
   ```python
   from mp.ui.calc_repl import run_demo
   run_demo()
   ```

   You should see the full demo exercising infix/RPN, programs, solver, stats, plot (ASCII on terminal), and CAS (stub on host-style bases; real eigenmath on ports that include it).

For a more "app-like" experience, look at `mp/apps/solver_app.py` and the CalcREPL dot commands (`.s`, `.plot`, `.solve`, `.cas`, `.demo`, etc.).

---

## 7. The Ideal End State: One Custom "SuperCalc" UF2 (True Drag-and-Drop Everything)

For the finished product you want a **single UF2** that contains:
- The LofiFren (or zenodante) base drivers (display, keyboard, SD, terminal).
- Our custom C modules (`picocalc_math`, `picocalc_vm`, `picocalc_plot`) compiled in via `USER_C_MODULES`.
- Our Python code (`mp/`) **frozen** into the firmware (so no need to push files every time; `import mp.ui.calc_repl` works immediately).

### How to Build It (Current Practical Recipe)

See also the comments inside `tools/build_supercalc.sh` and the "Building Firmware from Source" section in the LofiFren README.

High-level steps (you will do this **outside** this SuperCalc.OG tree):

1. Clone the LofiFren base (if not already):
   ```bash
   git clone https://github.com/LofiFren/PicoCalc ../LofiFren-PicoCalc
   ```

2. Follow their Docker setup (one-time):
   - They provide a `Dockerfile` in `MicroPython/firmware/` or tools.
   - Build the Docker image.

3. Build with our modules integrated. A typical command (adapt from `build_supercalc.sh` and LofiFren docs):

   ```bash
   # From inside the base's firmware build directory, something like:
   docker run --rm \
     -v "$(pwd)/../../SuperCalc.OG:/workspace/SuperCalc.OG" \
     -v "$(pwd):/out" \
     your-lfifren-build-image \
     bash -c '
       make -C . BOARD=RPI_PICO2_W \
            USER_C_MODULES=/workspace/SuperCalc.OG/src/math/micropython.cmake \
            -j$(nproc) &&
       cp build-RPI_PICO2_W/firmware.uf2 /out/supercalc.og-pico2w.uf2
     '
   ```

   You will also want to configure freezing of the `mp/` tree (via `FROZEN_MANIFEST` or the equivalent in the base build system) so the SuperCalc Python is baked in.

4. The resulting `supercalc.og-pico2w.uf2` is your magic file.

5. On a fresh (or reset) Pico 2 W:
   - BOOTSEL + drag the custom UF2 onto the `RP2350` drive.
   - Insert your prepared SD card.
   - Boot → everything (C accel + full Python REPL/apps/CAS) should be present without further file transfers.

**Current status of our tooling**: `tools/build_supercalc.sh` is a well-documented stub that prints the exact pattern. Once you have successfully built your first custom UF2, we can turn the script into a real one-liner wrapper.

For eigenmath/CAS: Choose or configure a base build that includes eigenmath (some zenodante-derived images do). The `mp/lib/cas.py` layer will auto-detect it.

---

## 8. Running SuperCalc.OG

Once the software is on the device (via push or custom UF2):

```python
from mp.ui.calc_repl import CalcREPL, run_demo
run_demo()                    # Full tour of capabilities

r = CalcREPL()
r.enter("2 + 3 * sin(pi/2)")  # Infix algebraic (fast C path)
r.enter(".s")                 # Show stack
r.enter("1 2 3 4 sum")        # RPN + lists + stats
r.enter(".cas solve x^2-2 x") # CAS (stub or real eigenmath)
```

Dot commands (type them in the REPL):
- `.s` / `.stack` — show stack
- `.v` / `.vars` — show variables
- `.plot <expr>` — quick ASCII plot
- `.solve <f> <lo> <hi>` — numeric root finder
- `.cas <verb> <args...>` — symbolic (simplify / solve / diff)
- `.prog ...` — quick program storage helper
- `.demo` — run the tour
- `.help` — current help text

Programs are first-class: define them, store with `sto`, `rcl`, and `run`.

---

## 9. Troubleshooting & Common Gotchas

- **No RP2350 drive appears**: Hold BOOTSEL *firmly* the entire time you plug in. Try a different USB port/cable. Power cycle completely.
- **SD card not mounting**: Re-format as FAT32. Ensure it is seated. Some ports have a short stabilization delay on cold boot.
- **"Bad UF2" or wrong board**: Use the `pico2w` specific file from LofiFren (not a generic RPI_PICO2_W.uf2).
- **Display/keyboard not working**: You must use a PicoCalc-*specific* UF2, not a stock MicroPython one.
- **CAS shows only stubs**: Your base firmware does not include eigenmath (or it is under a different module name). This is expected on many stock LofiFren builds; real symbolic math appears when the right base is used.
- **Custom build fails**: You need the full base source tree + Docker. The C modules require the public MicroPython headers from the base (our code follows the documented iterator API).
- **Memory pressure**: With lots of plots or large programs, watch `gc.mem_free()`. The design uses C for hot paths and keeps the MPy layer thin.

---

## 10. Next Steps & References

- Once hardware is alive and SuperCalc runs: Record a hardware verification with the project tools if you are following the Ralph Loop (`./tools/ralph.sh record-hardware-verification "..."`).
- For a polished "appliance" feel, a future increment can integrate SuperCalc deeper into the base menu/dashboard.
- Full technical details: See `docs/BRINGUP.md`, `docs/PHASES.md`, `README.md`, and the handoff artifacts in `handoffs/`.
- Community: ClockworkPi forums, the LofiFren and zenodante repos.

**You now have a working scientific/programmable calculator on charming PicoCalc hardware.**

Enjoy, and feel free to open issues or contribute improvements back to the project!

---

*Last updated for the Phase 7+ state of SuperCalc.OG. The exact file paths in the LofiFren tree may evolve — always check the README in the cloned base repo for the latest.*