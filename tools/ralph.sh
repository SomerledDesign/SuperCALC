#!/usr/bin/env bash
# ralph.sh — SuperCalc.OG autonomous Ralph Loop (Grok + Claude)
# Grok (via local grok CLI, guided by PGR.md) builds → commits
# Local Claude (guided by ClaudeQA.md) does independent QA and writes report
# Report feeds back to next Grok prompt. Rinse and repeat until complete.
#
# Usage: ./ralph.sh [pgr_file] [claudeqa_file] [start_phase] [end_phase]
#   pgr_file:     path to PGR.md (default: docs/PGR.md)
#   claudeqa_file: path to ClaudeQA.md (default: docs/ClaudeQA.md)
#   start_phase:  default 0
#   end_phase:    default 7
#
# The script must be run from (or will cd to) the SuperCalc.OG project root.
# It uses your installed Grok CLI (from curl -fsSL https://x.ai/cli/install.sh | bash)
# for the implementer role and your installed claude CLI for the auditor role.
#
# Fully automated like your old Codex + Claude version, but with Grok for the PGR-driven building.

set -euo pipefail

# ── resolve sandbox (project root) ──────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

echo "[ralph] Sandbox: $PROJECT_DIR"

# Unconditional safe defaults (so complete-phase / status when invoked as $1 never
# see unbound for these when printing instructions or doing fallbacks).
PGR_FILE="docs/PGR.md"
CLAUDEQA_FILE="docs/ClaudeQA.md"
START_PHASE="0"
END_PHASE="7"

# ── colors (hoisted so subcommands like complete-phase can use ok/fail early) ─────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

log()  { echo -e "${CYAN}[ralph]${RESET} $*"; }

# Auditor config for full-loop (ralph.sh 0 7 etc). complete-phase path is the primary for
# PGR "implementer does work then hands off". These prevent unbound var under set -u and
# make logs + error msgs sensible. Support optional -a / env for custom auditor binary
# (e.g. different claude model or codex wrapper) without breaking existing calls.
AUDITOR="${AUDITOR:-claude}"
AUDITOR_BIN="${AUDITOR_BIN:-${AUDITOR}}"
AUDITOR_FLAGS="${AUDITOR_FLAGS:---dangerously-skip-permissions}"
ok()   { echo -e "${GREEN}[ralph]${RESET} $*"; }
warn() { echo -e "${YELLOW}[ralph]${RESET} $*"; }
fail() { echo -e "${RED}[ralph]${RESET} $*"; }

# ── helpers hoisted VERY early (before any handle_subcommand or early intercept) ──
# This fixes the "current_phase: command not found" / "LOOP_STATE.json: command not found"
# class of errors when complete-phase is the first arg (the main root cause behind
# the permission-denied / cmd-not-found / syntax errors in the provided claude_report.txt).
current_phase() {
  if [[ -f docs/LOOP_STATE.json ]]; then
    python3 -c '
import json
try:
    data = json.load(open("docs/LOOP_STATE.json"))
    print(int(data.get("current_phase", 0)))
except:
    print(0)
' 2>/dev/null || echo 0
  else
    echo 0
  fi
}

phase_cleared() {
  # Strict clearance signals only. "APPROVED" was removed because it appears in
  # "APPROVED WITH MINORS" reviews that still end with "NEEDS WORK - DO NOT ADVANCE".
  # This prevents false-positive phase advancement.
  grep -qiE "CLEARED TO CONTINUE|PHASE COMPLETE - CLEARED TO ADVANCE|CLEARED TO ADVANCE" claude_report.txt 2>/dev/null
}

# ── robust subcommand detection (supports `./ralph.sh complete-phase "msg"` cleanly) ──
# Must be early so complete-phase/status can be used before PGR/CLAUDEQA defaults.
# We detect subcmd on $1, shift, then call handle which receives remaining args for msg etc.
handle_subcommand() {
  local cmd="$1"; shift || true
  case "$cmd" in
    status|--status)
      echo "════════════════════════════════════════════════════════"
      echo "  ralph.sh status — SuperCalc.OG Ralph Loop"
      echo "════════════════════════════════════════════════════════"
      python3 - <<'PYEOF' 2>/dev/null || echo "(status python helper failed)"
import json, os, subprocess
try:
    with open("docs/LOOP_STATE.json") as f:
        data = json.load(f)
