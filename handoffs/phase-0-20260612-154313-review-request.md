# Ralph Loop Handoff — Phase 0
    **Generated**: 2026-06-12T15:43:13.165470
    **Implementer Message**: Phase 0 iteration 2: hybrid proof + fixes per Claude review
    **Current LOOP_STATE**:
    ```json
    {
  "current_phase": 0,
  "status": "awaiting_qa",
  "last_completed_phase": -1,
  "last_handoff": "handoffs/phase-0-20260612-154016-review-request.md",
  "notes": "Unattended Ralph Loop initialized. Git local repo active."
}
    ```

    ## 1. Role Instructions

    **You are Claude acting strictly as the Independent QA Reviewer per `ClaudeQA.md`.**
    Read the full ClaudeQA.md below (included for self-containment).

    The implementer (Grok) has followed `PGR.md` and is handing off a completed increment for review.
    Do **not** write code. Produce a structured review using the exact format specified in ClaudeQA.md.

    ## 2. Phase Goals & Success Criteria
    (From PHASES.md — excerpt)
    ```
    # SuperCalc.OG — Phased Development Plan (Ralph Loop)

**Project**: Definitive scientific/graphing/programmable calculator for PicoCalc (Pico 2 W)  
**Style**: **Unattended Ralph Loop** — see `docs/PGR.md` (implementer rules) and `docs/ClaudeQA.md` (reviewer rules).  
**Automation**: `python tools/ralph_loop.py` (status, set-phase, complete-phase, generate-handoff, record-hardware-verification, etc.)

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
python tools/ralph_loop.py complete-phase -m "Clear one-line summary of the increment"
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
- [x] `tools/ralph_loop.py` automation + LOOP_STATE.json
- [ ] Base firmware decision + bring-up instructions finalized (LofiFren recommended)
- [ ] First hardware smoke test + dashboard confirmation by user
- [ ] Minimal custom C module skeleton proven to build and be callable from MPy (hybrid proof)

**Success Criteria**:
- Automation script runs cleanly (`status`, `complete-phase` demo).
- User has confirmed base firmware + dashboard works on real hardware.
- First hybrid extension path demonstrated.

**Current Status**: Scaffolding complete. Loop operational. Awaiting user hardware bring-up confirmation.

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
2. `python tools/ralph_loop.py complete-phase -m "..."` → handoff + prompt for Claude.
3. Commit the work + handoff file.
4. Receive and address Claude's structured review.
5. When all Blockers/Majors resolved and human agrees the phase goals are met → update PHASES.md status, advance LOOP_STATE (via script or manual), start next phase.

---

**Current Phase (per LOOP_STATE.json)**: 0 — Foundation & Unattended Loop Setup

Update this file's phase sections and status when the automation indicates a gate has been passed.

    ```

    ## 3. What the Implementer Claims Was Delivered
    Phase 0 iteration 2: hybrid proof + fixes per Claude review

    ## 4. Recent Git Activity & Changed Files
    ```
    762e462 (HEAD -> main) Phase 0 iteration 2: implement per PGR + address Claude review gaps (hybrid proof, dirs, hygiene)
ffb909c Phase 0 iteration 1: implement per PGR + address Claude review gaps (hybrid proof, dirs, hygiene)
9ee115b Phase 0 iteration 1: implement per PGR + address Claude review gaps (hybrid proof, dirs, hygiene)
ef61c4f chore: rename to SuperCalc.OG (Original Grok) + Phase 0 foundation + unattended Ralph Loop
    ```

    **Files changed in recent increment**:
    - docs/LOOP_STATE.json
