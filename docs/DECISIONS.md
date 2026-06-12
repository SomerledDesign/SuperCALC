# SuperCalc.OG — Decisions Log (Living Document)

Record significant architectural, technical, and scope decisions with rationale and date. This helps the Ralph Loop reviews.

## 2026-06 (Phase 0)

### Base Firmware Choice
**Decision**: Build on LofiFren/PicoCalc (Pico 2 W focused) + zenodante/PicoCalc-micropython-driver foundations.

**Rationale**:
- Explicit Pico 2 W support and prebuilt UF2s.
- Excellent developer experience (dashboard, MCP, on-device editor, file sync).
- Already includes high-quality C modules for display (picocalcdisplay), VT100 terminal, keyboard (I2C), SD.
- Proven ulab + eigenmath builds — perfect for symbolic/numeric calculator work.
- Community momentum and the official ClockworkPi repo even calls out graphing/scientific calculations as a natural extension.

**Alternative considered**: Pure official Pico SDK C application or PicoMite BASIC. Rejected for this project because hybrid MPy + C + existing excellent hardware abstractions give fastest path to a rich calculator while still allowing deep C optimization.

### Custom Language Direction
**Decision**: Create a custom RPL-inspired language (programs as first-class objects, excellent stack model, locals via `->` or equivalent, control structures) executed by a small dedicated C VM/bytecode interpreter. Support both text program entry and (later) keystroke recording mode.

**Rationale**:
- Matches user's explicit request for "functionality of the old HP programmables" and "custom language for the functions".
- RPL (HP-48 lineage) is the pinnacle of calculator programmability — we want that power and expressiveness.
- C VM gives the speed and deterministic behavior that makes programming feel good (classic HPs were responsive for their time).
- Still allows a friendly infix/algebraic entry mode on top for everyday use.

### Hybrid Boundary
**Decision**: Keep the boundary thin and explicit. MPy owns UI, parsers (initially), program source management, high-level orchestration. C owns math kernel, plotting sampling + rendering primitives, and the language VM/bytecode execution.

**Rationale**:
- Lets us iterate UI and language syntax quickly in Python.
- Puts performance-critical loops (function evaluation during plotting, VM inner loop, heavy numerics) where they belong.
- Plays nicely with the existing frozen C module pattern in the base ports.

### Graphing Color & Memory Strategy
**Decision**: Start with the existing LUT / reduced-bit modes from the base display driver (excellent for speed and RAM on 320x320). Extend the LUT or add higher-fidelity paths only where graphing quality justifies it. Leverage PSRAM for any large plot data.

**Rationale**:
- The community ports already solved the hard problem of making the SPI display feel good.
- Graphing is one of the most RAM- and CPU-intensive things we will do — we must be disciplined.
- 320x320 square is a gift for plots; we can deliver very usable graphs even in 16-color or 8-color + dither modes.

### Offline-First Policy
**Decision**: All core features (calculation, graphing, programming, storage) must work with zero network. WiFi/BT features (if any) are strictly optional and non-blocking for main use.

**Rationale**:
- Matches user requirement.
- Classic HP programmables were self-contained powerhouses — that independence is part of the charm and reliability.
- Keeps the device useful in the field, classroom, or anywhere without connectivity.

### Numeric Baseline
**Decision**: Double-precision floating point as the primary numeric type for Phase 1–2, with clear extension points for higher-accuracy techniques (compensated summation, decimal, etc.) and integer/fraction types later. Complex numbers supported from the start.

**Rationale**:
- Double is fast on RP2350 (has FPU), widely understood, and sufficient for the vast majority of scientific/graphing work.
- We can demonstrate clear accuracy wins by moving hot functions into well-implemented C.
- ulab + eigenmath already bring strong numeric and symbolic capabilities we can build on.

### Parser Location (Initial)
**Decision**: Infix and RPN parsers start in MicroPython for rapid iteration and easy experimentation with syntax. Hot evaluation path immediately calls into C. We can move parser pieces to C later if profiling shows it is a bottleneck.

**Rationale**:
- Syntax is likely to evolve during Phase 1–2. Python is far faster to change.
- The expensive work is evaluation + plotting loops — those go to C immediately.

### Phase 0 Hybrid Proof Implementation
**Decision**: The minimal proof uses a single `picocalc_math` C module (registered with MP_REGISTER_MODULE) exposing version/add/sin/sqrt using mp_obj_{get,new}_float + <math.h>. MPy side has mp/lib/hybrid.py with try/import + pure-math fallback. Host test harness in tests/test_hybrid.py. Empty architectural dirs populated with .gitkeep. ralph.sh extended for `status`/`help`. build_supercalc.sh made actionable.

**Rationale**:
- Directly satisfies the three remaining Phase 0 deliverables (firmware decision docs, hybrid proof, automation cleanliness).
- Demonstrates the exact thin-boundary pattern required by PGR and ARCHITECTURE (C for numeric hot paths, MPy for orchestration).
- Uses standard MicroPython C extension APIs that work with the LofiFren/zenodante USER_C_MODULES flow.
- Host tests are runnable immediately (fallback); real C path exercised after UF2 flash (human step).
- No future-phase features (no parsers, no VM, no plotting yet).

**Date**: 2026-06 (Phase 0 inc1)

