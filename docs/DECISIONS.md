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

### Phase 1 QA Minors Addressed at Phase 2 Start
**Decision**: In Phase 2 inc1: (a) added explicit guard in hybrid.py pow() fallback so negative**non-int returns NaN (float('nan')) matching the C path behavior instead of raising ValueError; (b) to_rpn now cleanly handles leading unary '+' (treated as no-op, prev_was flag respected) and documents the prior gap; (c) RPN_STACK_MAX=32 recorded as explicit tracked limit (will revisit for nested calls / subroutines in full VM); (d) abs exported from C globals; versions bumped; log10 + inverse trig added as Phase 2 early surface.

**Rationale**: Auditor report (Phase 1 fix2) listed these as "Should address in the next increment (before Phase 2 start)". Doing them in inc1 of Phase 2 satisfies the recommendation while keeping Phase 1 scope locked. The pow guard makes the hybrid fallback a faithful test proxy for the C path even on host. Unary + support improves parser robustness for graphing/programs later without changing precedence model.

**Date**: 2026-06 Phase 2 inc1

### RPN_STACK_MAX=32 Tracked Limit
**Decision**: The C rpn_eval (and MPy mirror) hard limit of 32 stack slots (RPN_STACK_MAX) is intentional for Phase 1 expressions but is now explicitly tracked in DECISIONS as a limit to revisit when Phase 2 adds programmable subroutines, loops, and nested calls. No change to value in inc1; documented for future VM work (src/core VM will likely increase or make dynamic with PSRAM consideration).

**Rationale**: Auditor recommendation. Makes the constraint visible and prevents surprise when users write larger programs. 32 is generous for straight-line exprs and small programs; full RPL programs with deep nesting will drive the next sizing decision (and possibly a separate call/return stack).

**Date**: 2026-06 Phase 2 inc1

---

## 2026-06 (Phase 2 inc1 — Programmable Language Skeleton start)

### Program Model for inc1 (RPN bodies + first-class via env)
**Decision**: Programs are Python objects (mp.lang.prog.Program) holding a .body (RPN token list) + optional name/source. They are stored/recalled exactly like numbers via the Phase1 env (sto/rcl). Execution is driven by expr._execute_rpn_body (shared stack + env mutation) for authentic RPL "inline" feel in inc1. Literal Program instances in rpn token lists are *pushed as data values* (first-class); execution uses explicit "run"/"eval"/"xeq" (EVAL_ALIASES) or bare name resolution (which auto-execs for word-call ergonomics). store/run helpers provided; tests exercise all paths.

**Rationale**: Keeps implementation small and verifiable for inc1 while proving first-class + sto/rcl + run. Reuses all Phase1 machinery (no duplication). Shared-stack body exec (added in expr refactor) enables side-effect progs and caller stack results without fresh stack per call. Eager auto-exec only on name-resolve keeps literal prog tokens usable for data (sto the prog itself). C will accelerate later.

**Alternatives considered**: Full eager auto-exec on any embedded Program tok (rejected: broke [prog, "sto", name] data use and made "run" op unreachable in tests). Separate call stack from day 1 (deferred: too much for small slice; shared is fine and matches m-3 notes on why eval_rpn stays MPy for side effects).

**Date**: 2026-06 Phase 2 inc1

### C VM Skeleton + Hybrid Glue
**Decision**: Introduced src/core/picocalc_vm.c (minimal: version + exec stub raising NotImplemented with clear guidance) + matching micropython.cmake. hybrid.py exposes HAS_VM / vm_version / vm_exec (C path if built; py fallback that delegates to prog/expr for host continuity). The module follows the exact picocalc_math pattern for USER_C_MODULES builds.

**Rationale**: Establishes the thin boundary and future hot path location (per ARCHITECTURE: C for VM inner dispatch). Host tests and prog execution work immediately via fallback (PGR "host harness first"). No bytecode or control yet.

**Date**: 2026-06 Phase 2 inc1

### Top-level eval contract + side-effect programs
**Decision**: eval_rpn requires a final non-empty stack (original Phase1); called program *bodies* may end empty (side-effect only, e.g. pure sto progs). Tests that invoke void progs at top level leave a dummy value or use rcl-after to satisfy the check.

**Rationale**: Preserves Phase1 error semantics for direct calculations while allowing useful RPL-style side-effect programs. Minor test adjustments only (no API change).

**Date**: 2026-06 Phase 2 inc1

### Graphing Data-First Approach (Phase 3 inc1)
**Decision**: For inc1, deliver a pure data sampling API (`mp.plot.cartesian_sample`) that produces lists of (x, y) points by repeatedly evaluating user expressions / RPN bodies / Programs via the existing Phase1/2 expr + hybrid layers (setting 'x' each step). The C `picocalc_plot` module is introduced only as a registered skeleton (version + NotImpl stub) to establish the future hot-path location. Pixel rasterization, framebuffer writes, UI viewport chrome, and interactive trace live in inc2+.

