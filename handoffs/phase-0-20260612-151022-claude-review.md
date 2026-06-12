Now I have everything I need. Let me compose the formal QA review.

---

## Ralph Loop QA Review — Phase 0: Foundation & Scaffolding + Unattended Loop

**Reviewer**: Claude (following ClaudeQA.md)
**Handoff ID / Commit**: `ef61c4f` — `chore: rename to SuperCalc.OG (Original Grok) + Phase 0 foundation + unattended Ralph Loop`
**Date**: 2026-06-12
**Overall Assessment**: NEEDS WORK

---

### Summary

The foundation scaffolding is substantively solid — ARCHITECTURE.md, DECISIONS.md, HP_INSPIRATION.md, BRINGUP.md, INITIAL_STUBS.md, PGR.md, ClaudeQA.md, and `ralph_loop.py` are all present and well-written. The process tooling is well-designed and operational. However, the handoff was submitted prematurely: two of three Phase 0 success criteria are not yet met (no hardware confirmation, no hybrid C module proof-of-build), the working tree was not clean at handoff time (a process rule violation), and `src/` / `mp/` directory scaffolding is absent. These must be resolved before the phase can be marked complete.

---

### Phase Scope Fidelity

The work is correctly scoped to Phase 0 — no scope creep into Phase 1+ material observed. Documentation and tooling are what was promised.

**Deliverable status against PHASES.md checklist**:

| Deliverable | Status |
|---|---|
| Directory structure + git init | DONE |
| Core docs (README, ARCHITECTURE, PHASES, HP_INSPIRATION, DECISIONS, BRINGUP, INITIAL_STUBS) | DONE |
| PGR.md + ClaudeQA.md | DONE |
| `tools/ralph_loop.py` + LOOP_STATE.json | DONE |
| Base firmware decision + bring-up instructions finalized | PARTIAL — BRINGUP.md is written and makes a clear LofiFren recommendation, but user hardware confirmation is not recorded |
| First hardware smoke test + dashboard confirmation | NOT DONE |
| Minimal custom C module skeleton proven to build and callable from MPy | NOT DONE |

**Success Criteria**:

1. Automation script runs cleanly — **PARTIAL** (see Major Issue below re: dirty working tree)
2. User has confirmed base firmware + dashboard works on real hardware — **NOT MET**
3. First hybrid extension path demonstrated — **NOT MET** (only a textual code sketch in INITIAL_STUBS.md; no actual file in `src/`, no build invocation)

The handoff was called before the phase was ready. The three unchecked deliverables are explicitly required by PHASES.md.

---

### Correctness & Robustness

This phase contains no executable calculator code, so math accuracy, parser, and stack semantics are not yet in scope. No issues here for Phase 0 specifically.

**Blockers**: None (no calculator logic to be incorrect yet)

**Major Issues**:

- **Dirty working tree at handoff time** — The git status at handoff shows `tools/ralph_loop.py` as modified and unstaged (` M tools/ralph_loop.py`), meaning the working tree was not clean when `complete-phase` was invoked. PGR.md rule 3 states the tree must be clean before calling the automation. The script enforces this with an explicit guard that exits with an error unless `--force` is passed. If `--force` was used, that is a process rule violation. If the script failed to catch it, that is a bug in the guard logic. Either way this must be resolved — the handoff should represent a clean, reproducible snapshot. The uncommitted changes to `ralph_loop.py` must be committed or explained.

- **No `src/` or `mp/` directory structure** — ARCHITECTURE.md describes `src/math/`, `src/plot/`, `src/core/`, `mp/ui/`, `mp/lang/`, `mp/apps/`, `mp/lib/` as the project layout. None of these directories exist in the repo. For a "Foundation & Scaffolding" phase, having at least the skeleton directory structure (even with placeholder `.gitkeep` files) is necessary so Phase 1 has a defined home to land code and the hybrid boundary is concrete rather than conceptual. INITIAL_STUBS.md describes what `picocalc_math.c` and `micropython.cmake` should look like, but these actual files are absent.

**Minor / Observations**:

- INITIAL_STUBS.md uses `STATIC` keyword in C code stubs. This was the MicroPython-style `#define STATIC static` convention but newer MicroPython versions have moved toward plain `static`. Not an issue now (Phase 0 stubs are illustrative), but worth using the current idiom in Phase 1 real code.

---

### Architecture & Hybrid Design

