# Ralph Loop Handoff — Phase 5
**Generated**: 2026-06-13T23:20:44-04:00
**Implementer Message**: phase-5-fix3: purge expr annots (MPy typing B) + fix REPL var-tok data corruption + harden guard tests (all B/M addressed pre-handoff)
**Current LOOP_STATE**:
```json
{
  "current_phase": 5,
  "status": "awaiting_qa",
  "last_completed_phase": -1,
  "phase_history": [
    {
      "phase": 0,
      "started": "2026-06-12",
      "status": "in_progress",
      "description": "Foundation & Scaffolding + Unattended Loop setup (inc1)",
      "last_update": "2026-06-12",
      "notes": [
        "First attempt per PGR: phase-0-inc1 focused on automation completeness for HW record + status per Phase 0 success criteria.",
        "Hybrid C skeleton (minimal proof) + cmake + hybrid.py + test_hybrid present (host fallback green).",
        "Handoffs from prior history preserved; loop reconciled for Phase 0 inc1 work only (no future scope).",
        "record-hardware-verification subcommand implemented + tested (exercised with TEST note; human will invoke on real PicoCalc after dashboard/REPL/hybrid smoke to flip verified + last_completed=0).",
        "Handoff generated: handoffs/phase-0-20260612-231211-review-request.md",
        "Handoff generated: handoffs/phase-4-20260613-001320-review-request.md",
        "Handoff generated: handoffs/phase-4-20260613-004410-review-request.md",
        "Handoff generated: handoffs/phase-4-20260613-005324-review-request.md",
        "Handoff generated: handoffs/phase-5-20260613-011047-review-request.md",
        "Handoff generated: handoffs/phase-5-20260613-230802-review-request.md",
        "Handoff generated: handoffs/phase-5-20260613-231053-review-request.md"
      ]
    }
  ],
  "last_handoff": "handoffs/phase-5-20260613-231053-review-request.md",
  "hardware_verified": false,
  "notes": "Phase 0 inc1 (first attempt): set current_phase=0 per task; added ralph record-hardware-verification + set-phase support for pending HW gate + automation success criteria. Hybrid proof structure in place (C src/math + mp/lib/hybrid + tests). HW smoke pending human confirmation on real PicoCalc (use ralph record-hardware-verification after dashboard/REPL/hybrid smoke).; complete-phase at 20260612-231211; set-phase 4 (was 0); complete-phase at 20260613-001320; complete-phase at 20260613-004410; complete-phase at 20260613-005324; set-phase 5 (was 4); complete-phase at 20260613-011047; complete-phase at 20260613-230802; complete-phase at 20260613-231053",
  "hardware_note": ""
}
```

## 1. Role Instructions
**You are Claude acting strictly as the Independent QA Reviewer per `ClaudeQA.md`.**
Read the full ClaudeQA.md (in repo). The implementer followed PGR.md.
Do not write code. Produce the exact structured review format. End with one of:
CLEARED TO CONTINUE
PHASE COMPLETE - CLEARED TO ADVANCE
NEEDS WORK - DO NOT ADVANCE
Also write full report to claude_report.txt .

## 2. Phase Goals & Success Criteria
(Excerpt from docs/PHASES.md for the active phase)
```
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
- Thin + reuse: CalcREPL is <200 LOC orchestration; zero duplication of eval logic; calls exactly the public prior APIs (eval_infix, eval_rpn_str, make_prog, find_root, ascii_plot, hybrid.*). Future UI or device keyboard can feed the same enter().
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
```

## 3. What Was Delivered (implementer claim)
phase-5-fix3: purge expr annots (MPy typing B) + fix REPL var-tok data corruption + harden guard tests (all B/M addressed pre-handoff)

Key files changed (since prior):
docs/DECISIONS.md
docs/PHASES.md
mp/lang/expr.py
mp/lib/solver.py
mp/ui/calc_repl.py
tests/test_repl.py

## 4. Git Activity
```
e52748c phase-5-fix3: purge expr annots (MPy typing B) + fix REPL var-tok data corruption + harden guard tests (all B/M addressed pre-handoff)
7ac5963 phase-5-fix2: add handoff artifact + LOOP_STATE awaiting_qa (ralph complete-phase)
b5cb21a phase-5-fix2: add handoff artifact + LOOP_STATE awaiting_qa (ralph complete-phase)
d1ff772 phase-5-fix2: purge MPy typing/future/annots (prog+plot+solver_app) + compact infix scalar asserts in guard test + docs (all B/M from auditor fixed before re-handoff)
26979b0 phase-5-fix2: fix MPy typing (solver/calc_repl comments + apps future; guard coverage in tests) + compact infix data push + weak tests + docs
50d937a phase-5-inc1: Grok implementer work (auto-fallback commit)
```

## 5. Next
After review: address any Blockers/Majors, then either re-run complete-phase for fixes or (on clearance) let automation/script advance phase.
