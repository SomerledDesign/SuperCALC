# SuperCalc.OG — Phased Development Plan (Ralph Loop)

**Project**: Definitive scientific/graphing/programmable calculator for PicoCalc (Pico 2 W)  
**Style**: **Unattended Ralph Loop** — see `docs/PGR.md` (implementer rules) and `docs/ClaudeQA.md` (reviewer rules).  
**Automation**: `./tools/ralph.sh` (takes PGR.md and ClaudeQA.md on the command line; fully automates the Grok-implementer → commit → local Claude auditor loop)

**Critical Process Rule**: Never declare a phase complete yourself. Use the automation script to generate a handoff package and the ready-to-paste prompt for Claude. Commit cleanly. The loop is unattended once the handoff is produced.

## Overall Goals (from user requirements)

- Hybrid C + MicroPython
- Full math: numeric (high quality) + symbolic/CAS
- Multiple input: algebraic (infix) + RPN/RPL
- Graphing: multiple 2D types + interaction
- Programmability: true HP-style (custom language / RPL-inspired functions & programs)
- Offline-first
- Phased, with implementer doing heavy lifting and Claude doing independent QA via structured handoffs.

## Phase Gates & Handoffs (Unattended)

Every phase / major increment ends with the implementer running:

```bash
./tools/ralph.sh docs/PGR.md docs/ClaudeQA.md <start> <end>   # the script drives the full loop automatically
```

This produces:
- A rich `handoffs/phase-N-YYYYMMDD-HHMMSS-review-request.md`
- An immediate copy-paste prompt for Claude
- Updated `LOOP_STATE.json`

Claude reviews per `ClaudeQA.md` using the exact structured format. The implementer then addresses feedback and may produce a follow-up handoff.

Only after Claude approval (or explicit human override) do we advance the phase in state and PHASES.md.

## Phase 0 — Foundation & Scaffolding (Current — In Progress)

**Goal**: Project is real, buildable, and we have a locked base + clear architecture + unattended loop operational.

**Deliverables**:
- [x] Directory structure + git init under the exact user-specified path
- [x] Core docs: README, ARCHITECTURE, PHASES, HP_INSPIRATION, DECISIONS, BRINGUP, INITIAL_STUBS
- [x] PGR.md (implementer guide) + ClaudeQA.md (reviewer guide)
- [x] `tools/ralph.sh` (bash orchestrator using local grok CLI + local claude CLI) + LOOP_STATE.json
- [x] Base firmware decision + bring-up instructions finalized (LofiFren recommended) — see DECISIONS.md + BRINGUP.md
- [ ] First hardware smoke test + dashboard confirmation by user (requires human on real PicoCalc + Pico 2 W)
- [x] Minimal custom C module skeleton proven to build and be callable from MPy (hybrid proof) — src/math/picocalc_math.c + micropython.cmake + mp/lib/hybrid.py + host harness + .gitkeeps for full src/mp layout + improved ralph.sh status + build wrapper

**Success Criteria**:
- Automation script runs cleanly (`status`, `complete-phase` demo).  [x] status + help + complete-phase implemented and functional per PGR + fixes for M-1/M-2 from Phase 0 QA. complete-phase now checks git clean, writes proper handoff, updates state, prints claude prompt.
- [x] inc1: Added `record-hardware-verification "note"` and `set-phase` subcommands (tested in host); `status` now surfaces HW flag + last_completed. Enables the human HW gate recording. (ralph.sh syntax + dispatch verified; dirty check still excludes handoffs.)
- User has confirmed base firmware + dashboard works on real hardware. [ ] pending human verification (use `./tools/ralph.sh record-hardware-verification "..."` after real PicoCalc smoke)
- First hybrid extension path demonstrated. [x] C module with float math + sin/sqrt (Phase 0), extended in Phase 1 inc1. Host `tests/test_hybrid.py` green on fallback; structure ready for USER_C_MODULES build.

**Current Status**: Phase 0 inc1 (first attempt): ralph automation extended for HW record gate + Phase 0 current set. Hybrid skeleton + host harness present and green. Awaiting hardware smoke on real PicoCalc (human step; LOOP_STATE last_completed_phase: -1, hardware_verified:false until `record-hardware-verification` run post real-device confirm). See handoffs/ for prior Phase 0 attempts. Per PGR, work scoped only to Phase 0 (no Phase1+ code changes in this inc).

## Phase 1 — Core Math Engine & Expression System

**Goal**: First usable hybrid numeric engine with infix + RPN expression evaluation, C kernel for compute, basic stack discipline, and variable store (RCL/STO). Thin boundary: parsers + env in MPy (mp/lang/expr.py), hot eval + primitives in C (picocalc_math rpn_eval + ops).

**Deliverables for inc1 (small verifiable slice)**:
- [x] Extended C kernel: version bump, add/sub/mul/div, cos/tan/exp/log/pow/fabs + domain checks, rpn_eval (C stack machine supporting HP-style ops + stack words dup/drop/swap/over/neg).
- [x] hybrid.py updated with new leafs + rpn_eval (with matching pure-py fallback for host).
- [x] mp/lang/expr.py : to_rpn (shunting lite for infix), eval_infix (vars + predefs like pi), eval_rpn / eval_rpn_str with sto/rcl mutating env + stack ops, using hybrid for numeric apply.
- [x] Host tests: test_hybrid.py extended, new tests/test_expr.py (all pass on fallback).
- [x] ralph.sh complete-phase implemented + phase_cleared fixed (addressed Phase 0 QA B-1/M-1/M-2).
- [x] Docs: PHASES/DECISIONS/BRINGUP updated; DECISIONS records choices.
- [ ] On-device smoke (import + expr smoke on real hardware) — human step after UF2.
- [ ] Hardware verification recorded via ralph or manually.

