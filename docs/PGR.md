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
- Run `./tools/ralph.sh docs/PGR.md docs/ClaudeQA.md <start_phase> <end_phase>` (or just `./tools/ralph.sh` to use defaults).
- The bash script handles status, phase advancement, and the full Grok → commit → Claude QA loop automatically.
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
# The loop is driven by the bash script (see usage above). After Grok's work is committed, it automatically invokes the local claude CLI with ClaudeQA.md for the audit.
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
- The script checks the Claude report for clearance language ("CLEARED TO CONTINUE", "PHASE COMPLETE - CLEARED TO ADVANCE", etc.) and advances automatically.

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
./tools/ralph.sh --help  (or just run it to see usage)
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
- Final "phase truly approved" override.
- Deciding whether to accept Claude's "needs work" vs. proceeding.
- Any scope changes that affect multiple phases.

## Forbidden Behaviors

- Declaring a phase done without running the `complete-phase` automation.
- Implementing future-phase features without recording a decision.
- Handing messy, uncommitted, or undocumented work to Claude.
- Ignoring Claude's Blockers (you must address them before the next handoff or get explicit human override).

## Spirit

This is a **definitive** build. The loop exists to produce high-quality, reviewable, shippable increments with clear accountability. Move deliberately, verify on hardware, respect the HP programmable legacy while using the PicoCalc's real strengths (square screen, backlit QWERTY, PSRAM, Pico 2 W power).

**You are the engine. Claude is the independent conscience. The human is the final arbiter and hardware operator.**

Follow this guide strictly for an unattended, high-trust loop.