except Exception:
    data = {"current_phase": 0, "status": "unknown"}
phase = int(data.get("current_phase", 0))
print("Current phase:", phase)
st = data.get("status", "?")
print("Status:", st)
last = data.get("last_handoff", "-")
print("Last handoff:", last)
print()
try:
    out = subprocess.check_output(["git","status","--porcelain"], text=True, stderr=subprocess.DEVNULL)
    lines = [l for l in out.strip().split("\n") if l.strip()]
    # Filter transient claude_report.txt (the "auditor report" file) and handoffs to match
    # complete-phase dirty logic. Prevents "Git dirty files: 1 M claude_report.txt" noise
    # in status (was visible in prior retry failure logs) while still warning on real mods.
    filtered = [l for l in lines if 'claude_report.txt' not in l]
    print("Git dirty files:", len(filtered), ("(+ claude_report.txt transient ignored)" if any('claude_report' in l for l in lines) else ""))
    for l in filtered[:5]:
        print("  ", l)
except Exception:
    print("Git: n/a")
print()
if os.path.isdir("handoffs"):
    hs = sorted([h for h in os.listdir("handoffs") if h.endswith(".md")])[-3:]
    print("Recent handoffs:", hs)
print("Run example: ./tools/ralph.sh docs/PGR.md docs/ClaudeQA.md 0 0")
print("HW record (Phase 0): ./tools/ralph.sh record-hardware-verification \"PicoCalc dashboard + REPL smoke OK\"")
PYEOF
      echo "Active auditor: $AUDITOR (bin: $AUDITOR_BIN , flags: $AUDITOR_FLAGS)"
      echo "════════════════════════════════════════════════════════"
      # Show HW verification status (Phase 0 gate) if present
      python3 - <<'PYEOF' 2>/dev/null || true
import json
try:
    with open("docs/LOOP_STATE.json") as f: data = json.load(f)
    if data.get("hardware_verified"):
        print("Hardware verified: YES -", data.get("hardware_note", "(no note)"))
    else:
        print("Hardware verified: NO (pending real PicoCalc smoke; use record-hardware-verification after human confirm)")
    print("Last completed phase:", data.get("last_completed_phase", -1))
except: pass
PYEOF
      # Auditor report visibility (so `ralph.sh status` shows clearance / rate limit state at a glance;
      # addresses the prior issue where report content was invisible from status and could be wiped).
      echo
      if [[ -f claude_report.txt ]]; then
        size=$(wc -c < claude_report.txt 2>/dev/null | tr -d ' ' || echo 0)
        echo "Auditor report present: ${size} bytes"
        echo "Last lines:"
        tail -5 claude_report.txt 2>/dev/null | sed 's/^/  /' || true
        if grep -qiE 'CLEARED TO CONTINUE|PHASE COMPLETE - CLEARED TO ADVANCE|CLEARED TO ADVANCE' claude_report.txt 2>/dev/null; then
          echo "  Clearance: YES (CLEARED TO ... present)"
        elif grep -qiE 'NEEDS WORK - DO NOT ADVANCE' claude_report.txt 2>/dev/null; then
          echo "  Clearance: NO (NEEDS WORK)"
        fi
        if grep -qiE "You've hit your limit|resets|rate limit|limit will reset" claude_report.txt 2>/dev/null; then
          echo "  (rate limit / reset message present in report)"
        fi
      else
        echo "Auditor report: (none on disk)"
      fi
      exit 0
      ;;
    set-phase)
      # Allow explicit phase set (per PGR: use only intentionally, rare mid-phase; supports starting fresh inc on declared phase)
      local newp="${1:-0}"
      if ! [[ "$newp" =~ ^[0-9]+$ ]]; then
        fail "set-phase requires numeric arg 0-7"
        exit 1
      fi
      RALPH_PHASE="${newp}" python3 - <<'PYEOF'
import json
import os
data = {}
try:
    with open("docs/LOOP_STATE.json") as f: data = json.load(f)
except: pass
old = data.get("current_phase", 0)
newp = int(os.environ.get("RALPH_PHASE", "0"))
data["current_phase"] = newp
data["status"] = "in_progress"
data.setdefault("notes", "")
data["notes"] = data.get("notes", "") + f"; set-phase {newp} (was {old})"
with open("docs/LOOP_STATE.json", "w") as f:
    json.dump(data, f, indent=2)