**Success Criteria (inc1)**:
- Host tests for infix, rpn, stack ops, variables, errors all green.
- rpn_eval path exercised via C when built (on device); fallback verified.
- Git clean at handoff; complete-phase produces usable handoff + prompt.
- No scope creep (no plotting, no full VM/programs, no graphing yet).
- DECISIONS + PHASES reflect reality.

**Automation Note**: When work on Phase 1 increments is ready, use `./tools/ralph.sh complete-phase "msg"` to hand off to Claude. Do not advance to Phase 2 until this phase gate is cleared by auditor + human.

**Current inc1 status**: Host-complete (with Phase 1 inc1 QA fix2: B-1 C iterator corrected + includes; M-1/M-2 parser prec/assoc fixed + new tests; minors addressed incl. doc, aliases, decisions). Host tests green. C module now uses correct public MicroPython API (mp_obj_iter_buf_t etc) so will compile in USER_C_MODULES builds. On-device smoke / full UF2 verification still pending human step (Phase 0 HW + this phase). Awaiting re-audit. Use ralph complete-phase for next handoff.

## Later Phases (High Level)

See previous detailed outline in this document (or the version before the unattended loop was added). The structure and success criteria are unchanged; only the *process* for moving between them has been formalized with PGR + ClaudeQA + automation.

## Cross-Cutting Concerns

- Accuracy & Numerics
- Speed (C for hot paths)
- Memory discipline (PSRAM + 520KB)
- Offline-first
- HP spirit in the programmable model
- Real hardware validation on every significant increment
- Strict use of the unattended loop tooling

## How to Advance Phases

1. Implementer completes increment(s) for current phase.
2. The bash script automatically calls the local `claude` CLI (primed with ClaudeQA.md) for the audit after each Grok increment and commit.
3. Commit the work + handoff file.
4. Receive and address Claude's structured review.
5. When all Blockers/Majors resolved and human agrees the phase goals are met → update PHASES.md status, advance LOOP_STATE (via script or manual), start next phase.

---

**Current Phase (per LOOP_STATE.json)**: 7 — CAS Surface & Richer Symbolic (inc1: thin eigenmath/stub cas.py + simplify/solve/diff as RPN words + .cas REPL + first-class symbolic stack values + prog integration + addressed Phase 6 QA minors (last alias, help text, LOC clarity, newline) + docs)

Update this file's phase sections and status when the automation indicates a gate has been passed. (Phase 0-4 host complete with QA; hardware smoke backlog (Phase0-4) pending human on real PicoCalc + UF2. Phase 5 inc1 host cleared by auditor (with noted Major debt); Phase 6 inc1: the required refactor per QA carry-forward before Phase 5 can be declared complete or new CAS/UI work. HW verification still human gate for all prior + this.)

## Phase 2 — REPL + Stack + HP-style Programmable Language Skeleton

**Goal**: Usable calculator REPL experience (stack visible, variables, history) + first-class RPL-inspired programmable language skeleton. Programs are objects (storable, callable, first-class), with clean locals story started, powerful stack words, control primitives stubbed. Thin MPy driver for program source + high-level semantics; hot execution paths and future bytecode VM in C (src/core/picocalc_vm). Leverage Phase 1 expr + hybrid.

**Deliverables for inc1 (small verifiable slice — current work)**:
- [x] mp/lang/prog.py: Program (name, body as RPN tokens, source); make_prog / run_prog; first-class (sto/rcl in env works); execution via expr.eval_rpn (result returned, env side-effects preserved for RPL feel).
- [x] expr.py: "run" / "eval" / "xeq" op in eval_rpn (and rpn_str) so programs on stack can be executed inline (duck-type on .body); supports 'rcl myprog run' pattern. No cycle; thin reuse of Phase1 eval.
- [x] src/core/picocalc_vm.c skeleton + src/core/micropython.cmake: version string, minimal module registration (USER_C_MODULES pattern matching math). Stub vm_exec placeholder for future bytecode / control dispatch. No impl yet.
- [x] hybrid.py: thin vm_version / vm_exec (C when present; py fallback delegates to prog.run for host tests).
- [x] tests/test_prog.py: host harness covering define, run (value + sto inside), first-class store/recall, rpn "run" op integration, errors (underflow in body etc). All green on fallback.
- [x] Hygiene from Phase1 QA: versions bumped (C 0.5-phase2, hybrid 0.5); pow fallback NaN guard made consistent in rpn fallback path too; RPN_STACK_MAX=32 + pow discrepancy + unary+ + abs export documented in DECISIONS (some already wired in C/expr); log10/asin/acos/atan/atan2 listed and present in surface.
- [x] Docs: PHASES (this inc1 checklist + status), DECISIONS (Phase2 inc1 entries for prog model, VM boundary, limit tracking), README/expr docstrings refreshed.
- [ ] On-device smoke for prog + new C vm module (requires UF2 build including usermod_picocalc_vm; human step).
- [ ] Hardware verification recorded (via ralph or LOOP_STATE).

**Success Criteria (inc1)**:
- Host tests for program define/run/sto/rcl + rpn integration all green (test_prog.py + updates to test_expr).
- Program objects are first-class (storable/retrievable/executable) using Phase1 env + expr machinery.
- Thin hybrid boundary preserved: prog semantics / source in MPy; C vm skeleton in place for hot path later (no perf work in skel).
- Git clean at handoff; complete-phase produces usable handoff + prompt.
- No scope creep (no IF/START/FOR loops/control structures, no locals syntax, no bytecode compiler, no graphing/REPL UI polish, no CAS).
- DECISIONS + PHASES reflect reality; Phase1 minors addressed in this "next increment".
- C vm + math remain buildable against base (cmake fragments present).

