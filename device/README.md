# device/

Board-side scripts copied to the PicoCalc filesystem (not frozen into the UF2).

| Repo path | Device path | Purpose |
|---|---|---|
| `main.py` | `/main.py` | Boot menu; shows a random amber PicoCalc splash (`pc_splash`) at power-up |
| `py_scripts/supercalc.py` | `/py_scripts/supercalc.py` | SuperCalc launcher; shows the SuperCALC splash (`sc_splash`) |
| `py_scripts/hp12c.py` | `/py_scripts/hp12c.py` | SuperCalc 12C launcher; shows the SuperCALC splash |

The splash modules (`pc_splash`, `sc_splash`) are frozen into firmware `20261115h` or later.
Each call is wrapped in `try/except`, so older firmware just skips the splash.

`hp12c.py` and parts of `supercalc.py` import `sheets`, which is maintained separately and is not in this repo yet.