## 2026-06 (Phase 0 QA fixes carried into Phase 1 inc1)

### Loop Automation Hygiene (ralph.sh)
**Decision**: Implemented `complete-phase` subcommand (git-clean gate, timestamped rich handoff in handoffs/, LOOP_STATE update to awaiting_qa, prints self-contained copy-paste claude prompt using ClaudeQA). Also removed bare `APPROVED` from phase_cleared() grep (false-positive risk), fixed string length in C using strlen().

**Rationale**:
- Directly addresses the three must-fix items (B-1 string, M-1 complete-phase missing, M-2 false-positive) from the Phase 0 auditor report.
- Makes the unattended loop match the documented PGR.md contract and Phase 0 success criteria.
- strlen() pattern prevents recurrence of length bugs as more C string returns are added in later phases.
- complete-phase lets implementer produce clean handoff artifact + state without always running the full Grok+Claude auto loop.

**Date**: 2026-06 (Phase 1 inc1)

### Minor Hygiene
- build_supercalc.sh front-matter now clearly labels itself a stub (was misleading "Building..." on first line).
- BRINGUP.md now documents the MICROPY_FLOAT_IMPL_DOUBLE assumption for the numeric baseline.

## 2026-06 Phase 1 inc1 — Core Math + Expression System (first slice)

### Expression System Split (C kernel + MPy parsers)
**Decision**: Infix parser + RPN driver with variable env (sto/rcl) implemented in pure MicroPython (mp/lang/expr.py). Numeric hot path (all math primitives + full rpn_eval stack machine with HP ops) in C (src/math/picocalc_math.c: rpn_eval + added cos/tan/exp/log/pow/fabs/sub/mul/div). hybrid.py provides the transparent boundary + py fallback.

**Rationale**:
- Matches the "Parser Location (Initial)" decision: parsers in MPy for fast iteration/syntax experiments during Phase 1.
- Puts the inner dispatch, stack ops during evaluation, and FPU math where they belong (C) for speed/accuracy/determinism on RP2350.
- rpn_eval in C is the first "expression system" C kernel; thin list-of-tokens API keeps boundary simple and auditable.
- Stack words (dup/drop/swap/over) + neg/chs give immediate RPL/HP spirit even before the full src/core VM.
- Variables/env side effects kept in MPy (sto/rcl mutate caller-provided dict) — keeps C pure-compute and simple; full locals will evolve with the language VM in later incs.
- Host tests exercise the fallback identically; same code paths on device will hit C.

**Alternatives considered**:
- Full RPN interp in MPy only: rejected for Phase 1 because it would not exercise/prove the C kernel path required by architecture and "C for hot paths".
- Moving shunting-yard to C too: rejected — syntax is still evolving; Python is far cheaper to change while we discover the language feel.

**Date**: 2026-06 Phase 1 inc1

### Numeric Surface for inc1
**Decision**: Added the practical scientific set (trig, log/exp, pow, fabs) + four basic arithmetic + rpn control words. No complex, no matrices, no stats yet.

**Rationale**: Small verifiable slice that is already useful for real calculations on the device, exercises the new rpn_eval C entry point, and gives the expression layer something non-trivial to drive. More (atan2, hypot, gamma, etc.) will come as needed by graphing or solver work.

**Date**: 2026-06 Phase 1 inc1

### Phase 1 inc1 QA Fixes (retry 2)
**Decision**: Addressed all Blockers/Majors from first inc1 auditor report before re-handoff:
- B-1: Corrected MicroPython C iterator usage in rpn_eval (mp_obj_iter_buf_t + mp_obj_get_iter return value + mp_iternext(iter)).
- M-1: Lowered "neg" precedence to 2.5 ( > * / + - , < ^ ) + right-assoc ^ via strict > in shunting push_op.
- M-2: Power now right-associative (2^2^3 == 256 not 64).
- Added regression tests; extended rpn_str aliases; documented eval_rpn vs eval_infix paths; recorded pow behavior.
Also fixed m-1 (raise msg), m-2 (alias dispatch), m-3 (doc), m-5 (tests).

**Rationale**: Must-fix items per ClaudeQA report for Phase 1 inc1 clearance. Host tests now cover the previously-untested cases that exposed the defects (-2^2, 2^2^3, alias forms). C API now matches public MPy headers (will compile in USER_C_MODULES build).

**Date**: 2026-06 Phase 1 inc1 fix2

### C pow() NaN for complex-result cases (e.g. pow(-1, 0.5))
**Decision**: picocalc_math_pow (and hybrid fallback) pass through NaN for cases like (-1)**0.5 without raising; contrast with sqrt(-1) which raises ValueError in both layers. Recorded as deliberate for Phase 1.

**Rationale**: Keeps C kernel simple and fast (no extra isnan/domain checks on every pow). Matches Python's math.pow behavior for negative**non-int. sqrt path has explicit guard for common real-domain use. Full complex support and consistent domain policy (or signed-zero/branch-cut handling) deferred to later numeric or CAS work. Acceptable for inc1 scope; users doing fractional powers on negatives will see NaN (or can use explicit logic).

**Date**: 2026-06 Phase 1 inc1 (post QA)

---

Add entries at the end of each phase or when a significant choice is locked. Include date, decision, rationale, and alternatives considered.