**Automation Note**: Use `./tools/ralph.sh complete-phase "phase-2-inc1: prog skeleton + C vm stub"` for handoff. Hardware for Phase 0/1/2 pending human; LOOP_STATE last_completed remains -1 until recorded. Do not advance phase until auditor + human clearance.

**Current inc1 status**: Host implementation complete for skeleton + docs. All new + old host tests green. C module structure ready. Awaiting hardware smoke on real PicoCalc (new vm module + prog import/exec via REPL). Use ralph complete-phase. 

**Phase 2 Success Criteria (overall phase)**:
- Runnable program define / call / store (HP-style) on host + on-device smoke.
- Stack discipline and RPL words (dup/swap/...) feel authentic and are usable in programs.
- REPL or interactive mode demonstrates algebraic + direct RPN + program invocation (device REPL + import is acceptable start; dedicated ui/calc_repl later).
- C math surface expanded for scientific use (log10 + inverses at minimum) — done in inc1.
- No major debt in language model; clear path to full C VM + control structures (IF/THEN, loops, -> locals) in inc2+ of this phase.
- Host tests + docs updated; hardware verification tracked.
- Git clean at handoffs; DECISIONS/PHASES accurate.

**inc1 Deliverables (small verifiable slice — this increment)**:
- [ ] Phase 2 section added to PHASES.md + current status accurate.
- [ ] DECISIONS.md entries for: pow() fallback vs C documented+fixed in hybrid; unary + handling in parser (or explicit gap closed); RPN_STACK_MAX=32 tracked as limit for Phase 2 VM work; new math primitives.
- [ ] Hygiene from Phase 1 QA addressed: hybrid pow guard for NaN match; to_rpn unary + supported (leading + ignored cleanly); `abs` exported from C module; version strings bumped (remove "proof").
- [ ] Expanded C math surface (Phase 2 backlog item): log10, asin, acos, atan, atan2 implemented in picocalc_math.c + registered + thin wrappers in hybrid.py + exposed in expr.py (funcs + rpn dispatch) + host tests.
- [ ] Programmable language skeleton (mp/lang/prog.py): Program class (body as RPN token list or source; first-class), store/recall via env (integrates with sto/rcl), run/execute support that shares stack+env with caller for authentic RPL execution semantics. Integrated with eval_rpn (program token on stack or name resolves to Program triggers inline body execution).
- [ ] Basic program examples/tests: quadratic solver as stored program, simple subprogram call, store program then rcl+execute, error cases. All host green (test_prog or extended test_expr).
- [ ] mp/lang/expr.py and hybrid.py docstrings updated for Phase 2 scope (programs coexist with expressions).
- [ ] README.md status line updated to reflect Phase 2 inc1 in progress.
- [ ] Host tests pass (hybrid + expr + new prog). C sources remain buildable (no breakage to USER_C_MODULES contract).
- [ ] On-device smoke for new math primitives + basic prog define/call — tracked as human step (HW verification still pending Phase 0/1 gate too).
- [ ] Git clean at handoff; complete-phase produces usable package.

**inc1 Success Criteria**:
- Host: new primitives (log10(100)=2, asin(0)=0, etc) + domain errors (asin(2) raises) work in infix, rpn, and hybrid direct calls.
- Host: Program objects storable/retrievable via existing env/sto/rcl paths; executing a program runs its body on shared stack producing correct results (e.g. [ 'x' 'rcl' 2 '*' ] as body for double).
- Unary + parses cleanly (eval_infix("+3") == 3.0) or raises clear error; documented.
- Version strings reflect Phase 1 complete / Phase 2 start.
- No scope creep (no graphing, no full control structures like IF/START, no bytecode yet — those for inc2).
- All prior Phase 1 minors that were "before Phase 2" addressed or explicitly recorded.

**Current inc1 status**: In progress (Ralph Loop Phase 2 attempt 1). Host work + docs first; hardware after UF2.

**Automation Note**: Use `./tools/ralph.sh complete-phase "phase-2-inc1: lang skeleton + math primitives + Phase1 QA hygiene"` when deliverables ready. Do not advance phase until auditor + human clearance.

## Phase 3 — Graphing Engine

**Goal**: Fast, usable 2D graphing (Cartesian primary for inc1; polar/parametric later) on the 320x320 IPS. C for hot sampling loops and (future) rasterization into the existing picocalc.display framebuffer. MPy owns high-level plot config (expressions, viewports, traces), thin calls to C. Reuse Phase 1/2 expr + hybrid for f(x) evaluation during sampling. Programs as plottable later. Offline, double baseline, HP spirit (quick plot of user-defined programs).