print("LOOP_STATE current_phase set to", newp)
PYEOF
      ok "Current phase set to ${newp}. (Follow PGR: only on declared phase; record in DECISIONS if significant.)"
      exit 0
      ;;
    record-hardware-verification)
      # Phase 0 critical: record human-performed smoke on real hardware (PicoCalc + Pico 2 W)
      # Per PGR + PHASES success: "User has confirmed base firmware + dashboard works on real hardware."
      # "Hardware verification: the feature runs on the real PicoCalc (you may need the human to confirm specific interactions)."
      # Call e.g.: ./tools/ralph.sh record-hardware-verification "Dashboard + REPL + import picocalc_math + hybrid.sin(0.5) OK on Pico 2 W unit"
      local note="${1:-Hardware smoke + dashboard confirmed on real PicoCalc (Pico 2 W)}"
      python3 - <<PYEOF
import json, datetime
data = {}
try:
    with open("docs/LOOP_STATE.json") as f: data = json.load(f)
except: pass
data["hardware_verified"] = True
data["hardware_note"] = """${note}"""
data["last_completed_phase"] = 0
data["status"] = "complete" if data.get("current_phase", 0) == 0 else data.get("status", "in_progress")
hist = data.setdefault("phase_history", [])
note_entry = "HW verified via record-hardware-verification: ${note}"
if not any(note_entry in str(h) for h in hist[-3:] if isinstance(h, dict)):
    for h in hist:
        if isinstance(h, dict) and h.get("phase") == 0:
            h.setdefault("notes", []).append(note_entry)
            h["status"] = "complete"
            break
data.setdefault("notes", "")
data["notes"] = data.get("notes", "") + "; HW verified at $(date -Iseconds): ${note}"
with open("docs/LOOP_STATE.json", "w") as f:
    json.dump(data, f, indent=2)
print("Hardware verification recorded. last_completed_phase=0 for Phase 0 gate.")
PYEOF
      ok "HW verification recorded: $note"
      echo "Re-run status to confirm. Use for Phase 0 clearance once human confirms on-device."
      exit 0
      ;;
    complete-phase)
      # Proper complete-phase per PGR.md + Phase 0 success criteria + auditor feedback (M-1).
      # - requires clean git (enforces "commit cleanly" before handoff)
      # - generates timestamped handoff/phase-N-...-review-request.md
      # - updates LOOP_STATE.json (status=awaiting_qa, last_handoff, history note)
      # - prints copy-paste ready prompt for local claude (per ClaudeQA.md)
      # Does NOT auto-run claude or the full loop; that is done by `ralph.sh <phases>` or human.
      # FIXED: now correctly captures user-provided description as ${msg} even when invoked
      # as first arg (previous versions lost it into CLAUDEQA_FILE or used subcmd name).
      local msg="${1:-phase inc complete}"
      echo "════════════════════════════════════════════════════════"
      echo "  ralph.sh complete-phase — generate handoff + await QA"
      echo "════════════════════════════════════════════════════════"

      # Best-effort clean of transient report so dirty check doesn't surprise on retry flows.
      git checkout -- claude_report.txt 2>/dev/null || rm -f claude_report.txt 2>/dev/null || true

      # 1. Git must be clean (or only untracked we intend to leave)
      # Note: porcelain " M path" (unstaged) vs "M  path" (staged); previous regex missed
      # worktree mods (leading space) -> false "clean" reports, violating PGR "commit cleanly".
      # Also filter claude_report and handoffs consistently.
      local dirty
      dirty=$( (git status --porcelain 2>/dev/null | grep -E '^( ?M| ?A| ?D| ?R| ?C|\?\?)' | grep -v '^?? handoffs/' | grep -v '^?? .ralph/' | grep -v 'claude_report.txt' | grep -v '__pycache__' || true ) | wc -l | tr -d ' ')
      if [[ "$dirty" -gt 0 ]]; then
        fail "Git working tree not clean. Commit or stash changes before complete-phase."
        echo "Dirty (excluding handoffs/ + temps):"
        git status --porcelain | grep -E '^( ?M| ?A| ?D| ?R| ?C|\?\?)' | grep -v 'handoffs/' | grep -v '.ralph/' | grep -v claude_report | grep -v pycache | head -10
        exit 1
      fi
      ok "Git tree clean. Proceeding with handoff."

      local phase
      phase=$(current_phase)
      local ts
      ts=$(date +%Y%m%d-%H%M%S)
      local hname="phase-${phase}-${ts}-review-request.md"
      local handoff="handoffs/${hname}"
      mkdir -p handoffs .ralph

      # Snapshot key state for self-contained handoff
      local loop_json
      loop_json=$(cat docs/LOOP_STATE.json 2>/dev/null || echo '{}')
      local gitlog
      gitlog=$(git log --oneline -6 2>/dev/null || echo 'n/a')
      local changed
      changed=$(git diff --name-only HEAD~1 2>/dev/null | head -30 || git status --porcelain | head -20 || echo 'first commit or n/a')

      # Build rich handoff (modeled on prior examples + ClaudeQA expectations)
      # Use unquoted heredoc only for the sections that require immediate $( ) expansion.
      cat > "$handoff" <<HFD
