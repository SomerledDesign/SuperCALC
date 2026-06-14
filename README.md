# SuperCalc.OG — Definitive Scientific / Graphing / Programmable Calculator for PicoCalc

**Target Platform**: ClockworkPi PicoCalc (v2.0 board) with Raspberry Pi **Pico 2 W** (RP2350)

**Project Root**: `~/GROK/iWasCodeing/PicoCalc/SuperCalc.OG/`

**Status**: Phase 7 inc2 — CAS dispatch fix + Symbolic wrapper + help note for solve RPN convention + diff/solve RPN test cov + nits closed (per prior auditor). Full tests+demo green on host. Ralph Loop (phase 7 per set; LOOP_STATE may lag until complete). HW backlog (0-7) pending real PicoCalc + UF2. See docs/PHASES.md + handoffs/.

## Vision

A "full on" scientific, graphing, and programmable calculator that captures the best of the classic HP programmable machines (HP-41, HP-48/49/50 RPL lineage) while delivering modern capability on the charming PicoCalc hardware.

- **Hybrid architecture**: C for speed + numerical accuracy + core execution; MicroPython for flexibility, UI, and user extensibility.
- **Multiple entry modes**: Algebraic (infix with precedence) + full RPN/RPL-style.
- **Deep math**: High-quality numeric, matrices, complex numbers, statistics, solvers, units, constants — plus symbolic/CAS hooks.
- **Graphing**: Fast, usable 2D (Cartesian, polar, parametric, etc.), multiple plots, interactive exploration.
- **True programmability**: HP-style custom language / RPL-inspired environment. User-defined functions, programs, local variables, control structures, stack manipulation, first-class programs. Stored on SD, loadable, editable on-device.
- **Offline-first**: Everything works without network. WiFi/BT are optional future enhancements.
- **Hardware fit**: Leverages the beautiful 320×320 IPS, 67-key backlit QWERTY, 8 MB PSRAM, SD storage, dual speakers, and long battery life.

This is a **Ralph Loop** endeavour: rigorous, iterative, high-quality development with clear phases, self-review, and independent QA handoff (Claude + review tools).

## Inspirations

- Classic HP programmables: HP-41C (keystroke + extensions), HP-48/49/50 series (full RPL — Reverse Polish Lisp — with extraordinary programmability, object model, and library power).
- Modern graphing calculators (TI-89/92, Casio, NumWorks) for UI/UX lessons.
- The PicoCalc community ports (especially zenodante and LofiFren) that already provide excellent optimized display, keyboard, terminal, and even ulab + eigenmath builds.

## High-Level Architecture (Hybrid)

```
User Input (Keyboard / REPL)
          │
          ▼
MPy Layer (mp/)
  • Expression entry (infix ↔ RPN)
  • UI / menus / history / graph viewport
  • Program editor & SD manager
  • High-level orchestration
          │ (calls / passes data)
          ▼
C Core (src/)
  • Math kernel (numeric, matrices, complex, solvers — high accuracy)
  • Symbolic interface (eigenmath or lightweight CAS)
  • Plotting engine (sampling + fast rendering primitives)
  • Language VM / bytecode executor (HP-style programs)
  • Low-level hardware extensions (if needed beyond base drivers)
          │
          ▼
Base Firmware Drivers (frozen C modules)
  • picocalcdisplay (framebuffer + LUT + core1 refresh)
  • vtterminal / keyboard (I2C)
  • SD, audio PWM, etc.
```

**Key extension points**:
- New custom C modules (compiled into a PicoCalc-specific MicroPython build for Pico 2 W).
- Python-accessible C functions for hot paths.
- SD-based storage for user programs, custom functions, constants, saved plots/data.

## Current Project Structure

```
SuperCalc.OG/
├── README.md
├── docs/                 # Design, phases, references, HP notes
├── src/                  # C heavy lifting
│   ├── core/             # Glue, VM, system interfaces
│   ├── math/             # Numeric + symbolic kernel
│   └── plot/             # Graphing primitives & renderers
├── mp/                   # MicroPython layer
│   ├── ui/               # Screens, input, graphing UI, menus
│   ├── lang/             # Parser, compiler, runtime for custom HP-style language
│   ├── apps/             # Built-in apps (solver, stats, constants, etc.)
│   └── lib/              # Reusable MPy modules
├── firmware/             # Notes + build artifacts for custom UF2
├── tools/                # Flash helpers, dashboard integration, build scripts
├── build/                # Build outputs
├── examples/             # Example programs (user + demo)
├── tests/                # Unit + integration tests (host + on-device)
├── assets/               # Fonts, icons, reference images
└── .gitignore
```

## Base Platform Recommendation (to be confirmed in Phase 0)

Start from the excellent community work:

- **LofiFren/PicoCalc** (Pico 2 W focused, great dashboard + apps + MCP)
- **zenodante/PicoCalc-micropython-driver** (core C display/keyboard drivers + ulab/eigenmath builds)

We will:
1. Use (or fork) one of these as the base firmware.
2. Add new `USER_C_MODULES` for the calculator core (math, plot, lang VM).
3. Keep the existing high-quality display/keyboard abstractions.
4. Extend the MPy environment with our `mp/` tree.

This gives us immediate working display, keyboard, SD, REPL, editor, and even symbolic math to build upon instead of starting from zero.

## Phased Development (Ralph Loop)

See `docs/PHASES.md` for the detailed plan.

Rough sequence:
- **Phase 0**: Scaffolding, architecture lock-in, base firmware selection + build environment.
- **Phase 1**: Core hybrid math engine + expression system (infix + RPN) + evaluator.
- **Phase 2**: REPL + stack + variables + HP-style programmable language skeleton (custom language + VM).
- **Phase 3**: Graphing engine (2D first, multiple functions, interaction).
- **Phase 4+**: Solvers, units, stats, richer CAS integration, on-device programming polish, full apps, performance tuning, packaging.

At each meaningful increment we do internal review then hand off to Claude for independent QA.

## Getting Started (for the team)

1. Hardware: PicoCalc kit assembled with Pico 2 W installed.
2. Base firmware: Follow LofiFren or zenodante flashing instructions (UF2 via BOOTSEL).
3. Dev tools: Thonny or mpremote + the excellent dashboard from LofiFren for file sync/REPL.
4. C extensions: Docker-based build like the existing ports (or native Pico SDK).

Detailed bring-up will be documented in `docs/` as we go.

## Ralph Loop Principles (for this project)

- Small, verifiable increments.
- Heavy lifting by Grok; independent QA by Claude (using review/check-work skills when appropriate).
- Clear documentation and design artifacts updated with each phase.
- On-device testing on real hardware is mandatory.
- "Best of all worlds" — respect speed (C), accuracy (good numerics + CAS), usability (HP spirit + modern affordances), and the delightful PicoCalc hardware.

## Contributing / Process Note

This is a focused, high-standard personal + collaborative build. All major changes go through the loop.

---

**Buona fortuna e buon lavoro!** Let's make something definitive.

Next: Phase 0 work (base firmware confirmation + detailed architecture). See docs/.