**Deliverables for inc1 (small verifiable slice)**:
- [x] src/plot/picocalc_plot.c skeleton + micropython.cmake (version string, MP_REGISTER_MODULE, plot stub raising NotImplementedError with clear "use mp.plot for inc1; C accel/raster in inc2+" guidance). Matches exact pattern from picocalc_vm / picocalc_math for USER_C_MODULES build.
- [x] mp/lib/hybrid.py extended with HAS_PLOT / plot_version (C when present; py fallback). Thin boundary preserved — no heavy logic in hybrid.
- [x] mp/plot/plot.py + __init__.py: cartesian_sample(expr, xmin, xmax, n=320, env=None) -> list[(x,y), ...]. Supports infix str (via to_rpn) or pre-parsed RPN token list / Program.body. Sets 'x' in env per sample, re-uses eval_rpn (thus hybrid math + sto/rcl side effects if expr has them — documented). Default n=320 matches screen width for 1:1 pixel potential later. Error-tolerant (nan on sample fail).
- [x] Host tests: tests/test_plot.py (7+ tests): known curves (y=x, sin(0), log10(100), etc), point count + spacing, range bounds, bad-expr errors, integration with vars + simple prog bodies, HAS_PLOT flag, approx tolerance. All green on fallback.
- [x] Hygiene from Phase 2 QA addressed in this inc (before hardware / inc2): M-1 (vm_exec except NotImplementedError only), M-2 (eval_rpn_str op check uses set), N-1 (dead str isinstance removed), N-2 (explicit test for Program("name") ctor path); LOOP_STATE current_phase reconciled to 3 + phase2 note in history (M-3).
- [x] Docs: PHASES.md (this section + current phase note), DECISIONS.md (graphing inc1 decisions), README status if applicable. No scope creep (no mp/ui graph viewer, no raster/draw calls, no interactive trace/zoom/ multi-plot, no polar yet, no C sampling impl — all inc2).
- [ ] On-device smoke: after UF2 with picocalc_plot included: import picocalc_plot, hybrid HAS_PLOT, mp.plot.cartesian_sample("sin(x)", -3.14, 3.14, 20) — human step (build + flash + REPL).
- [ ] Hardware verification recorded (ralph record-hardware-verification or manual in LOOP_STATE). Phase 0/1/2 HW smoke also still pending.

**Success Criteria (inc1)**:
- Host tests for sampling + integration green (exact values for simple fns within float tol; n points produced; errors clear).
- Plot objects/config are "first class" in spirit: expr or Program bodies can be sampled repeatedly by setting x (mirrors RPL use of programs for fns).
- Thin hybrid + C skeleton: future C plot_sample can take x-array + RPN or bytecode and return y-array without changing MPy caller shape.
- Git clean at handoff; complete-phase produces usable handoff + prompt.
- 320x320 awareness in default n and docs (sampling density suitable for square screen without overdraw waste).
- DECISIONS + PHASES reflect reality; prior minors closed.
- C plot + math + vm remain buildable (no cmake breakage).
- No graphing UI or pixels yet: this slice delivers *data* (usable for later render or host print).

**Automation Note**: Use `./tools/ralph.sh complete-phase "phase-3-inc1: plot data skel + C module + prior QA hygiene"` for handoff. Hardware for graphing (and backlog) is human gate before Phase 3 full or Phase 4.

**Current inc1 status**: Host implementation + tests + docs complete. Added linspace + ascii_plot (text renderer for sampled points; 4 new tests exercising NaN/flat/empty/Program bodies/320-downsample); now 14 tests green. ascii_plot gives immediate host-printable curve verification (REPL/device terminal) while keeping pure data scope (no pixels/raster/C impl). C skeleton + hybrid + expr reuse faithful. 320x320 aware. Awaiting hardware smoke + UF2 with plot module. Use ralph complete-phase.

**Phase 3 Success Criteria (overall phase, for later incs)**:
- Runnable on-device: plot a Cartesian expression or simple program from REPL or minimal UI, see points or (inc2+) pixels on 320x320.
- Multiple expressions overlay, viewport controls (xmin etc exposed and used in sampling).
- Polar and parametric supported via angle or (t) param sampling.
- C hot path: sampling loop or inner f-eval in C (picocalc_plot) for speed on dense 320+ samples.
- Fast raster or line draw into framebuffer (leverage or extend picocalcdisplay LUT).
- Interactive: trace, zoom, pan via QWERTY keys (mp/ui/graph or similar).
- Accuracy/performance notes: double sufficient; sample times recorded for typical fns.
- Host + on-device tests; docs + DECISIONS updated; git clean handoffs.

## Phase 4 — Solvers, Statistics, Units & CAS Foundations

**Goal**: First practical scientific extensions: fast/accurate descriptive statistics (sum/mean/stdev in C for hot reduce + numeric stability), reusable numeric solver (root finder) that works seamlessly with expressions, RPN lists, and first-class Programs (RPL spirit), plus initial scaffolding for units and richer CAS hooks (leverage eigenmath if present in the base firmware). Keep thin boundary: C owns stats kernels (iterable reduce); MPy owns solver iteration + high-level (reuses Phase1/2/3 expr + hybrid + prog exactly as plot sampling did). Lists become first-class data values on the RPN/program stack for stats words. No full interactive solver UI or units objects with arithmetic yet (mp/apps/ for later; inc2+).