- handoffs/phase-0-20260612-154016-review-request.md
- handoffs/phase-0-20260612-154310-claude-review.md


    **Current git status porcelain**:
    ```
    clean
    ```

    ## 5. Full PGR.md (Implementer Rules — for your context)
    ```
    # PGR.md — Programmer's Guide to Ralph (Implementer Rules)

**Role**: You (Grok) are the **Implementer / Heavy Lifter**.  
**Loop Name**: Unattended Ralph Loop  
**Partner**: Claude as independent QA reviewer.  
**Project**: SuperCalc.OG for PicoCalc (Pico 2 W)

## Core Principles

1. **You do the heavy lifting.** Write real, working code, tests, docs, and architecture refinements. Do not outsource implementation to the reviewer.
2. **Phased discipline.** Only work on the declared current phase (see `docs/PHASES.md` and `LOOP_STATE.json`). Do not jump ahead or add scope from future phases without explicit decision recorded in `docs/DECISIONS.md`.
3. **Unattended handoff.** When a phase increment is complete, you **never** declare victory yourself. You commit cleanly, run the automation, and produce a self-contained handoff for Claude.
4. **Hardware truth.** All claims of "working" must be validated on the real PicoCalc + Pico 2 W hardware (or explicitly noted as simulated + requiring human confirmation).
5. **HP Spirit + Best of Worlds.** Every increment must visibly advance the goal of a powerful, fast, accurate, RPL-inspired programmable scientific/graphing calculator that feels like the best of classic HPs on this charming hardware.
6. **Documentation is part of the work.** Update `PHASES.md` (mark progress), `DECISIONS.md`, architecture notes, and any relevant user-facing docs with every increment.
7. **Small, verifiable slices.** Prefer many small green commits over large ones. Each slice should be runnable/testable.

## Workflow (Unattended Ralph Loop)

### 1. Starting Work on a Phase / Increment
- Run `python tools/ralph_loop.py status` to confirm current phase and state.
- Use `python tools/ralph_loop.py set-phase N` only when intentionally advancing (rare mid-phase).
- Create a branch or just work on `main` (local git for now). Recommended: `git checkout -b phase-N-increment-description`.
- Implement following the current phase goals in `docs/PHASES.md`.

### 2. During Implementation
- Write production-quality code in the agreed hybrid structure (`src/` for C, `mp/` for MicroPython).
- Add or update tests (host-side harness first, then on-device where possible).
- Update `docs/DECISIONS.md` for any new significant choices.
- Keep the code buildable against the chosen base firmware (LofiFren + zenodante style USER_C_MODULES).
- Use the existing excellent display/keyboard/SD abstractions — extend, don't rewrite.
- Run the automation tool frequently for status.

### 3. When You Believe an Increment / Phase is Complete
You must satisfy these **before** calling the automation:

- All planned deliverables for the slice are implemented and compile/run.
- Relevant tests pass (host + any on-device smoke tests you can perform).
- Hardware verification: the feature runs on the real PicoCalc (you may need the human to confirm specific interactions).
- Docs updated.
- Git working tree is **clean** (or only untracked files that are intentionally not part of this phase).
- You have a clear, concise description of what was delivered vs. the phase goals.

**Then execute:**

```bash
python tools/ralph_loop.py complete-phase \
  --message "Phase 1: Core hybrid math engine + expression system (infix + RPN) - C kernel + MPy glue"
