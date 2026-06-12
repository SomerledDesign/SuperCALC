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
- Automation script runs cleanly (`status`, `complete-phase` demo).  [x] status + help now functional; ralph.sh supports PGR workflow.
- User has confirmed base firmware + dashboard works on real hardware. [ ] pending human verification
- First hybrid extension path demonstrated. [x] C module with float math + sin/sqrt, thin MPy wrapper, host test harness exercising fallback, full dir skeleton with .gitkeeps, build wrapper updated. (C path verified on-device by human after flash.)

**Current Status**: Phase 0 foundation + hybrid proof substantially complete in code + tooling. Automation improved. Dirs concrete. Awaiting hardware smoke (import picocalc_math + run hybrid smoke on real PicoCalc + Pico 2 W). See handoff for details.

## Phase 1 — Core Math Engine & Expression System

(See full details in earlier version of this file or ARCHITECTURE.md. Goals remain: hybrid numeric + symbolic hooks, infix + RPN parsers, C kernel for speed/accuracy, basic evaluator, stack + variables.)

**Automation Note**: When work on Phase 1 increments is ready, use `complete-phase` to hand off to Claude. Do not advance to Phase 2 until this phase gate is cleared.

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

**Current Phase (per LOOP_STATE.json)**: 0 — Foundation & Unattended Loop Setup

Update this file's phase sections and status when the automation indicates a gate has been passed.