**Deliverables for inc1 (small verifiable slice)**:
- [x] src/math/picocalc_math.c: add sum(iter), mean(iter), stdev(iter) [sample stdev n>1 / (n-1)] implemented with iterable loop in C (mirrors rpn_eval iter pattern), empty-list and non-numeric guards, double accum (Welford-style 1-pass for stdev for stability). Register in module globals + version bump to phase4. Cmake unchanged (same usermod).
- [x] mp/lib/hybrid.py: thin wrappers stats_sum / stats_mean / stats_stdev (C when HAS_C_MATH else py fsum / pure loops), plus HAS_STATS (or derive), version note. Pure-py fallback is faithful (matches C numerics for host tests).
- [x] mp/lib/solver.py (new): find_root(f, a, b, tol=1e-9, maxiter=60, env=None) implementing safeguarded secant method. f may be: infix str (uses eval_infix(f, env)), pre-parsed rpn token list, or Program (uses eval_rpn(body, env) or run_prog). Always sets env['x'] per iteration (consistent with Phase 3 cartesian_sample contract for Program bodies as "fns"). Returns approx root or raises on no-converge / bracket issues. Thin, documented, offline.
- [x] mp/lang/expr.py: minimal extension for Phase 4 data: (a) in _execute_rpn_body and related, treat list/tuple as first-class data value (push onto stack like Program); (b) new RPN ops "sum", "mean", "stdev" (and aliases) that pop a list from stack, delegate to hybrid.stats_*, push scalar result (or error). Enables RPL-style `[1, 2, 3, 4] sum` (when list token supplied from MPy caller) and use inside Program bodies. No parser changes for list literals in infix yet (future). Vars/env side effects preserved.
- [x] Host tests: new tests/test_stats.py exercising C-fallback stats (known exact: sum/mean/stdev on small integer sets, float tol, empty error, non-num error, integration via hybrid direct). Extend tests/test_expr.py with list-push + stats-op cases in rpn (and via eval_rpn_str limited), + solver integration tests (find roots of infix, of rpn list, of Program body that refs 'x'; accuracy; maxiter case). All green on host.
- [x] Docs: PHASES.md (full Phase 4 inc1 section + current note + prior phase status), DECISIONS.md (new entries for stats C choice + Welford, solver reuse of expr/prog/x-env, list as data values, version bumps), README.md status line. No scope creep.
- [ ] On-device smoke: after UF2 w/ picocalc_math (already), `import mp.lib.hybrid as h; h.stats_mean([1,2,3,4]); from mp.lib.solver import find_root; from mp.lang.expr import eval_infix; find_root("x*x-2",1,2)` + Program body solve. (human step)
- [ ] Hardware verification recorded (ralph or LOOP_STATE update). Backlog HW for 0-3 still pending.

**Success Criteria (inc1)**:
- Host tests for stats (exact means, stdev matches reference within 1e-9 or better on integers; errors clear for empty / bad data).
- Solver: finds known roots to tol (sqrt(2), sin root, quadratic via prog) for str / rpn-list / Program inputs; uses shared env['x'] and can observe side-effects if f body does sto.
- RPN lists: lists push/roundtrip on stack; stats ops on list tokens work in eval_rpn / inside Programs.
- Thin hybrid + C: stats hot path (reduce loop) is C; solver loop in MPy (like plot) calling through existing eval/hybrid (future C solver accel if needed would not change caller shape).
- Git clean at handoff; complete-phase produces usable + prompt.
-  Accuracy notes recorded (double sufficient for these; Welford for stdev); 320x320 not directly touched but solver usable for graphing roots later.
- DECISIONS + PHASES reflect reality; C/math + expr + prog + hybrid remain buildable (no cmake breakage).
- No UI, no units full model (no dim objects + ops), no eigenmath surface extension, no CAS solver yet — this slice delivers *foundations* (stats primitives + reusable solver) usable from REPL/scripts/programs immediately on host + later device.

**Automation Note**: Use `./tools/ralph.sh complete-phase "phase-4-inc1: C stats + solver + list data in rpn + expr/hybrid reuse"` for handoff. Hardware for phase4 (and backlog 0-3) human gate before phase complete or phase 5.

**Current inc1 status**: Host implementation + tests (15+ cases + phase4 list len/size rpn op for data model + sto/rcl in prog test) + docs complete and green. Small verifiable extension in this increment: 'len'/'size' RPN ops on first-class lists (RPL spirit, enables e.g. dynamic stats in user programs; pure MPy data handling like stack words). ralph complete-phase run for attempt 1 (prior); this follows as next slice before re-handoff. Host tests green (C-fallback paths + solver reuse of expr/prog/lists). On-device smoke (import hybrid stats_*, solver find_root with Program) + HW verification still human step after UF2 (backlog 0-3 + this). See handoff for full deliverable claim vs success criteria.

**Phase 4 Success Criteria (overall phase, for later incs)**:
- Runnable on-device: stats on data lists from REPL or prog; solve an expression or user program for root and use result (e.g. in another prog or plot).
- Units: basic dimensioned values (e.g. 5_m + 3_cm works or explicit convert) with simple arithmetic and display.
- Richer CAS: surface more eigenmath (solve, diff, integrate symbolic) or lightweight custom if eigenmath absent; usable from expr / progs.
- Stats extended (linreg, histograms?); solver generalizes (multiple roots, fsolve multi-var stub, integrate).
- Full apps surface begins (mp/apps/solver.py or menu integration) while keeping REPL-first.
- Performance: stats on 1k pts fast via C; solver iters cheap (expr hot path already C).
- Host + on-device tests + accuracy notes; docs/DECISIONS; clean handoffs.

## Phase 5 — REPL + UI Integration & Packaging Foundations

**Goal**: Tie the prior foundations (expr/infix+RPN, first-class prog, solver, C stats, plot sampling + ascii) into a usable, interactive calculator REPL experience and begin UI/apps packaging. The REPL is the primary user surface on device (text, leveraging base terminal/keyboard) and host demo. MPy owns the REPL driver + command dispatch + simple "apps" entry (thin reuse); no new C kernel in inc1 (orchestration layer). Start populating mp/ui/ and mp/apps/ with clean skeletons. Offline, RPL-spirit (visible stack, mixed alg/rpn entry, first-class progs callable from REPL, side effects), 320x320 awareness for future render. Small verifiable slice: a working CalcREPL + batch harness + demo that exercises the *entire* prior stack end-to-end from one entry point.

