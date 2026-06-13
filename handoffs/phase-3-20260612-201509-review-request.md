# Ralph Loop Handoff — Phase 3
**Generated**: 2026-06-12T20:15:09-04:00
**Implementer Message**: phase-3-fix2: clean handoff after ralph automation fixes (msg capture, early helpers, phase-aware prompts, dirty detection, safety defaults)
**Current LOOP_STATE**:
```json
{
  "current_phase": 3,
  "status": "awaiting_qa",
  "last_completed_phase": -1,
  "phase_history": [
    {
      "phase": 0,
      "started": "2026-06-12",
      "status": "awaiting_qa",
      "description": "Foundation & Scaffolding + Unattended Loop setup",
      "last_update": "2026-06-12",
      "notes": [
        "Handoff generated: phase-0-20260612-150759-review-request.md",
        "Handoff generated: phase-0-20260612-154010-review-request.md",
        "Handoff generated: phase-0-20260612-154016-review-request.md",
        "Handoff generated: phase-0-20260612-154313-review-request.md",
        "Handoff generated: phase-0-20260612-154318-review-request.md",
        "Handoff generated: phase-0-20260612-154621-review-request.md",
        "Handoff generated: handoffs/phase-1-20260612-164414-review-request.md",
        "Handoff generated: handoffs/phase-1-20260612-170437-review-request.md"
      ]
    },
    {
      "phase": 2,
      "started": "2026-06-12",
      "status": "complete",
      "description": "REPL + Stack + HP-style Programmable Language Skeleton inc1 (host complete)",
      "last_update": "2026-06-12",
      "notes": [
        "Phase 2 inc1 host: 30 tests green, Program first-class, C vm skel, Phase1 QA minors addressed",
        "APPROVED WITH MINORS by auditor; hardware smoke pending (Phase 0/1/2 backlog)",
        "Handoff generated: handoffs/phase-3-20260612-171627-review-request.md",
        "Handoff generated: handoffs/phase-3-20260612-201030-review-request.md"
      ]
    }
  ],
  "last_handoff": "handoffs/phase-3-20260612-201030-review-request.md",
  "notes": "Unattended Ralph Loop initialized. Git local repo active.; phase-1-inc1 handoff 20260612-163039; Phase 1 fix2: B/M fixes + minors; Phase 0 last_completed still -1 (HW verification pending human per m-6); complete-phase at 20260612-164414; phase-1-fix2 complete-phase handoff; complete-phase at 20260612-170437; Phase 2 inc1 approved (with minors addressed in Phase 3 inc1 hygiene); current_phase manually reconciled to 3 for Phase 3 start per M-3 spirit + user directive; complete-phase at 20260612-171627; complete-phase at 20260612-201030"
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

**Current inc1 status**: Host implementation + tests + docs complete. Added linspace(xmin,xmax,n) grid helper (used by cartesian_sample, exported, tested, 320-aware) as small verifiable data slice addition; all 10 tests green + cross tests. C skeleton + hybrid ready for UF2. Sampling reuses expr/hybrid faithfully (RPL feel for user fns). Awaiting hardware smoke + UF2 with plot module. Use ralph complete-phase.

**Phase 3 Success Criteria (overall phase, for later incs)**:
- Runnable on-device: plot a Cartesian expression or simple program from REPL or minimal UI, see points or (inc2+) pixels on 320x320.
- Multiple expressions overlay, viewport controls (xmin etc exposed and used in sampling).
- Polar and parametric supported via angle or (t) param sampling.
- C hot path: sampling loop or inner f-eval in C (picocalc_plot) for speed on dense 320+ samples.
- Fast raster or line draw into framebuffer (leverage or extend picocalcdisplay LUT).
- Interactive: trace, zoom, pan via QWERTY keys (mp/ui/graph or similar).
- Accuracy/performance notes: double sufficient; sample times recorded for typical fns.
- Host + on-device tests; docs + DECISIONS updated; git clean handoffs.

## Later Phases (High Level)
```

## 3. What Was Delivered (implementer claim)
phase-3-fix2: clean handoff after ralph automation fixes (msg capture, early helpers, phase-aware prompts, dirty detection, safety defaults)

Key files changed (since prior):
tools/ralph.sh

## 4. Git Activity
```
0aa009b phase-3-fix2: ralph.sh fixes (early current_phase/phase_cleared hoist before subcmd dispatch + complete-phase msg capture from args + improved dirty regex for unstaged mods + early PGR/CLAUDEQA defaults + phase-aware auditor handoff ls + AUDITOR var safety + auto-clean) — addresses every bash/permission-denied/command-not-found/syntax/truncation/unbound symptom from the claude_report.txt in QA rejection retry 2/3
80aae49 phase-3-inc1: Grok implementer work (auto-fallback commit)
152ab71 phase-3-inc1: add handoff artifact + LOOP_STATE awaiting_qa (ralph complete-phase)
fbc7341 phase-3-inc1: add linspace grid helper + tests + docs hygiene
28024b7 phase-3-inc1: add handoff artifact + LOOP_STATE awaiting_qa (ralph complete-phase)
f63e3ad phase-3-inc1: plot data skel + C module + prior QA hygiene + phase3 docs/state
```

## 5. Next
After review: address any Blockers/Majors, then either re-run complete-phase for fixes or (on clearance) let automation/script advance phase.