# Ralph Loop Handoff — Phase ${phase}
**Generated**: $(date -Iseconds)
**Implementer Message**: ${msg}
**Current LOOP_STATE**:
\`\`\`json
${loop_json}
\`\`\`

## 1. Role Instructions
**You are Claude acting strictly as the Independent QA Reviewer per \`ClaudeQA.md\`.**
Read the full ClaudeQA.md (in repo). The implementer followed PGR.md.
Do not write code. Produce the exact structured review format. End with one of:
CLEARED TO CONTINUE
PHASE COMPLETE - CLEARED TO ADVANCE
NEEDS WORK - DO NOT ADVANCE
Also write full report to claude_report.txt .

## 2. Phase Goals & Success Criteria
(Excerpt from docs/PHASES.md for the active phase)
\`\`\`
$(sed -n "/^## Phase ${phase} /,/^## /p" docs/PHASES.md | head -80 || python3 -c "
import re,sys
txt=open('docs/PHASES.md').read()
m=re.search(r'## Phase ${phase} —[^\n]*\n(.*?)(?=\n## |\Z)', txt, re.S)
print(m.group(1)[:3000] if m else '(see docs/PHASES.md)')
" 2>/dev/null || echo "(see docs/PHASES.md)")
\`\`\`

## 3. What Was Delivered (implementer claim)
${msg}

Key files changed (since prior):
${changed}

## 4. Git Activity
\`\`\`
${gitlog}
\`\`\`

## 5. Next
After review: address any Blockers/Majors, then either re-run complete-phase for fixes or (on clearance) let automation/script advance phase.
HFD

      # Update LOOP_STATE for the handoff. Use shell-expanded vars for note/hname safely.
      local note_str="Handoff generated: handoffs/${hname}"
      python3 - <<PYEOF
import json, datetime, os
data = {}
try:
    with open("docs/LOOP_STATE.json") as f: data = json.load(f)
except: pass
ph = int(data.get("current_phase", ${phase}))
data["status"] = "awaiting_qa"
data["last_handoff"] = "handoffs/${hname}"
hist = data.setdefault("phase_history", [])
# append note for this handoff if not duplicate (note_str is shell-expanded into this source)
note = "${note_str}"
if not any(note in str(h) for h in hist[-3:]):
    if isinstance(hist, list):
        # best effort append to last entry or add
        if hist and isinstance(hist[-1], dict):
            hist[-1].setdefault("notes", []).append(note)
        else:
            hist.append({"phase": ph, "notes": [note]})
data["notes"] = data.get("notes", "") + "; complete-phase at ${ts}"
with open("docs/LOOP_STATE.json", "w") as f:
    json.dump(data, f, indent=2)
print("LOOP_STATE updated for awaiting_qa")
PYEOF

      ok "Handoff written: $handoff"
      echo
      echo "════════════════════════════════════════════════════════"
      echo "COPY-PASTE PROMPT FOR CLAUDE (local claude CLI):"
      echo "════════════════════════════════════════════════════════"
      # SAFE emission: cat the ClaudeQA.md *literally* via file (no ${} expansion of its
      # content, which contains markdown **, ( ), code fences, backticks, etc that previously
      # triggered "permission denied", "command not found", syntax error near `(' and
      # "message got cut off" symptoms when unquoted heredoc or large inlines were used
      # during prompt construction / CLI handoff). Only safe ${phase} etc expand in the
      # small wrapper heredocs.
      cat <<'PROMPT_START'
You are the independent auditor. Follow this ClaudeQA.md document with absolute discipline.

=== ClaudeQA.md ===
PROMPT_START
      cat "$CLAUDEQA_FILE" 2>/dev/null || echo "(ClaudeQA.md not readable here; use file directly from docs/)"
      cat <<PROMPT_END
=== END ClaudeQA.md ===

This is the handoff after implementer work on Phase ${phase}.
Handoff file: ${handoff}
Recent git:
${gitlog}

Perform a full QA review per ClaudeQA.md.
Write a complete structured report to claude_report.txt .
At the end of your report, on its own line, output exactly one of:
CLEARED TO CONTINUE
PHASE COMPLETE - CLEARED TO ADVANCE
NEEDS WORK - DO NOT ADVANCE
Print a one-line summary at the very end.
PROMPT_END
      echo "════════════════════════════════════════════════════════"
      echo "Then (after claude writes claude_report.txt): ./tools/ralph.sh status"
      echo "The loop (ralph.sh <start> <end>) will auto-detect clearance on next full run."
      exit 0
      ;;
    help|--help|-h)
      cat <<'EOF'