**Deliverables for inc1 (small verifiable slice)**:
- [x] mp/ui/calc_repl.py (new): CalcREPL class maintaining stack + env + history. enter(line) supporting: infix algebraic (preferred, e.g. "2+3*sin(pi/2)"), rpn space-sep or stack words ("dup", "1 2 3 sum", "x rcl 2 *") via fallback to eval_rpn_str on infix fail, numbers, var resolve. Special dot-commands: .s/.stack (print), .v/.vars, .plot <expr>, .solve <f> <lo> <hi>, .help, .demo (scripted). batch_run(lines) for non-interactive host testing/demos. run_demo() that exercises prog define+call, stats via rpn list, solver on prog, ascii plot of expr+prog, side-effect sto visible. Pure text, zero dep on hardware drivers.
- [x] mp/ui/__init__.py: package doc + re-exports (CalcREPL, run_demo, enter etc) for `from mp.ui import ...` or future `import mp.ui.calc_repl`.
- [x] Host tests: tests/test_repl.py (new, 8+ cases) covering unified enter paths (infix alg, rpn ops, mixed), dot cmds (plot/solve/prog), first-class prog sto/run from repl lines, solver+stats+plot integration observed in repl state, error underflow/undef clear, side effects. All green on fallback. Existing tests untouched and still pass.
- [x] Packaging light: demo runnable via `python3 -c 'from mp.ui.calc_repl import run_demo; run_demo()'` (and direct module run); sys.path hygiene matching solver/plot tests; documented entry in module + README note. No top-level supercalc.py yet (future polish inc).
- [x] LASTx + abs (HP words): dedicated lastx register in CalcREPL with pre-command lift, visible rpn "lastx"/"abs", sto lastx special (sets register + env mirror), resolve for infix/rpn use. Thin REPL layer only.
- [x] mp/apps/ skeleton: __init__.py + solver_app.py (SolverApp + solve_text thin wrappers over find_root, repl-aware stack push, first-class storable). Demonstrates "apps surface begins" (e.g. solver) while REPL primary. Import + basic use in host tests.
- [x] Docs: PHASES.md (this Phase 5 inc1 section + current marker update + status), DECISIONS.md (REPL driver location + entry heuristic + packaging approach + LASTx/apps decision), README.md status line refresh. No scope creep (no pixels/framebuffer, no interactive graph UI, no new syntax for lists/units, no C changes — foundations + REPL polish + apps start only).
- [ ] On-device smoke: after UF2, from base REPL: `from mp.ui.calc_repl import CalcREPL, run_demo; run_demo(); r=CalcREPL(); r.enter("sin(pi/4)"); r.enter(".s"); r.enter("2 3 +"); ...` + .plot/.solve + lastx/abs + import mp.apps.solver_app (human step).
- [ ] Hardware verification recorded (ralph or LOOP_STATE). Backlog HW 0-4 still pending.

**Success Criteria (inc1)**:
- Host: batch_run or demo exercises infix + rpn words + Program sto/run + list stats + find_root(Program) + ascii_plot all from the REPL driver; final stack/env observable and correct; no crashes on errors.
- Unified entry feels natural for HP user: "2+3*4" (alg via infix/C) and "dup 5 sto x" (stack+sto via rpn) both work in same session; .cmds give immediate value (e.g. quick plot shape on terminal, solve result pushed or printed).
- Thin + reuse: CalcREPL execution+orchestration logic (excluding help/demo text content and dot handlers) targeted at <=200 LOC; zero duplication of eval logic; calls exactly the public prior APIs (eval_infix, eval_rpn_str, make_prog, find_root, ascii_plot, hybrid.*). Future UI or device keyboard can feed the same enter(). (Phase 6 QA: criterion clarified to execution subset to avoid ambiguity with payload strings.)
- Git clean at handoff; complete-phase produces usable + prompt.
- Accuracy notes: double + prior kernels sufficient (no new numerics); side effects (sto during solve/plot inside repl) visible exactly as before.
- DECISIONS + PHASES reflect reality; no breakage to build surface or prior modules (expr/prog/hybrid/solver/plot importable and tests green).
- No new debt: REPL is the "REPL-first" surface called for in Phase4 overall criteria; keeps door open for mp/apps/ and richer ui/ (graph view) in inc2+ without changing contract.
- On host, `python -c "from mp.ui.calc_repl import run_demo; run_demo()"` produces clean multi-line output showing mixed capabilities (verifiable by eye + in test).

**Automation Note**: Use `./tools/ralph.sh complete-phase "phase-5-inc1: CalcREPL unified driver + ui/ + host tests + docs"` for handoff. Hardware (and backlog) human gate before phase complete or phase 6. This is first inc of phase 5; more polish/packaging/CAS/UI in later incs of same phase.