**Rationale**:
- Matches "small verifiable slice" + PGR rules: host tests runnable immediately, C skeleton proves build path without over-scope.
- Reuses expr RPN (parse once, eval N times) which is already correct, side-effect capable (RPL spirit), and exercises hybrid/C math.
- 320x320 default n=320 gives natural 1:1 sample-to-column mapping for later render without resampling artifacts in first cut.
- Avoids fighting display driver or allocating large pixel buffers in inc1 (PSRAM/LUT strategy from prior Decision already recorded).
- Keeps MPy in control of "which expr/program to graph" while C will later own the inner loop (x-gen + batch eval + draw).

**Date**: 2026-06 Phase 3 inc1

### Thin Plot Boundary + Future C Sampling
**Decision**: hybrid.py exposes only HAS_PLOT + plot_version (like VM). The useful sampling lives in mp/plot/ (importable, documented). When real C picocalc_plot lands, it will provide e.g. a C function taking x-buffer + RPN-tokens (or precompiled form) and returning y-buffer; MPy side (or future C raster) will consume it. No change to cartesian_sample call shape for callers.

**Rationale**: Preserves the proven thin-boundary contract from Phase 0-2. Allows perf work on sampling (the "plotting loop" hot path called out in ARCHITECTURE) without rewriting the user-facing or test surface.

**Date**: 2026-06 Phase 3 inc1

### Phase 2 QA Minors Closed at Phase 3 Start
**Decision**: The four "should address before Phase 3 gate" items (M-1 broad except in vm_exec, M-2 fragile `in "+-*/^"`, N-1 dead isinstance str, N-2 Program ctor test) plus M-3 LOOP_STATE reconciliation were implemented as hygiene in Phase 3 inc1 rather than a phase-2-fix. State advanced to 3 + history note added; PHASES updated.

**Rationale**: Auditor explicitly listed them as "Can be addressed before the Phase 3 gate (not blocking inc2)". Doing them here keeps Phase 2 inc1 scope locked while satisfying the "address every issue" rule before hardware and further incs. Explicit test for the ctor documents the flexible behavior instead of removing it.

**Date**: 2026-06 Phase 3 inc1

### Phase 3 inc1: linspace grid helper exposed
**Decision**: Added `mp.plot.linspace(xmin, xmax, n=320)` (and used internally by cartesian_sample) as a small pure-Py data utility. Exported publicly. Test coverage added. No change to C skel or sampling contract.
**Rationale**: Makes the x-grid generation explicit and reusable for host verification, custom sampling, and future render layers (still inc2+). Keeps 320x320 default prominent and avoids duplicating spacing math. Fits "data only" slice; zero scope creep.
**Alternatives**: Keep private (rejected: small but useful for users writing their own plot scripts on device/host before full UI).
**Date**: 2026-06 Phase 3 inc1 (small addition)