ralph.sh — SuperCalc.OG unattended Ralph Loop driver

Usage:
  ./tools/ralph.sh                                   # run full loop (phases 0-7)
  ./tools/ralph.sh docs/PGR.md docs/ClaudeQA.md 0 0  # run specific phase range (e.g. just 0)
  ./tools/ralph.sh status                            # print current loop state, git, handoffs, HW verify
  ./tools/ralph.sh set-phase N                         # (rare) explicitly set current_phase (PGR: intentional only)
  ./tools/ralph.sh complete-phase "short description of increment"
  ./tools/ralph.sh record-hardware-verification "note" # Phase 0+: record human-confirmed smoke on real PicoCalc
  ./tools/ralph.sh help

complete-phase: checks git clean, writes handoffs/phase-N-...-review-request.md,
updates LOOP_STATE to awaiting_qa, prints ready-to-paste claude prompt.
Use this (not full ralph run) when you have manually implemented per PGR.

record-hardware-verification "note from human": records real-hw smoke for Phase 0 gate
  (sets last_completed_phase=0, hardware_verified, appends to phase 0 history).
  Run after user confirms dashboard/REPL/hybrid on actual PicoCalc + Pico 2 W.

set-phase N: sets current_phase (use sparingly per PGR phased discipline).

The script drives Grok (implementer per PGR.md) then Claude (QA per ClaudeQA.md).
It updates LOOP_STATE.json and produces handoffs/ on increments.

See docs/PGR.md for workflow and success criteria (status + complete-phase must run cleanly, etc).
EOF
      exit 0
      ;;
  esac
}

# ── option parsing for -a/--auditor (must run BEFORE subcommand detection) ─────
# Supports the requested CLI switch: ./tools/ralph.sh -a claude status
# ./tools/ralph.sh -a codex complete-phase "msg"
# ./tools/ralph.sh -a grok ...
# The AUDITOR_BIN + FLAGS are then used by run_claude_qa (and printed in status).
# Option parsing shifts them away so the existing early subcommand guard + positional
# parsing see a clean $1 (status / complete-phase / PGR etc).
while [[ $# -gt 0 && "$1" == -* ]]; do
  case "$1" in
    -a|--auditor)
      shift
      if [[ $# -eq 0 ]]; then
        echo "Error: -a/--auditor requires one of: claude codex grok" >&2
        exit 1
      fi
      AUDITOR="$1"
      case "$AUDITOR" in
        claude|claude*)
          AUDITOR_BIN="claude"
          AUDITOR_FLAGS="--dangerously-skip-permissions"
          ;;
        codex)
          AUDITOR_BIN="codex"
          AUDITOR_FLAGS="exec --full-auto"
          ;;
        grok)
          AUDITOR_BIN="grok"
          AUDITOR_FLAGS="--single"
          ;;
        *)
          # Custom/unknown auditor name: treat the value as the bin, keep prior FLAGS or default
          AUDITOR_BIN="$AUDITOR"
          AUDITOR_FLAGS="${AUDITOR_FLAGS:---dangerously-skip-permissions}"
          ;;
      esac
      shift
      ;;
    --)
      shift
      break
      ;;
    *)
      # Not our option; stop so normal subcmd/positional logic can see it (or error later)
      break
      ;;
  esac