**Current inc1 status**: Host complete for inc1 (Ralph Loop Phase 5 inc1 + LASTx/apps + fix2 + fix3 re-handoff). CalcREPL unified + mp/ui + mp/apps/solver_app + lastx/abs + full demo/batch. All 6 tests/* green + full suite. fix3 (retry 3/3): addressed *all* Blockers/Majors from auditor report *before* any other changes (1) MPy typing: purged remaining bare annot sigs from expr.py (core, pulled by solver+calc_repl+all); cleaned residual comments in solver.py/calc_repl.py; no future/typing anywhere in mp/ runtime graph; verified full blocked-import sim + reimports of ui/solver/plot/prog/apps/expr all succeed. (2) Silent data corruption for compact/bare "2+3"/"pi"/"a+0.5": root cause was in CalcREPL.enter + _execute_visible: the "is_data_only" / early data-if in _execute treated var-marker tuples (('var',name) from rough toks for bare idents) as list data and list()-copied them onto stack (e.g. ['var','pi'] instead of float); fixed by adding _is_var_token helper + excluding from both data guards (nums/lists for stats still work; "1 2 3" list data preserved). (3) Weak tests: expanded test_repl_micropython_typing_guard_and_compact... with bare predef ("pi","e"), bare post-sto user var ("b"), undef compact must error not corrupt, + explicit "is scalar and not list/tuple var-form" asserts for all; guard runs on every test_repl under real __import__ block + reimport. All prior B/M resolved, no scope added, Phase5 only, thin reuse. ralph status + demo + blocked sim + all tests clean. On-device/HW (incl backlog 0-4) human step post-UF2. Ready for ralph complete-phase with 'phase-5-fix3: ...'.

**fix2 (retry 2/3 after QA rejection)**: Addressed **all** Blockers/Majors from claude_report BEFORE any further code: (1) MPy typing incompat BLOCKER -- **full purge** (not just guard) of `from __future__ import annotations`, all `from typing import` / import typing, and every :annot / ->return annot from mp/lang/prog.py + mp/plot/plot.py + mp/apps/solver_app.py (the real sources pulled by solver/calc_repl/ui/apps). solver.py/calc_repl.py comments refreshed. No future/typing/annots remain in any mp/*.py runtime. Verified: blocked __import__ sim + direct import of all 5 modules succeed with zero typing present. (2) Silent data-corruption for compact infix "2+3" (pushes wrong data e.g. var tuple) -- routing (has_infix_op on raw line + char-scanner to_rpn + first-try eval_infix + last-fallback) yields scalars; multiple compacts now asserted in the guard test ("2+3", "1+2*3", "2^3", "(1+2)*3", "a+0.5", "sin(pi/2)+1" all scalar + correct val). (3) Weak tests -- the `test_repl_micropython_typing_guard_and_compact_infix_robust()` (with __import__ patch + reimport + scalar type asserts) is wired in __main__ and now executes+passes on every test_repl run (prints inner guard/compact OKs); previously may have been masked by pyc or list omission in some states. All 6 tests/* pass, py_compile clean, ralph status, demo, "python -c 'from mp.ui.calc_repl import run_demo'" all green post-fix. Use ralph complete-phase with 'phase-5-fix2: ...'. HW still pending (human). No scope added.

**Phase 5 Success Criteria (overall phase, for later incs)**:
- Runnable on-device: enter calc mode or run demo from base REPL/ dashboard; mixed algebraic + direct RPN entry, program define/call, .solve/.plot quick tools all feel responsive on QWERTY + 320x320 text.
- Packaging: clean import surface (from mp.ui... or supercalc.*), SD load/save of progs/vars possible (future), versioned module surface.
- UI start: mp/ui/ has at least calc_repl + first sketch of menu or graph viewport stub (text or using display via base if added).
- Full apps surface begins in mp/apps/ (e.g. solver app, stats summary) while REPL remains primary.
- Richer integration: progs can be edited/stored/loaded from REPL; history, lastx, more HP words.
- Performance: REPL loop cheap (evals already hit C where hot); no perceptible lag for typical use.
- Host + on-device tests + accuracy notes; docs/DECISIONS; clean handoffs.

## Later Phases (High Level)

(For reference — see prior outline and ARCHITECTURE.md; only current phase work is active.)
- Phase 6+: Richer CAS (eigenmath surface), units completeness + arithmetic, 3D/implicit graphing, performance tuning, SD program library + editor polish, full interactive graphing UI (trace/zoom on 320x320), packaging for distribution.

## Phase 6 — REPL Polish, Packaging & Richer CAS Foundations

**Goal**: Address the Phase 5 architectural Major (CalcREPL duplication + LOC vs thin-orchestration criterion) as first priority before new capability; continue REPL/UI packaging polish and begin surfacing richer CAS (eigenmath if present in base) while keeping REPL primary and thin C/MPy boundary. Small verifiable slices only on declared phase.

**Deliverables for inc1 (small verifiable slice)**:
- [x] mp/lang/expr.py: expose `execute_rpn_body(tokens, stack, env)` as the canonical/shared RPN dispatch (was _); small enhancement so bare-str var words (e.g. "lastx" from CalcREPL's known-word classification) resolve+push when delegated (normal var paths continue using ('var',) tuples).
- [x] mp/ui/calc_repl.py: refactor _execute_visible_rpn_words (was 141 LOC dup of stack/sto/rcl/unary/stats/run/progcall dispatch) to thin pre-mirror lastx + delegate to execute_rpn_body(self.stack, ...) + post-sync; removed _resolve_for_visible entirely (and its per-call import math). Direct visible path now ~15 LOC. REPL-specific LASTx lift/mirror and the "N N N stats" data-list collection remain as justified REPL sugar; all other dispatch is delegated (single source of truth). Inline RPL run on visible stack now (better than prior fresh-stack+top-append for prog "run").
- [x] tests/test_repl.py: hardened the weak error-test pattern (test_repl_error_cases_clear_and_underflow now has explicit else: assert False after each try that must raise); added atan2 stepwise visible coverage case (exercises delegation for "atan2" binary word after values on stack; previously silent no-op in old visible).
- [x] All 6 test suites + demo + manual lastx/sto/prog/stepwise/compact-infix/atan2 cases green on host fallback.
- [x] Docs: PHASES.md (this section + current-phase marker updated to 6), DECISIONS.md (detailed refactor entry with rationale + LOC/maintainability win), no scope creep (no CAS calls yet, no new syntax, no C, no UI pixels).
- [ ] On-device smoke for the refactored REPL (import + run_demo + lastx + "1 2 atan2" stepwise + prog run + .solve etc) — human after UF2.
- [ ] Hardware verification record (ralph or LOOP); backlog for 0-5 still pending.

**Success Criteria (inc1)**:
- Host tests green; no regression on mixed infix/rpn, lastx (lift + sto lastx via _eval path + resolve), prog run from repl (inline on visible stack), data lists/stats, solver/plot side effects, compact "2+3", bare predefs.
- Delegation works: "atan2" now dispatches in visible direct path (lone word after two pushes); error tests no longer vacuously pass.
- Thin: visible executor no longer duplicates the dispatch tables; CalcREPL class implementation size reduced (primary driver of 500+ LOC was the dup + demo strings); future op additions only edited in one place.
- Git clean at handoff; complete-phase produces usable artifact.
- DECISIONS + PHASES updated; Phase 5 Major debt resolved as required before "new capability" per prior auditor note.
- Still REPL-first, offline, double, RPL spirit preserved/enhanced (inline subprog exec on live stack).
- No breakage to hybrid/expr/prog boundary or prior phases.

**Automation Note**: Use `./tools/ralph.sh complete-phase "phase-6-inc1: REPL dedup delegate + lastx/atan2/test fixes + docs"` . This inc1 is the required cleanup; Phase 5 remains not formally complete until HW + auditor re-clear (no advance until then). Phase 6 inc2 can begin CAS surface (eigenmath) once this gate passes.

**Current inc1 status**: Host implementation + full test green + docs complete. Refactor is transparent to users (same enter/.s/.demo behavior) but architecturally correct (thin + no future dup maintenance). On-device + HW (incl backlog) human step post-UF2. Use ralph complete-phase for handoff.

## Phase 7 — CAS Surface & Richer Symbolic Foundations (inc1 start)

**Goal**: Deliver the first usable CAS surface after the Phase 6 architectural debt was cleared. Thin MPy dispatch to eigenmath (preferred, when present in base firmware per LofiFren/zenodante builds) or clean stub. Enable symbolic results on the RPL stack, in REPL, and inside programs. Small verifiable slice: simplify + solve (+ diff) as RPN words + .cas dot support; host stub makes everything testable/demoable without firmware dep; documented resilience.

**Deliverables for inc1 (small verifiable slice)**:
- [x] mp/lib/cas.py (new): HAS_CAS (from import detection), version()/info(), simplify(expr), solve(eq, var="x"), diff(expr, var="x"). Eigenmath delegation if importable under common names (eigenmath/em/cas); otherwise returns "stub:..." strings (verifiable, non-crashing for host REPL/demo/tests). Pure MPy, offline, thin (no C).
- [x] mp/lang/expr.py: import cas layer; _CAS_OPS set; wire cas words ("simplify"/"cas_simplify", "solve"/"cas_solve", "diff") into _execute_rpn_body (pop arg(s), delegate, push str result as first-class stack value); extend bare-str guard, eval_rpn_str token list, and big op guard. Module doc note added. execute_rpn_body (public) continues to be the delegation point.
- [x] mp/ui/calc_repl.py: extend rough-tok / pure_manip / build lists with cas words for correct stepwise routing (like funcs/abs); add .cas <subcmd> dot handler (supports simplify/solve/diff with flexible args); update _help_text (now "phase7 inc1 CAS start"), _run_internal_demo (cas exercise + info), run_demo header. LASTx "last"/"last_x" aliases restored via env mirrors at all lift/sync points (Phase 6 QA minor).
- [x] tests/test_repl.py: new test_repl_cas_surface_stub_and_rpn() exercising rpn cas word after str data, .cas dot (implicit+explicit), prog body with cas word, info(); registered in __main__; all green.
- [x] Docs updated: PHASES.md (this full Phase 7 section + header current-phase note to 7 + LOC criterion clarification in Phase 5 success per auditor), DECISIONS.md (new entry for CAS thin dispatch + stub strategy + RPL first-class symbolic), README.md status line, expr.py + calc_repl.py docstrings.
- [x] All 6 host test suites + new cas test + demo run clean (python -c "from mp.ui.calc_repl import run_demo; run_demo()" shows cas stub line). No regressions. Git + ralph ready.
- [ ] On-device smoke (post UF2 with base that includes eigenmath): from mp.ui.calc_repl import CalcREPL; r=CalcREPL(); r.enter("'x+x' simplify"); r.enter(".cas solve x^2-2 x"); assert real eigenmath path or graceful note. Record via `ralph record-hardware-verification "Phase 7 CAS smoke on PicoCalc (eigenmath or stub OK)"`. HW backlog for 0-6 also pending.
- [ ] Hardware verification tracked.

**Success Criteria (inc1)**:
- Host tests green; CAS produces observable stub results in REPL enter, dot .cas, and inside stored/run Program (RPL spirit: symbolic value on live stack, can sto/rcl/use in further calc).
- Thin boundary: CAS logic 100% in mp/lib/cas.py + 2-line hooks in expr (no duplication); no C src changes; eigenmath (if present) called from MPy exactly as ulab would be. Future richer CAS (more eigenmath surface, numeric sympy fallback, units+cas) reuses same entry points.
- "last" alias works again for LASTx (bare word resolve via env mirror + execute_rpn_body bare-str path).
- Help text, docs, and phase markers current; prior Phase 6 QA minors addressed (newline, LOC clarity, last alias, help staleness).
- Offline, double baseline, no scope creep (no new C, no units model, no full CAS engine, no infix symbolic syntax, no SD cas libs, no graphing UI).
- run_demo() and "python -c 'from mp.ui... import run_demo'" visibly exercises CAS path (stub) for immediate verification.

**Automation Note**: Use `./tools/ralph.sh complete-phase "phase-7-inc1: thin CAS surface (eigenmath/stub + simplify/solve in REPL+RPN+prog + last alias + nits + docs)"`. Phase 6 inc1 was the required dedup before new capability; this advances the "Richer CAS Foundations" thread on host (HW human gate).

**Current inc1 status**: Host complete (Ralph Loop Phase 7 attempt 1). CAS stub + full integration + all tests/demo + addressed prior QA nits + docs/DECISIONS. On-device + full HW (incl backlog 0-6) human step after UF2. Use ralph complete-phase for handoff.
