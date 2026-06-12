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
- User has confirmed base firmware + dashboard works on real hardware. [ ] pending human verification
- First hybrid extension path demonstrated. [x] C module with float math + sin/sqrt (Phase 0), extended in Phase 1 inc1.

**Current Status**: Phase 0 foundation complete in code/tooling. complete-phase + clearance logic fixed. Automation now matches PGR expectations. Awaiting hardware smoke on real PicoCalc. Phase 1 inc1 work has begun (see below). See handoffs/ and claude_report for history.

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

**Current inc1 status**: Host-complete, C+MPy glue + parsers + tests in place. Awaiting hardware confirmation + auditor review. See commit phase-1-inc1.

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

**Current Phase (per LOOP_STATE.json)**: 1 — Core Math Engine & Expression System (inc1 in progress)

Update this file's phase sections and status when the automation indicates a gate has been passed. (Phase 0 automation now passes with complete-phase; hardware + final clearance pending.)