**Positive**: The documented architecture is well-reasoned. The layered diagram, the thin-boundary principle, the decision to put hot paths (sampling, VM dispatch, numerics) in C while leaving UI and parsers in MicroPython, and the PSRAM + memory discipline notes are all correct and well-grounded in the hardware reality.

**Major Issues**:

- **Hybrid proof path is undemonstrated** — INITIAL_STUBS.md is a sketch document, not working code. A `src/` directory with an actual (even trivial) `picocalc_math.c`, `micropython.cmake`, and a matching `mp/lib/hybrid.py` that imports it (with graceful fallback) would prove the extension path is real and set the exact pattern for Phase 1. Right now the architecture is aspirational only. One concrete "hello from C" module that builds is the agreed gate criterion.

- **Build system path not locked** — BRINGUP.md correctly identifies the Docker-based `USER_C_MODULES` pattern from LofiFren/zenodante as the build approach, but there is no `tools/build_supercalc.sh` (or equivalent) that concretely invokes it. This means Phase 1 would start without a proven build path. This should be a deliverable of Phase 0's hybrid proof.

**Minor**:

- ARCHITECTURE.md mentions eigenmath as "highly desirable" and ulab as base firmware. DECISIONS.md should record whether eigenmath is confirmed present in the chosen LofiFren UF2 or whether we need a custom build from zenodante. This open question needs to be resolved before Phase 1 starts.

---

### HP Programmable Spirit

Phase 0 is pure foundation — no language or stack work in scope. However, `HP_INSPIRATION.md` is excellent. It correctly identifies the HP-48/RPL lineage as the gold standard and articulates the specific features to inherit (local variables, first-class programs, `DO...UNTIL`, `FOR...NEXT`, soft menus, `LASTx`). The separation between "pro RPL mode" and "friendly algebraic entry" is the right call. The decision to use a C VM for the language runtime is well-motivated.

No issues for Phase 0. Flag for Phase 2: when the custom language syntax is being designed, HP_INSPIRATION.md's description of `<< ... >>` + `->` locals should be treated as the reference, not just general inspiration.

---

### Performance & Resources

No code to benchmark. The documented memory strategy (C for hot loops, PSRAM for large buffers, framebuffer discipline) is sound. One observation: ARCHITECTURE.md notes "520 KB" of RAM — confirm this is the RP2350's 520 KB SRAM (not inclusive of the 8 MB PSRAM). The two pools have very different access latency and the distinction matters for the math kernel and VM design. DECISIONS.md should record the precise memory map expected.

---

### Testing & Hardware Verification

**No hardware verification has occurred.** The Phase 0 success criteria explicitly require:
- User confirmation that the base firmware (LofiFren UF2) flashes and boots on the real PicoCalc + Pico 2 W.
- Dashboard works.

This is a **human step** that cannot be automated, but it must happen before this phase is declared complete. Without it, we have no evidence the chosen firmware base even runs on the actual target device.

BRINGUP.md is well-written and gives clear step-by-step instructions. It ends with a direct prompt to the user: *"When you're at a computer with the device, run through the flashing steps..."* — that loop has not been closed.

---

### Documentation & Process

**Positive**: The documentation quality is high across the board. DECISIONS.md captures the key architectural choices with solid rationale. ARCHITECTURE.md is clear and the layered diagram is accurate. HP_INSPIRATION.md provides real design guidance, not just vague inspiration. PGR.md and ClaudeQA.md together form a functioning process framework.

**Major Issues**:

- **Process rule violated — dirty tree at handoff** (see Correctness section above). PGR.md section 3 is explicit: git working tree must be clean before calling `complete-phase`. This was not satisfied. The implementer must commit (or discard) the outstanding `tools/ralph_loop.py` changes and explain what they were.

**Minor**:

- `ralph_loop.py` has a `list-handoffs` command referenced in PGR.md but it is not implemented in the current script (no `cmd_list_handoffs` function, no `list-handoffs` subparser). This is a small but real discrepancy between docs and implementation.

- PHASES.md header says "Current Phase (per LOOP_STATE.json): 0 — Foundation & Unattended Loop Setup" but the LOOP_STATE.json itself has `"description": "Foundation & Scaffolding + Unattended Loop setup"`. Minor naming inconsistency; pick one and be consistent across files.

- The handoff file itself is truncated in two places (`PGR.md` and `ClaudeQA.md` sections are cut at `max_chars`). For Phase 0 this is acceptable — the full files are readable on disk — but consider whether 6000/4000 char limits will be adequate as docs grow.