done

# Early subcommand intercept (before normal arg defaults). This fixes prior
# breakage where `complete-phase "real msg"` would clobber CLAUDEQA_FILE and
# cause msg to be lost (handoffs showed "Implementer Message: complete-phase").
# (Now safe to run after -a options have been consumed.)
if [[ $# -gt 0 ]]; then
  first_arg="$1"
  if [[ "$first_arg" == "status" || "$first_arg" == "--status" || "$first_arg" == "help" || "$first_arg" == "--help" || "$first_arg" == "-h" || "$first_arg" == "complete-phase" || "$first_arg" == "set-phase" || "$first_arg" == "record-hardware-verification" ]]; then
    handle_subcommand "$@"
    # handle_subcommand always exits for these
  fi
fi

# ── argument parsing (normal full-loop path) ─────────────────────────────────────
PGR_FILE="${1:-docs/PGR.md}"
CLAUDEQA_FILE="${2:-docs/ClaudeQA.md}"
START_PHASE="${3:-0}"
END_PHASE="${4:-7}"

if [[ ! -f "$PGR_FILE" ]]; then
  echo "Error: PGR file '$PGR_FILE' not found." >&2
  exit 1
fi
if [[ ! -f "$CLAUDEQA_FILE" ]]; then
  echo "Error: ClaudeQA file '$CLAUDEQA_FILE' not found." >&2
  exit 1
fi

# Clean transient prior auditor report ONLY for full unattended loop runs.
# Subcommands (status, complete-phase, etc) already returned via the early intercept above.
# This prevents `ralph.sh status` (or record-hardware-verification) from deleting claude_report.txt
# and losing the last review/clearance (the bug reported: unconditional git checkout at top level).
# Old rate-limit/partial/error text will not pollute a *new* loop's "previous auditor report" or
# cause dirty-tree surprises (report is gitignored/untracked anyway).
git checkout -- claude_report.txt 2>/dev/null || rm -f claude_report.txt 2>/dev/null || true
log "Cleared prior claude_report.txt for fresh loop run."

MAX_RETRIES=3

# (current_phase + phase_cleared are defined at the very top, before handle_subcommand + early dispatch)

run_grok() {
  local phase="$1"
  local attempt="$2"

  local pgr_content
  pgr_content="$(cat "$PGR_FILE")"

  local last_report=""
  if [[ -f "claude_report.txt" ]]; then
    last_report="$(cat claude_report.txt)"
  fi

  local prompt
  if [[ "$attempt" -eq 1 ]]; then
    prompt="You are the Implementer following this PGR.md exactly.

=== PGR.md ===
${pgr_content}
=== END PGR.md ===

Current Phase: ${phase}
Attempt: ${attempt}

Project context (recent commits, files, state):
$(git log --oneline -5 2>/dev/null || echo 'no git log')
$(git status --porcelain 2>/dev/null || echo 'no git status')

Previous auditor report (address every issue):
${last_report:-"(first attempt for this phase)"}

Task: Implement the next small, verifiable increment for Phase ${phase} according to the phase goals in docs/PHASES.md and the rules in PGR.md.
- Work only on the current phase.
- Make concrete code changes in the workspace.
- At the end, commit with message: 'phase-${phase}-inc${attempt}: <very short description>'
- Be precise and follow PGR.md (thin boundary, C for hot paths, offline-first, etc.).

After you are done, the work will be handed to the auditor."
  else
    # Limit previous report size in the embedded prompt to avoid CLI arg truncation /
    # "message got cut off" and "you just sent "to" and nothing else" symptoms when
    # full prior claude_report (with accumulated output or large handoffs) + PGR
    # exceeds practical limits for --single or the receiving model/CLI.
    # The full report + handoff files remain in the workspace for the implementer
    # (per "Read the previous claude_report.txt now").
    local limited_report
    limited_report=$(head -c 1500 claude_report.txt 2>/dev/null || echo "(no prior report or empty)")
    prompt="*** QA REJECTION — RETRY ${attempt}/${MAX_RETRIES} ***

Read the previous claude_report.txt now. Fix every issue the auditor raised before writing new code.
Address all blockers and majors first.

You are still the Implementer. Follow PGR.md.

=== PGR.md (reminder) ===
${pgr_content}
=== END PGR.md ===

Current Phase: ${phase}
This is retry ${attempt}.

Previous auditor report (excerpt; read full claude_report.txt + latest handoff/phase-N-*-review-request.md in workspace for complete context):
${limited_report}
... (truncated for prompt size safety; full file on disk)

Task: Fix the issues from the auditor report and complete a clean increment for Phase ${phase}.
Commit with: 'phase-${phase}-fix${attempt}: <short description>'

After you are done, it will be re-audited."
  fi

  log "Running Grok (implementer) — Phase ${phase}, attempt ${attempt}..."
  # Use the installed Grok CLI in headless mode
  # --single for the prompt, --always-approve to auto-allow tool use (like full-auto)
  if ! grok --single "$prompt" --always-approve; then
    fail "Grok CLI exited with error on Phase ${phase} attempt ${attempt}."
    return 1
  fi

  # Ensure a commit happened (Grok should have done it per prompt; fallback)
  if git status --porcelain | grep -q .; then
    git add -A
    git commit -m "phase-${phase}-inc${attempt}: Grok implementer work (auto-fallback commit)" || true
  fi

  ok "Grok completed Phase ${phase} attempt ${attempt}. Changes committed."
}

run_claude_qa() {
  local phase="$1"
  log "Running ${AUDITOR} (auditor) — Phase ${phase}..."

  # Lean prompt: tell the auditor to read the actual files from the workspace using its tools.
  # This avoids embedding the entire ClaudeQA.md + huge context every time.
  # Phase-aware ls (prefers the handoff for *this* phase) + explicit Read of LOOP/PHASES.
  # Avoids the prior phase-0 hardcode that produced empty ls results + partial "message got cut off"
  # symptoms and any downstream shell parse of instruction text.
  local auditor_prompt="You are the independent auditor. Follow exactly the instructions in the file docs/ClaudeQA.md (use the Read tool on it).

Current phase: ${phase}

Handoff for this increment:
- Recent changes: run Bash(git log --oneline -5) and Bash(git diff HEAD~1 --name-only) to see what Grok just did.
- Read the most recent handoff file: ls -1 handoffs/phase-${phase}-*-review-request.md 2>/dev/null | tail -1 || ls -1 handoffs/phase-*-review-request.md 2>/dev/null | tail -1 ; then Read the resulting path.
- Read docs/LOOP_STATE.json and extract the section for Phase ${phase} from docs/PHASES.md .
- If claude_report.txt exists, read the prior attempt (this may be a retry after QA feedback).

Produce the FULL structured Ralph Loop QA Review report (use the exact format from ClaudeQA.md).
Write the complete report to claude_report.txt (overwrite the file).
**Also print the full report text to stdout** so it is captured even if your file-write tool has issues.

At the very end of claude_report.txt (on its own line) output exactly one of:
CLEARED TO CONTINUE
PHASE COMPLETE - CLEARED TO ADVANCE
NEEDS WORK - DO NOT ADVANCE

Also print a short one-line summary to stdout at the end."

  # Use the AUDITOR_BIN/FLAGS from -a parsing (falls back to claude if not set).
  # Build array safely. Attach the prompt arg using the correct flag/position per auditor
  # type so -a codex / -a grok produce runnable commands (not always forcing -p).
  # claude: ... -p "prompt"
  # codex:  ... "prompt"   (after exec --full-auto)
  # grok:   ... "prompt"   (after --single)
  local -a cmd
  if [[ -n "$AUDITOR_BIN" ]]; then
    cmd=( "$AUDITOR_BIN" )
    for f in $AUDITOR_FLAGS; do cmd+=( "$f" ); done
  else
    cmd=( claude --dangerously-skip-permissions )
  fi

  case "$AUDITOR" in
    codex|grok)
      # Prompt is a trailing positional argument for these CLIs
      cmd+=( "$auditor_prompt" )
      ;;
    *)
      # claude and fallbacks use -p
      cmd+=( -p "$auditor_prompt" )
      ;;
  esac

  # Run with a reasonable timeout. Note: the prompt tells the auditor to write
  # the report to claude_report.txt itself (via its tools). We also capture stdout.
  # The CLI may exit non-zero even when the model successfully wrote a full
  # structured report (especially in "Claude Code" agentic CLIs vs. rich IDE sessions).
  # We therefore do a post-mortem check for a usable report + clearance line.
  echo "[ralph] Invoking auditor: ${cmd[*]} (timeout 300s, output >> claude_report.txt)"
  local claude_rc=0
  if ! timeout 300 "${cmd[@]}" >> claude_report.txt 2>&1; then
    claude_rc=$?
    echo "[ERROR] Local $AUDITOR review exited with rc=$claude_rc (timeout or CLI error) on Phase ${phase}." >> claude_report.txt
    warn "Auditor CLI exited rc=$claude_rc on Phase ${phase} (common with agentic claude CLI one-shot vs. full IDE session)."
  fi

  # Tolerate "failure" if the model still managed to produce a proper report
  # ending in one of the expected clearance tokens (this is what happened when
  # you drove the review successfully from VS Code and it wrote claude_report.txt).
  if phase_cleared; then
    ok "$AUDITOR QA complete for Phase ${phase}. Report present with clearance."
  else
    # Fallback: look for signs of a real structured review even without the exact token yet
    if [[ -s claude_report.txt ]] && tail -20 claude_report.txt | grep -qiE 'APPROVED|NEEDS WORK|Final Verdict|CLEARED TO'; then
      warn "Auditor CLI exited non-zero (rc=$claude_rc) but claude_report.txt contains a review + verdict text. Proceeding (you may need to confirm the exact clearance line)."
    else
      fail "$AUDITOR QA CLI timed out or errored on Phase ${phase} (no usable report detected)."
      return 1
    fi
  fi
}

