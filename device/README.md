# device/

Board-side scripts copied to the PicoCalc filesystem (not frozen into the UF2).

| Repo path | Device path | Purpose |
|---|---|---|
| `main.py` | `/main.py` | Boot menu; shows a random amber PicoCalc splash (`pc_splash`) at power-up |
| `py_scripts/supercalc.py` | `/py_scripts/supercalc.py` | SuperCalc launcher; shows the SuperCALC splash (`sc_splash`) |
| `py_scripts/hp12c.py` | `/py_scripts/hp12c.py` | SuperCalc 12C launcher; shows the SuperCALC splash |
| `py_scripts/sheets.py` | `/py_scripts/sheets.mpy` (compiled) | 12C financial worksheets (TVM, savings, mortgage, loan payoff, NPV/IRR, percent/APR, date math, Black-Scholes). TVM uses total years as the default horizon; N stays in periods; the doubling-time line is shown; extra FV/growth lines hide when hold is 0. |

The splash modules (`pc_splash`, `sc_splash`) are frozen into firmware `20261115h` or later.
Each call is wrapped in `try/except`, so older firmware just skips the splash.

## Compiling `.mpy` files

This tree keeps the MicroPython source only. The board runs compiled `.mpy` for `sheets`. Do not copy the `.py` next to the `.mpy` on the device: MicroPython prefers `foo.py` over `foo.mpy` in the same directory.

Build with `mpy-cross` from the SuperCALC firmware tree (MicroPython v1.25.0-preview.389, mpy v6.3):

    mpy-cross sheets.py -o sheets.mpy

`-march=armv6m` is accepted on both RP2040 and the Pico 2 W (RP2350).

## Worksheet keys

- **F5** clears the current sheet to the same state it has when first opened. This works on all eight sheets, and on the mortgage amortization table (F5 returns to the form and clears it).
- **Del** / backspace still clear only the current field.
- On the PicoCalc keyboard, Shift+DEL sends End (jump to the last field), so it is not used as a clear.

## Related files not in this directory

These are on the PicoCalc, and the sibling `device-root/` working copy is kept in sync, but they are not tracked here: adding them would need new folders under `device/` (`modules/`, `sd/py_scripts/`).

- `/modules/py_run.py` — menu runner, including a `sys.print_exception` plus sleep patch so a failing script (for example Tetris) cannot freeze the menu.
- `/sd/py_scripts/screensaver.py` — same screensaver as `/py_scripts/screensaver.py`, with `# picocalc-hide` as the first line so the menu lists it only once. The flash copy stays visible.
- `/py_scripts/tetris.py` is already on the device and is not tracked in this repo.
