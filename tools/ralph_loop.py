#!/usr/bin/env python3
"""
ralph_loop.py — Unattended Ralph Loop Automation Tool

This script manages the phase state, enforces process discipline,
generates self-contained handoff packages, and invokes the **local Claude**
(claude CLI / Claude Code installed on this computer) as the independent QA reviewer.

Usage examples:
  python tools/ralph_loop.py status
  python tools/ralph_loop.py set-phase 1
  python tools/ralph_loop.py complete-phase --message "Phase 1 core: hybrid math + parsers"
  python tools/ralph_loop.py generate-handoff 1
  python tools/ralph_loop.py record-hardware-verification "Graphing of 3 functions with trace works on real hardware"

Run from the SuperCalc.OG project root.

When complete-phase runs, it will:
- Generate the rich handoff file (with full PGR + ClaudeQA embedded)
- Automatically call your local `claude` CLI (non-interactively via --print)
- Capture the real independent Claude review and save it
- Update LOOP_STATE

Use --no-local-claude to skip the auto-invocation if needed.
"""

import argparse
import json
import subprocess
import sys
import datetime
from pathlib import Path
from textwrap import dedent

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
STATE_FILE = PROJECT_ROOT / "docs" / "LOOP_STATE.json"
HANDOFF_DIR = PROJECT_ROOT / "handoffs"
PGR_FILE = PROJECT_ROOT / "docs" / "PGR.md"
CLAUDEQA_FILE = PROJECT_ROOT / "docs" / "ClaudeQA.md"
PHASES_FILE = PROJECT_ROOT / "docs" / "PHASES.md"
DECISIONS_FILE = PROJECT_ROOT / "docs" / "DECISIONS.md"