---

### Risks & Technical Debt

1. **Build system not validated** — The biggest risk for Phase 1 is discovering the Docker-based `USER_C_MODULES` build is harder to set up than expected (e.g., LofiFren vs. zenodante differences, RP2350 toolchain quirks). Phase 0 should close this risk with a proved build.

2. **LofiFren vs. zenodante not fully resolved** — DECISIONS.md says "Build on LofiFren + zenodante foundations" but these are distinct repos with somewhat different module layouts. The exact choice (one vs. the other vs. a fork) needs to be locked before Phase 1, because the `USER_C_MODULES` cmake paths and frozen module names differ.

3. **`call_local_claude` flag correctness** — `ralph_loop.py:335` uses `["claude", "--print", "--no-session-persistence"]`. The flag `--no-session-persistence` may not be a valid flag for the local `claude` CLI. This should be verified by running `claude --help` to confirm the exact flags. If it's wrong, the unattended review invocation will silently fail.

4. **No `.gitignore` verification** — A `.gitignore` is present but its contents weren't reviewed. Confirm it excludes `.DS_Store` (one is already in the tree — it appears in the file listing), `__pycache__`, `*.pyc`, and any future build artifacts.

---

### Recommendations & Specific Action Items for Implementer

**Must fix before next handoff (same Phase 0):**

1. **Resolve the dirty `ralph_loop.py`** — Commit or discard the outstanding working tree change to `tools/ralph_loop.py`. Do not use `--force` for the next handoff. Explain in the commit message what changed and why it wasn't committed before the handoff.

2. **Create the skeleton directory structure** — Add `src/math/`, `src/plot/`, `src/core/`, `mp/ui/`, `mp/lang/`, `mp/apps/`, `mp/lib/` with `.gitkeep` files so the hybrid architecture is concrete in the repo, not just in a diagram.

3. **Create the minimal hybrid proof files** — Per INITIAL_STUBS.md, create the actual files: `src/math/picocalc_math.c` (trivial — even just a version constant function), `src/math/micropython.cmake`, and `mp/lib/hybrid.py` with the graceful fallback pattern. These don't need to be built yet, but the files must exist and be correct enough to build in Phase 1 with minimal changes.

4. **Add `tools/build_supercalc.sh` (skeleton)** — A stub script that shows exactly which Docker invocation / cmake command will build the UF2 with our modules. Even if it's a `# TODO: fill in Docker command` with the flags structure, it makes the build path concrete.

5. **Implement the `list-handoffs` subcommand** — It is documented in PGR.md and the `--help` text references it. Implement or remove the reference.

6. **Perform (or obtain) hardware bring-up confirmation** — Flash the LofiFren UF2 onto the real PicoCalc + Pico 2 W. Confirm: boots, dashboard connects, REPL works, display shows output. Record the result via `python tools/ralph_loop.py record-hardware-verification "..."`. This is a human step but it is a Phase 0 gate.

**Should fix soon (can be in same handoff or noted in DECISIONS.md):**

7. **Clarify LofiFren vs. zenodante** — Decide and record in DECISIONS.md which base repo is the primary build foundation and why. Note if eigenmath is present in the chosen prebuilt UF2 or requires a custom build.

8. **Verify `--no-session-persistence` flag** — Confirm `claude --help` lists this flag. If not, correct `ralph_loop.py:335` to use the valid flags for non-interactive invocation.

9. **Remove `.DS_Store` from repo** — Add `**/.DS_Store` to `.gitignore` and remove the file already committed (or at least add the gitignore rule to prevent future ones).

---

### Final Verdict

**Return for fixes before re-handoff.** The foundation documentation is genuinely good and the process tooling is functional. But Phase 0 has three stated success criteria, two of which are unmet (hardware bring-up not confirmed, hybrid extension path not demonstrated), and the handoff itself violated the clean-tree process rule. The phase cannot be marked complete until:

- The dirty `ralph_loop.py` is committed cleanly.
- The `src/` and `mp/` directory skeletons exist in the repo.
- The minimal hybrid proof files (`picocalc_math.c` stub + `micropython.cmake` + `hybrid.py`) are present.
- Hardware bring-up confirmation is recorded (human step — flash + dashboard confirmation).

Once those four items are addressed and committed cleanly, re-run `complete-phase` and this increment should be approvable as Phase 0 complete.