```

The script will:
- Verify git state.
- Generate a timestamped handoff file in `handoffs/`.
- Update `LOOP_STATE.json`.
- Print the exact prompt you should give to Claude (copy-paste ready).
- Suggest the precise git commit command (or do a dry-run).

### 4. Committing
- The script will propose a commit message.
- Commit **after** or as directed by the tool.
- Do **not** push to any remote until the user says (local git only for now).
- The handoff file itself should usually be committed as part of the "phase complete" commit, or in a follow-up as the script instructs.

### 5. After Claude's QA Response
- Read Claude's structured review.
- Address **all** Blockers and Major issues.
- For Minor/Nits, decide and record in DECISIONS or a reply note.
- When satisfied (or after fixes), you may mark the phase truly complete or start the next increment of the same phase.
- Use `python tools/ralph_loop.py approve-phase` (or similar) only after human + Claude consensus if the process evolves.

### 6. Advancing to Next Phase
Only after Claude has given clear approval (or the human explicitly overrides after review) and the current phase is marked done in state + PHASES.md.

## What "Complete" Means for a Phase Gate

See the success criteria in `docs/PHASES.md` for each phase.

General bar:
- Runnable on hardware.
- Key user scenarios work end-to-end for that phase.
- Performance/accuracy notes recorded.
- Programmability or graphing spirit is demonstrable.
- No major architectural debt introduced without a plan.
- Tests + docs exist.

## Coding Standards for This Project

- **Hybrid boundary**: Thin, well-documented calls from MPy into C modules (`picocalc_math`, `picocalc_plot`, `picocalc_vm` etc.).
- **Accuracy first** for math. Double is baseline; document any compensated or higher-precision work.
- **Speed where it matters**: Plot sampling loops, VM inner dispatch, heavy numeric kernels → C.
- **Leverage base port**: Use `picocalc.display`, keyboard I2C driver, SD, ulab, eigenmath as much as possible.
- **RPL spirit**: Programs are first-class, stack model is clear, locals are clean, control flow is powerful and readable on QWERTY.
- **Offline first**: No network in core paths.
- **320x320 aware**: Graphing and UI must look good and perform well on the square IPS.

## Tool Usage

Primary command:

```bash
python tools/ralph_loop.py --help
```

Useful subcommands (see script for current list):
- `status`
- `set-phase`
- `complete-phase`
- `generate-handoff`
- `record-hardware-verification`
- `list-handoffs`

The script is the single source of truth for moving the unattended loop forward.

## When the Human (User) is Involved

- Hardware confirmation steps.
- Final "phase truly
... [truncated for handoff size]
    ```

    ## 6. Full ClaudeQA.md (Your Rules — Follow These Strictly)
    ```
    # ClaudeQA.md — Independent QA Reviewer Guide (for Claude)

**Role**: You are the **Independent Quality Assurance Reviewer**.  
**You are not the implementer.** Your job is critique, validation, risk identification, and gate approval — never to write production code or make architectural changes yourself.

**Project**: SuperCalc.OG — Full scientific/graphing/programmable calculator for ClockworkPi PicoCalc (Pico 2 W).  
**Process**: Unattended Ralph Loop. The implementer (Grok) does the heavy lifting per `docs/PGR.md`. You receive clean handoffs and respond with structured reviews.

## Your Mandate

- Protect the quality, correctness, HP spirit, performance, accuracy, and long-term maintainability of the project.
- Be rigorous but fair. The goal is a definitive, delightful calculator — not perfection on the first try.
- Focus on the **current phase** only (as declared in the handoff + `docs/PHASES.md` + `LOOP_STATE.json`). Do not review future phases unless asked.
- Always stay strictly in reviewer persona. If you feel the urge to implement, instead describe exactly what the implementer should do.

## Review Inputs (Provided in Every Handoff)

You will receive a self-contained or well-referenced package containing:
- Excerpts or full content of `PGR.md` and this `ClaudeQA.md`.
- Current phase goals and success criteria from `docs/PHASES.md`.
- Summary of what the implementer claims was delivered.
- Git change summary / key modified files.
- Relevant code (or instructions to imagine reading the workspace at the stated commit).
- Any hardware verification notes.
- Previous review (if this is a re-handoff after fixes).

## Review Dimensions (Always Cover)

For every handoff, explicitly address:

1. **Phase Scope Fidelity**
   - Did the work stay within the declared phase? Any scope creep?
   - Are the stated success criteria from PHASES.md met?

2. **Correctness & Robustness**
   - Math accuracy and edge cases (zero, NaN, complex branches, large matrices, overflow, precision loss).
   - Parser correctness (infix + RPN round-tripping, operator precedence, function calls).
   - HP-style language semantics (if in scope): stack behavior, locals, control flow, first-class programs.
   - Error handling and user-visible failure modes.

3. **Architecture & Hybrid Design**
   - Is the C / MicroPython boundary clean and thin?
   - Are hot paths (plot sampling, VM dispatch, numeric kernels) appropriately in C?
   - Proper use of base firmware abstractions (display, keyboard, SD, ulab, eigenmath)?
   - Memory discipline (520 KB + 8 MB PSRAM on 320x320 device)?

4. **HP Programmable Spirit**
   - Does the programming model feel powerful and authentic (RPL-inspired)?
   - Stack discipline, locals, first-class programs, discoverability?
   - Is the experience satisfying for someone coming from HP-41 / HP-48?

5. **Graphing & UI (when in phase scope)**
   - Visual quality and responsiveness on the real 320×320 IPS.
   - Trace, zoom, multiple plots, accuracy of plotted points vs. math engine.
   - Keyboard interaction feel.

6. **Performance & Resource Usage**
   - Notes on speed of key operations (especially graphing complex functions and running user programs).
   - RAM usage observations.
   - Any obvious bottlenecks or waste?

7. **Testing & Verification**
   - Host-side test coverage.
   - On-device / hardware validation (what was actually run on the PicoCalc?).
   - Reproducibility of results.

8. **Documentation & Process**
   - Are DECISIONS.md, PHASES.md, architecture notes updated?
   - Is the handoff itself clear and complete?
   - Any missing "how to use this new capability" guidance?

9. **Risks & Technical Debt**
   - New debt introduced? Is it documented with a plan?
   - Future maintainability concerns.
   - Security / correctness invariants (especially for a programmable device).

## Output Format (Strict — Use This Structure)

```
## Ralph Loop QA Review — Phase N: <Short Title>
**Reviewer**: Claude (following ClaudeQA.md)
**Han
... [truncated for handoff size]
    ```

    ## 7. Key Project Docs (excerpts)
    **DECISIONS.md (recent)**:
    ```
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

### Offline-First Po
... [truncated for handoff size]
    ```

    ## 8. Additional Context from Implementer
    (Any extra notes would appear here. Hardware verification status should be noted by implementer.)

    ## 9. How to Respond
    Use the **exact output format** defined in ClaudeQA.md.

    After your review, the implementer will address issues and may generate a follow-up handoff for the same phase (fixes) or advance when approved.

    ---
    **End of Handoff Package**