# ── main loop ──────────────────────────────────────────────────────────────────
echo -e "\n${BOLD}════════════════════════════════════════════════════════${RESET}"
echo -e "${BOLD}  ralph.sh — SuperCalc.OG Ralph Loop (Grok + Claude)${RESET}"
echo -e "${BOLD}  PGR: ${PGR_FILE}${RESET}"
echo -e "${BOLD}  ClaudeQA: ${CLAUDEQA_FILE}${RESET}"
echo -e "${BOLD}  Phases ${START_PHASE}–${END_PHASE}  |  max ${MAX_RETRIES} retries/phase${RESET}"
echo -e "${BOLD}════════════════════════════════════════════════════════${RESET}\n"

for phase in $(seq "$START_PHASE" "$END_PHASE"); do
  echo -e "\n${BOLD}━━━  PHASE ${phase} / ${END_PHASE}  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"

  attempt=1
  while true; do
    # Grok implements (guided by PGR.md)
    if ! run_grok "$phase" "$attempt"; then
      fail "Grok failed on Phase ${phase} attempt ${attempt}. Halting."
      exit 1
    fi

    # Hand off to Claude for QA (guided by ClaudeQA.md)
    if ! run_claude_qa "$phase"; then
      fail "Claude QA failed on Phase ${phase}. Halting."
      exit 1
    fi

    # Check clearance from the report
    if phase_cleared; then
      ok "Phase ${phase} CLEARED by Claude. Advancing."
      # Update LOOP_STATE.json so other tools stay in sync
      python3 -c '
import json, sys
data = {}
try:
    with open("docs/LOOP_STATE.json") as f:
        data = json.load(f)
except:
    pass
data["current_phase"] = '"$((phase + 1))"'
data["status"] = "in_progress"
with open("docs/LOOP_STATE.json", "w") as f:
    json.dump(data, f, indent=2)
' || true
      break
    else
      warn "Phase ${phase} had issues per Claude (attempt ${attempt}/${MAX_RETRIES})."
      if [[ "$attempt" -ge "$MAX_RETRIES" ]]; then
        fail "Phase ${phase} failed after ${MAX_RETRIES} attempts. Review claude_report.txt and handoff material."
        exit 2
      fi
      attempt=$((attempt + 1))
      log "Feeding Claude report back to Grok for retry..."
    fi
  done
done

echo -e "\n${BOLD}════════════════════════════════════════════════════════${RESET}"
ok "All phases ${START_PHASE}–${END_PHASE} complete. Check claude_report.txt and .ralph/ for history."
echo -e "${BOLD}════════════════════════════════════════════════════════${RESET}\n"