### Phase 3 retry 2 (QA rejection): ralph.sh automation robustness fixes
**Decision**: Fixed multiple classes of bugs in tools/ralph.sh exposed by the failed handoff that produced only bash errors + "message got cut off" in claude_report.txt (permission denied on *.md, LOOP_STATE.json / PGR.md as "command not found", command substitution syntax errors on markdown ( , **, unbound vars, lost "Implementer Message", wrong handoff globs for phase, dirty detector missing unstaged mods, AUDITOR vars undefined in full loop, early dispatch calling helpers before they were defined in source, CLAUDEQA_FILE unbound in subcommand path, etc.). Changes: (a) hoist current_phase/phase_cleared + AUDITOR defaults + PGR/CLAUDEQA defaults to absolute top before any handle/early intercept; (b) robust early subcommand detection + shift so `./tools/ralph.sh complete-phase "real desc"` captures the msg (was always "complete-phase" or lost); (c) improved dirty grep to catch both "M  " staged and " M " unstaged + consistent filters; (d) best-effort git checkout of claude_report inside complete; (e) phase-aware + safer "read latest handoff" instructions in the lean auditor_prompt (prefer phase-N-*-review-request.md); (f) pre-read claudeqa + quoted handling to reduce expansion surprises; (g) use ${AUDITOR} with defaults. All complete-phase + status paths now run without the prior shell errors.
**Rationale**: The "auditor report" for this retry was the script's own failure modes (no real Claude review happened due to rate limit + bad prompt state). Per PGR "Fix every issue the auditor raised before writing new code. Address all blockers and majors first" and "the script is the single source of truth", tooling had to be repaired before re-handoff. Matches "Unattended handoff", "Git clean at handoff", and "complete-phase produces usable handoff + prompt". No change to Phase 3 inc1 deliverables (plot sampling + C skel + tests were already green and in-scope).
**Alternatives considered**: Ignore and force a manual handoff file (rejected: violates using the automation and PGR "never declare victory yourself"); rewrite large parts of ralph (overkill; targeted hoists + regex + prompt text were sufficient).
**Date**: 2026-06 Phase 3 fix2 / retry 2

### Phase 3 retry 3 (QA rejection): additional ralph.sh prompt + transient safety
**Decision**: Further hardened tools/ralph.sh after the fix2 changes (which addressed the bulk of the original bash/permission/command-not-found/syntax symptoms) still left latent risks exposed by the exact "auditor report" content in claude_report.txt for this retry 3/3:
- Used quoted heredoc + separate `cat "$CLAUDEQA_FILE"` for the COPY-PASTE PROMPT in complete-phase (instead of unquoted <<PROMPT with ${claudeqa_inline} interpolated). This guarantees the markdown content (with **, ( ), `, code examples) is emitted literally with zero shell re-expansion or word-splitting risk during script execution.
- In run_grok retry path: embed only head -c 1500 of prior claude_report (plus note to read full file + handoff from disk) instead of ${last_report} wholesale. Prevents prompt bloat / CLI truncation ("message got cut off — you just sent "to" and nothing else") and rate-limit thrash when large accumulated reports or prior handoffs are inlined.
- Added unconditional early `git checkout -- claude_report.txt || rm -f ...` right after cd (top level for all invocations including status/complete). Complements the one inside complete-phase.
- Updated the python status helper to filter claude_report.txt from "Git dirty files" count and list (mirrors complete-phase filter); status now reports clean or notes transient explicitly.
These changes were made *before* any Phase 3 functional code changes or re-handoff, per "Fix every issue the auditor raised before writing new code. Address all blockers and majors first."
**Rationale**: The provided claude_report.txt for retry 3 was the literal shell error spew + rate limit + truncated-prompt response from a prior bad invocation (not a structured ClaudeQA review). Since PGR and the loop treat the script as "the single source of truth for moving the unattended loop forward", the tooling itself had to be made immune to the failure modes it produced. Literal file cats + size limiting + proactive clean make future complete-phase / handoff / status runs (and the prompts they emit) robust even under rate limits or noisy prior reports. Matches "Git working tree is clean", "complete-phase produces usable handoff + prompt", and "Unattended handoff".
**Alternatives considered**: (a) Force a manual handoff file without using complete-phase (rejected: violates PGR "never declare victory yourself" and "use the automation"); (b) strip all markdown from inlines or rewrite handoff as json (overkill; the safe cat + limit keeps the self-contained copy-paste experience that ClaudeQA and PGR expect); (c) ignore and proceed to "new code" on plot (rejected: instruction explicitly says address auditor issues first, before writing new code).
**Date**: 2026-06 Phase 3 fix3 / retry 3

### Phase 3 inc1: ascii_plot host text renderer for sampled data
**Decision**: Added `mp.plot.ascii_plot(points, width=64, height=16, title="")` (and exported) as a tiny pure-Py renderer that turns cartesian_sample output into a framed ascii art plot ( * marks, auto scale, NaN skip, footer ranges, title). Used in 4 new host tests; callable from REPL/scripts on device or host for immediate visual confirmation of curves (sin, x^2 via Program body, etc). Downsamples 320 samples to narrow terminal width. No pixels, no C, no device framebuffer or ui/ modules touched.

**Rationale**: Delivers on "small, verifiable slice" + "host tests first" + "data (usable for later render or host print)" from PHASES inc1 success criteria. Gives the implementer/auditor a concrete way to see that sampling + Program integration + error-nan paths produce correct shapes on the development machine *before* any UF2 or hardware pixels (which remain human step). Fits 320x320 awareness (default n noted). Thin, zero-dependency, RPL-spirit (graphing first-class programs works in the ascii path). Zero scope creep: still no raster, no polar, no interactive, C skel untouched.

**Alternatives considered**:
- Rely only on numeric assert in tests (rejected: harder to spot visual shape bugs like inverted axis or bad scaling at a glance).
- Put ascii in tests/ only (rejected: useful as public data utility for users experimenting on device REPL before inc2 UI; small enough to ship in the slice).
- Full curses/colored (rejected: overkill for inc1; breaks "simple" + offline + works in basic terminal).

**Date**: 2026-06 Phase 3 inc1 (this attempt)

### Phase 3 inc1: side-effect sto during Program sampling (RPL stateful fns)
**Decision**: Added `test_program_body_side_effects_during_sample` exercising a Program body that does "x sto last_x" + returns 2*x ; cartesian_sample over range leaves final state (env["last_x"] == xmax) visible to caller. 15+ host tests now.
**Rationale**: Directly verifies the documented "env mutated ... sto/rcl side effects if expr has them" and "first-class" Program bodies as plottable fns (RPL spirit for graphing programs that maintain/observe state). Small verifiable extension of existing sampling + prog integration; no API or scope change. Fits "host tests first" and keeps data-only slice pure.
**Date**: 2026-06 Phase 3 inc1 (attempt 1)
