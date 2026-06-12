# SuperCalc.OG — Architecture (Hybrid C + MicroPython)

**Target**: PicoCalc (ClockworkPi v2.0) + Raspberry Pi Pico 2 W (RP2350)  
**North Star**: Best of classic HP programmables + modern capability, on delightful portable hardware, offline-first.

## Guiding Principles

1. **Hybrid for real reasons**
   - C: Speed, numerical accuracy, tight control of hot loops (plot sampling, VM execution, matrix ops, rendering primitives).
   - MicroPython: Rapid UI, flexible higher-level logic, on-device editing, easy user extension, excellent existing driver ecosystem.
2. **HP Spirit without slavish copy**
   - Stack-oriented thinking, powerful user-defined functions/programs, first-class objects where it adds power, excellent catalog of primitives.
   - Support both classic RPN/RPL entry *and* friendly algebraic entry.
3. **Leverage the community base heavily**
   - Do not rewrite display, keyboard, SD, or terminal from scratch.
   - Extend via `USER_C_MODULES` in the proven zenodante/LofiFren-style builds.
4. **Offline first, PSRAM-aware**
   - Everything core must work without WiFi. Use the 8 MB PSRAM for buffers (graphs, large programs, CAS state).
5. **Phased & Reviewable**
   - Each phase delivers a runnable, testable slice on real hardware.

## Layered Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User (Keyboard + Screen)                │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│  MicroPython Layer (mp/)                                    │
│  • mp/ui/          : Menus, expression editor, graph view,  │
│                      trace controls, program catalog        │
│  • mp/lang/        : Infix/RPN parsers, program loader,     │
│                      high-level language runtime glue       │
│  • mp/apps/        : Solver UI, stats, units converter,     │
│                      constants browser, etc.                │
│  • mp/lib/         : Reusable pure-Python helpers           │
│                                                             │
│  Talks to C via:                                            │
│    - Direct C extension functions (math_eval, plot_sample,  │
│      vm_run_program, etc.)                                  │
│    - ulab / eigenmath when useful                           │
└─────────────────────────────────────────────────────────────┘
                              │ (thin, fast boundary)
┌─────────────────────────────────────────────────────────────┐
│  C Core Layer (src/)                                        │
│  • src/math/       : Numeric kernel (real, complex, matrix) │
│                      Accuracy-focused primitives            │
│                      Solver building blocks                 │
│                      Thin symbolic dispatch (to eigenmath   │
│                      or our own lightweight CAS)            │
│  • src/plot/       : Sampling engine, axis/grid logic,      │
│                      fast line/point rasterization into     │
│                      the existing framebuffer               │
│  • src/core/       :                                        │
│      - Bytecode VM or direct interpreter for the HP-style   │
│        custom language (the heart of programmability)       │
│      - Expression internal forms (shared RPN/AST)           │
│      - Stack machine (HP-48 spirit)                         │
│      - Glue to display/keyboard/SD (minimal — prefer the    │
│        existing picocalcdisplay / keyboard abstractions)    │
│      - Power / backlight helpers if useful                  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│  Base Firmware (frozen / user C modules)                    │
│  • picocalcdisplay (C)  — 320x320 framebuffer, LUT, core1   │
│                           refresh, fast modes               │
│  • vtterminal + keyboard I2C driver                         │
│  • SD card (FAT), PWM audio                                 │
│  • ulab, eigenmath (highly desirable for Phase 1+)          │
│  • Our new modules: picocalc_math, picocalc_plot,           │
│    picocalc_vm (or similar names)                           │
└─────────────────────────────────────────────────────────────┘
                              │
                    Hardware (RP2350 + 8MB PSRAM + SPI display + I2C kb)
