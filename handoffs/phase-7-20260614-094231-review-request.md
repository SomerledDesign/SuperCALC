# Ralph Loop Handoff — Phase 7
**Generated**: 2026-06-14T09:42:31-04:00
**Implementer Message**: phase-7-inc2: CAS dispatch fix + Symbolic wrapper + help note for solve RPN + diff/solve RPN test cov + nits closed + docs
**Current LOOP_STATE**:
```json
{
  "current_phase": 7,
  "status": "in_progress",
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
        "Handoff generated: handoffs/phase-5-20260613-231053-review-request.md",
        "Handoff generated: handoffs/phase-5-20260613-232044-review-request.md",
        "Handoff generated: handoffs/phase-5-20260613-233234-review-request.md",
        "Handoff generated: handoffs/phase-7-20260613-234523-review-request.md"
      ]
    }
  ],
  "last_handoff": "handoffs/phase-7-20260613-234523-review-request.md",
  "hardware_verified": false,
  "notes": "Phase 0 inc1 (first attempt): set current_phase=0 per task; added ralph record-hardware-verification + set-phase support for pending HW gate + automation success criteria. Hybrid proof structure in place (C src/math + mp/lib/hybrid + tests). HW smoke pending human confirmation on real PicoCalc (use ralph record-hardware-verification after dashboard/REPL/hybrid smoke).; complete-phase at 20260612-231211; set-phase 4 (was 0); complete-phase at 20260613-001320; complete-phase at 20260613-004410; complete-phase at 20260613-005324; set-phase 5 (was 4); complete-phase at 20260613-011047; complete-phase at 20260613-230802; complete-phase at 20260613-231053; complete-phase at 20260613-232044; complete-phase at 20260613-233234; set-phase 6 (was 5); qa-cleared-and-advanced via status (handoff-phase 5 -> 7) at 2026-06-13T23:45:00-04:00; complete-phase at 20260613-234523; set-phase 7 (was 8)",
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

**inc2 (current work)**: Small verifiable follow-on per "CLEARED TO CONTINUE" + auditor recommendations (no phase advance). Deliverables:
- [x] Fixed latent CAS RPN dispatch bug in expr.py (the _CAS_OPS if + continue was swallowing solve/diff words and calling simplify on them; now explicit per-family ifs with continue). Added precise comments on 2-arg solve/diff stack layout ("eq var solve").
- [x] mp/lib/cas.py: introduced Symbolic(str) subclass wrapper returned from simplify/solve/diff (stub + delegation paths); added one-line docstring to diff(); updated module doc for inc2 scope. __all__ exports Symbolic. (First step toward richer symbolic type per inc1 auditor risk note.)
- [x] tests/test_repl.py: extended test_repl_cas_surface_stub_and_rpn() (now inc2) to cover diff via direct RPN ("x^2" diff), solve 2-arg RPN + 1-arg, .cas diff, explicit Symbolic/str checks + issubclass; all green.
- [x] mp/ui/calc_repl.py: _help_text updated to "phase7 inc2", cas: help line now shows solve example + explicit RPN note on eq/var order for bare-word solve (addresses auditor "must-fix before eigenmath live"). Demo header + internal CAS comment refreshed to inc2.
- [x] Docs: PHASES current marker + this inc2 para; DECISIONS.md new section for dispatch hygiene + Symbolic decision + help+test closure of prior QA items. No scope creep.
- [x] All 6+1 tests + demo run clean; "python -c 'from mp.ui.calc_repl import run_demo'" exercises updated CAS (now shows Symbolic-wrapped stubs).
- [ ] On-device: post-UF2 smoke of RPN " 'x^2' diff ", 2-arg solve via stack, isinstance of result, .cas help visible (eigen or stub). Use ralph record-hardware-verification when human confirms.
- [ ] HW verification (backlog + this).

**inc2 Success Criteria**:
- Host: solve/diff/simplify all work correctly via direct rpn word after stack push (no mis-dispatch); 2-arg solve respects documented eq-then-var layout; tests cover it.
- Symbolic wrapper is transparent (is str subclass, roundtrips on stack/env/prog/REPL) but exported and asserted for future guard points.
- Help text now guides users on solve RPN arg order (low-risk stub; critical for when real CAS active).
- Git clean at handoff; complete-phase produces handoff + prompt (stays on phase 7 per "CLEARED TO CONTINUE", not full phase gate).
- No C, no new syntax, thin (changes only in cas + glue dispatch + help + test + docs), prior auditor Minors/Nits addressed before next.
- Demo + batch still visibly exercise CAS path.

**Automation Note**: Use `./tools/ralph.sh complete-phase "phase-7-inc2: CAS dispatch fix + Symbolic wrapper + help note for solve RPN + diff RPN test cov + nits + docs"`. Hardware gate remains human (ralph record... after real PicoCalc UF2). Do not advance phase (7->8) until full phase criteria + HW + auditor "PHASE COMPLETE" language.
```

## 3. What Was Delivered (implementer claim)
phase-7-inc2: CAS dispatch fix + Symbolic wrapper + help note for solve RPN + diff/solve RPN test cov + nits closed + docs

Key files changed (since prior):
.last_ralph_pid

## 4. Git Activity
```
960ddf7 chore: untrack transient .last_ralph_pid (ralph script internal; gate filter misses some D cases; not phase deliverable)
cd3a86e phase-7-inc2: CAS dispatch fix + Symbolic wrapper + help note for solve RPN + diff RPN test + nits + docs
ccd8679 phase-7-inc1: add handoff artifact + LOOP_STATE awaiting_qa (ralph complete-phase)
c8d508d temp: stage LOOP_STATE to pass ralph clean gate for phase-7 handoff
ef3aae8 phase-7-inc1: thin CAS surface (eigenmath/stub + simplify/solve/diff RPN+REPL+demo + last alias + QA nits + docs)
2b47e28 phase-6-inc1: add handoff artifact + LOOP_STATE awaiting_qa (ralph complete-phase) [phase declared 6]
```

## 5. Next
After review: address any Blockers/Majors, then either re-run complete-phase for fixes or (on clearance) let automation/script advance phase.