def run_git(cmd: list[str]) -> str:
    """Run a git command and return stripped stdout. Raise on error."""
    result = subprocess.run(
        ["git"] + cmd,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()

def get_git_status_porcelain() -> str:
    try:
        return run_git(["status", "--porcelain"])
    except subprocess.CalledProcessError:
        return "ERROR: git status failed"

def get_recent_commits(n: int = 5) -> str:
    try:
        return run_git(["log", f"-{n}", "--oneline", "--decorate"])
    except Exception:
        return "(could not retrieve git log)"

def get_changed_files_since(ref: str = "HEAD~1") -> list[str]:
    try:
        out = run_git(["diff", "--name-only", ref])
        return [f.strip() for f in out.splitlines() if f.strip()]
    except Exception:
        return []

def load_state() -> dict:
    if not STATE_FILE.exists():
        return {
            "current_phase": 0,
            "status": "in_progress",
            "last_completed_phase": -1,
            "phase_history": [],
            "last_handoff": None,
            "notes": "Initialized by ralph_loop.py"
        }
    with open(STATE_FILE) as f:
        return json.load(f)

def save_state(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def load_text(path: Path, max_chars: int | None = None) -> str:
    if not path.exists():
        return f"[File not found: {path}]"
    text = path.read_text()
    if max_chars and len(text) > max_chars:
        return text[:max_chars] + "\n... [truncated for handoff size]"
    return text

def update_phase_history(state: dict, phase: int, status: str, note: str = ""):
    now = datetime.date.today().isoformat()
    for entry in state.get("phase_history", []):
        if entry.get("phase") == phase:
            entry["status"] = status
            entry["last_update"] = now
            if note:
                entry.setdefault("notes", []).append(note)
            return
    # New entry
    state.setdefault("phase_history", []).append({
        "phase": phase,
        "started": now,
        "status": status,
        "last_update": now,
        "notes": [note] if note else []
    })

def cmd_status(args):
    state = load_state()
    print("=== Ralph Loop Status ===")
    print(f"Current Phase : {state.get('current_phase')}")
    print(f"Status        : {state.get('status')}")
    print(f"Last Completed: {state.get('last_completed_phase')}")
    print(f"Last Handoff  : {state.get('last_handoff')}")
    print("\n--- Git Status ---")
    porcelain = get_git_status_porcelain()
    if porcelain:
        print(porcelain)
    else:
        print("Working tree clean")
    print("\n--- Recent Commits ---")
    print(get_recent_commits(6))
    print("\n--- Phase History (last 5) ---")
    for h in state.get("phase_history", [])[-5:]:
        print(f"  Phase {h.get('phase')}: {h.get('status')} (updated {h.get('last_update')})")

def cmd_set_phase(args):
    state = load_state()
    old = state.get("current_phase")
    new = args.phase
    state["current_phase"] = new
    state["status"] = "in_progress"
    update_phase_history(state, new, "in_progress", f"Manually set from phase {old}")
    save_state(state)
    print(f"Current phase set to {new}. Status: in_progress")
    print("Remember: use complete-phase when the work for this phase/increment is ready for QA.")

def cmd_complete_phase(args):
    state = load_state()
    current = state.get("current_phase", 0)

    # Git hygiene check
    porcelain = get_git_status_porcelain()
    if porcelain.strip() and not args.force:
        print("ERROR: Working tree is not clean. Commit or stash changes first, or use --force.")
        print(porcelain)
        sys.exit(1)

    # Build handoff
    handoff_path = create_handoff(state, current, args.message or f"Phase {current} increment complete")

    # Update state
    state["status"] = "awaiting_qa"
    state["last_handoff"] = str(handoff_path.relative_to(PROJECT_ROOT))
    update_phase_history(state, current, "awaiting_qa", f"Handoff generated: {handoff_path.name}")
    save_state(state)

    print(f"\n✅ Handoff generated: {handoff_path}")

    claude_prompt = build_claude_prompt(state, current, handoff_path, args.message)

    if args.no_local_claude:
        print("\n--no-local-claude specified. Skipping automatic call to local Claude.")
        print("\n--- NEXT STEPS ---")
        print("1. Commit the changes (suggested message below).")
        print("2. Manually feed the prompt + handoff file to your local claude CLI or claude.ai app.")
        msg = args.message or f"Phase {current}: increment complete - awaiting Claude QA"
        print(f'\nSuggested commit: git add -A && git commit -m "{msg}"')
        print("\n" + "="*70)
        print("READY PROMPT FOR CLAUDE (copy everything below the line)")
        print("="*70 + "\n")
        print(claude_prompt)
    else:
        print("\nInvoking local Claude (your installed claude CLI) for independent review...")
        print("This may take a moment while Claude reads the full handoff package and applies ClaudeQA.md rules.")
        claude_review = call_local_claude(claude_prompt)

        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        review_path = HANDOFF_DIR / f"phase-{current}-{timestamp}-claude-review.md"
        review_path.write_text(claude_review)

        print(f"\n✅ Independent review from local Claude saved to: {review_path}")
        print("\n" + "="*70)
        print("REVIEW FROM LOCAL CLAUDE (following ClaudeQA.md exactly)")
        print("="*70 + "\n")
        print(claude_review)
        print("\n" + "="*70)
        print("END OF CLAUDE REVIEW")
        print("="*70)

        print("\n--- NEXT STEPS ---")
        msg = args.message or f"Phase {current}: increment complete - awaiting Claude QA"
        print(f"1. Commit the changes: git add -A && git commit -m \"{msg}\"")
        print("2. Address any Blockers/Majors from the review above.")
        print("3. When ready for the next increment or re-review, run complete-phase again (or generate-handoff).")

def create_handoff(state: dict, phase: int, message: str) -> Path:
    HANDOFF_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"phase-{phase}-{timestamp}-review-request.md"
    handoff_path = HANDOFF_DIR / filename

    # Gather context
    pgr = load_text(PGR_FILE, max_chars=6000)
    claudeqa = load_text(CLAUDEQA_FILE, max_chars=4000)
    phases = load_text(PHASES_FILE, max_chars=5000)
    decisions = load_text(DECISIONS_FILE, max_chars=3000)

    git_log = get_recent_commits(8)
    changed = get_changed_files_since("HEAD~1") or get_changed_files_since("@{u}~1") or ["(first commit or no previous)"]
    porcelain = get_git_status_porcelain()

    content = dedent(f"""
    # Ralph Loop Handoff — Phase {phase}
    **Generated**: {datetime.datetime.now().isoformat()}
    **Implementer Message**: {message}
    **Current LOOP_STATE**:
    ```json
    {json.dumps({k: v for k, v in state.items() if k != 'phase_history'}, indent=2)}
    ```

    ## 1. Role Instructions

    **You are Claude acting strictly as the Independent QA Reviewer per `ClaudeQA.md`.**
    Read the full ClaudeQA.md below (included for self-containment).

    The implementer (Grok) has followed `PGR.md` and is handing off a completed increment for review.
    Do **not** write code. Produce a structured review using the exact format specified in ClaudeQA.md.

    ## 2. Phase Goals & Success Criteria
    (From PHASES.md — excerpt)
    ```
    {phases}
    ```

    ## 3. What the Implementer Claims Was Delivered
    {message}

    ## 4. Recent Git Activity & Changed Files
    ```
    {git_log}
    ```

    **Files changed in recent increment**:
    {chr(10).join("- " + f for f in changed[:30])}
    {"... (more files)" if len(changed) > 30 else ""}

    **Current git status porcelain**:
    ```
    {porcelain or "clean"}
    ```

    ## 5. Full PGR.md (Implementer Rules — for your context)
    ```
    {pgr}
    ```

    ## 6. Full ClaudeQA.md (Your Rules — Follow These Strictly)
    ```
    {claudeqa}
    ```

    ## 7. Key Project Docs (excerpts)
    **DECISIONS.md (recent)**:
    ```
    {decisions}
    ```

    ## 8. Additional Context from Implementer
    (Any extra notes would appear here. Hardware verification status should be noted by implementer.)

    ## 9. How to Respond
    Use the **exact output format** defined in ClaudeQA.md.

    After your review, the implementer will address issues and may generate a follow-up handoff for the same phase (fixes) or advance when approved.

    ---
    **End of Handoff Package**
    """).strip()

    handoff_path.write_text(content)
    return handoff_path

def build_claude_prompt(state: dict, phase: int, handoff_path: Path, message: str) -> str:
    """Return the exact text the implementer should paste to Claude."""
    return dedent(f"""
    You are now acting as the Independent QA Reviewer for the Unattended Ralph Loop on the SuperCalc.OG project.

    Please perform a full QA review of the latest increment for **Phase {phase}**.

    The complete handoff package (including PGR.md, ClaudeQA.md, phase goals, git summary, and context) has been written to:
    {handoff_path.relative_to(PROJECT_ROOT)}

    **Implementer summary of this increment**: {message or "See handoff file"}

    **Current state** (from LOOP_STATE.json):
    Current Phase: {state.get('current_phase')}
    Status: {state.get('status')}
    Last completed: {state.get('last_completed_phase')}

    **Instructions**:
    1. Read the handoff file at the path above in full.
    2. Follow *exactly* the rules and output format in the included ClaudeQA.md.
    3. Be rigorous on correctness, HP programmable spirit, hybrid architecture, accuracy, and hardware implications.
    4. Output using the precise structure specified (## Ralph Loop QA Review — Phase ... etc.).

    When you are finished, I will address any Blockers/Majors and produce a follow-up handoff if needed.

    Begin your review now.
    """).strip()

def cmd_generate_handoff(args):
    state = load_state()
    phase = args.phase or state.get("current_phase")
    path = create_handoff(state, phase, "Regenerated handoff (manual)")
    print(f"Handoff regenerated: {path}")

def call_local_claude(prompt: str) -> str:
    """Invoke the local claude CLI (Claude Code) non-interactively.
    
    Uses --print for one-shot response + --no-session-persistence for clean automation.
    The prompt should instruct Claude to read the generated handoff file (which contains
    full embedded copies of PGR.md, ClaudeQA.md, phase goals, git state, etc.).
    """
    try:
        result = subprocess.run(
            ["claude", "--print", "--no-session-persistence"],
            input=prompt,
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=180  # allow time for thoughtful review
        )
        if result.returncode != 0:
            err = result.stderr.strip() or "unknown error"
            return f"[ERROR from local claude CLI (exit {result.returncode})]\n{err}"
        return result.stdout.strip()
    except FileNotFoundError:
        return "[ERROR] 'claude' command not found in PATH. Is Claude Code installed?"
    except subprocess.TimeoutExpired:
        return "[ERROR] Local Claude review timed out."
    except Exception as e:
        return f"[ERROR invoking local claude CLI]: {e}"


def cmd_record_hardware(args):
    state = load_state()
    note = " ".join(args.note) if args.note else "Hardware verification recorded"
    update_phase_history(state, state.get("current_phase", 0), state.get("status", "in_progress"), f"[HARDWARE] {note}")
    save_state(state)
    print(f"Hardware verification note recorded: {note}")
    print("Include this in your next complete-phase or mention it explicitly in the handoff message.")

def main():
    parser = argparse.ArgumentParser(
        description="Unattended Ralph Loop automation for SuperCalc.OG"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # status
    p_status = sub.add_parser("status", help="Show current loop state and git info")
    p_status.set_defaults(func=cmd_status)

    # set-phase
    p_set = sub.add_parser("set-phase", help="Manually change the current phase (use sparingly)")
    p_set.add_argument("phase", type=int)
    p_set.set_defaults(func=cmd_set_phase)

    # complete-phase
    p_complete = sub.add_parser("complete-phase", help="Mark current work complete, generate handoff, invoke local Claude for independent QA review, update state")
    p_complete.add_argument("--message", "-m", type=str, default=None,
                            help="Short description of what was delivered in this increment")
    p_complete.add_argument("--force", action="store_true",
                            help="Proceed even if git tree is not clean")
    p_complete.add_argument("--no-local-claude", action="store_true",
                            help="Generate handoff + prompt but skip automatically calling the local claude CLI")
    p_complete.set_defaults(func=cmd_complete_phase)

    # generate-handoff (manual)
    p_handoff = sub.add_parser("generate-handoff", help="Regenerate a handoff package for a phase (without changing state)")
    p_handoff.add_argument("phase", type=int, nargs="?", default=None)
    p_handoff.set_defaults(func=cmd_generate_handoff)

    # record-hardware-verification
    p_hw = sub.add_parser("record-hardware-verification", help="Record that a feature/behavior was confirmed on real PicoCalc hardware")
    p_hw.add_argument("note", nargs="+", help="Description of what was verified on hardware")
    p_hw.set_defaults(func=cmd_record_hardware)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