```

## Data Flow Examples

**Simple calculation (infix)**:
1. MPy UI collects string `"sin(2*pi) + sqrt(3)"`
2. Parser (MPy or thin C call) → internal RPN or AST
3. `math_eval(internal)` → C kernel returns double/complex result
4. MPy formats and displays (nice printing, history)

**RPN / stack mode**:
1. User enters numbers and operators directly on stack (MPy maintains visible stack)
2. Operators call thin C primitives for speed/accuracy
3. LastX, stack lift, etc. handled in MPy or C stack module

**Graphing**:
1. MPy maintains list of expressions + view parameters (Xmin etc.)
2. Calls C `plot_sample(expr_id, x_values, y_out)` or equivalent (C does the heavy sampling + function evaluation)
3. C (or MPy calling C drawing) renders into framebuffer using existing fast paths
4. MPy handles interaction (trace cursor, zoom gestures via keys)

**User Program**:
1. User writes text in HP-style language (or keystroke mode later)
2. MPy does light syntax checking / tokenizing
3. Compiler (MPy or C) emits compact bytecode
4. `vm_execute(bytecode)` runs in C VM (fast, deterministic, good stack control)
5. Program can call built-in math/plot functions and user subroutines
6. Results / side effects (drawing on screen) visible immediately

## Custom Language (HP-Style) — Initial Design Sketch

**Spirit**: RPL (HP-48) more than pure keystroke (HP-41), but we can offer both flavors later.

**Characteristics we want**:
- Stack-based core (unlimited or deep stack + registers)
- Named programs and functions (`<< ... >>` or `<< ... >> 'NAME' STO` style)
- Local variables (`-> x y << ... >>`)
- Conditionals (`IF ... THEN ... ELSE ... END`)
- Loops (`START`, `FOR`, `DO ... UNTIL`, `WHILE ... REPEAT`)
- First-class programs (can be stored in variables, passed around)
- Strong set of primitives for stack manipulation (`DUP`, `SWAP`, `ROT`, `DROP`, `OVER`, etc.)
- Easy access to the math/plot library

**Implementation**:
- Text source stored as plain text on SD (editable on-device).
- Lightweight compiler in C (or MPy that emits simple bytecode) for fast execution.
- Bytecode interpreter / VM in C (`src/core/vm.c` or similar).
- This gives "custom language" feel while delivering the speed users expect from classic programmables.

We will iterate the exact syntax in Phase 2 with real examples.

## Memory & Performance Strategy

- Framebuffer: Use the existing reduced-bit + LUT modes for UI speed; switch to higher fidelity only when needed.
- Graphing: Sample in C, render in C where possible. Keep only the current view window data in RAM.
- Programs: Bytecode is compact. Source lives on SD.
- Large CAS state or big matrices: PSRAM via existing mechanisms (many ports already expose it).
- Avoid fighting the base port's core1 display refresh — coordinate if we do heavy WiFi later (but offline first).

## Hardware Interfaces We Touch (minimally)

- Display & backlight: Through the existing `picocalc.display` abstraction + any new fast drawing we add in C.
- Keyboard (I2C via STM32): Existing driver. We may add custom keymaps or direct access for calculator modes.
- SD: Existing driver. Primary persistence for programs, data, user constants.
- Audio: Optional nice-to-have for beeps / program feedback (LofiFren port already has synth work).
- GPIO expansion: Future (sensors, etc.) — not Phase 1–3.

## Build & Deployment

- Firmware: Custom MicroPython build for `RPI_PICO2_W` that includes our new C modules (following the Docker pattern in LofiFren/zenodante repos).
- Filesystem / SD: Boot files + our `mp/` tree + user `programs/` folder.
- Dev workflow (strongly recommended):
  - LofiFren dashboard for rapid push/diff/REPL during development.
  - mpremote or Thonny for direct work.
  - On-device editor for final user experience validation.

## Extension Points for Future

- Deeper CAS (more eigenmath surface or custom simplifier/deriver)
- Keystroke programming mode (HP-41 style)
- 3D / implicit / DE visualization
- Optional network features (export plots to desktop, fetch updated constants, act as remote calculator)
- External modules via exposed headers

## Open Decisions (to be resolved in phases)

- Exact numeric precision model (plain double vs. decimal or compensated techniques for key algorithms)
- How much of the parser lives in C vs MPy (start MPy for speed of iteration)
- Bytecode format for the language VM (keep it simple and documented)
- Color / visual style for graphs (leverage existing LUTs or extend)
- Default stack depth and register model

These will be locked with rationale in a `DECISIONS.md` as we go.

---

This architecture is intended to be **living** — updated at the end of each phase with what we actually learned.
