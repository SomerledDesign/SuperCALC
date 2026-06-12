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

# ── colors (hoisted so subcommands like complete-phase can use ok/fail early) ─────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

log()  { echo -e "${CYAN}[ralph]${RESET} $*"; }
ok()   { echo -e "${GREEN}[ralph]${RESET} $*"; }
warn() { echo -e "${YELLOW}[ralph]${RESET} $*"; }
fail() { echo -e "${RED}[ralph]${RESET} $*"; }

# ── argument parsing ────────────────────────────────────────────────────────────
PGR_FILE="${1:-docs/PGR.md}"
CLAUDEQA_FILE="${2:-docs/ClaudeQA.md}"
START_PHASE="${3:-0}"
END_PHASE="${4:-7}"

# --- subcommand handling (status / help) for Phase 0 automation criteria + PGR ---
handle_subcommand() {
  local cmd="$1"
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
    print("Git dirty files:", len(lines))
    for l in lines[:5]:
        print("  ", l)
except Exception:
    print("Git: n/a")
print()
if os.path.isdir("handoffs"):
    hs = sorted([h for h in os.listdir("handoffs") if h.endswith(".md")])[-3:]
    print("Recent handoffs:", hs)
print("Run example: ./tools/ralph.sh docs/PGR.md docs/ClaudeQA.md 0 0")
PYEOF
      echo "════════════════════════════════════════════════════════"
      exit 0
      ;;
    complete-phase)
      # Proper complete-phase per PGR.md + Phase 0 success criteria + auditor feedback (M-1).
      # - requires clean git (enforces "commit cleanly" before handoff)
      # - generates timestamped handoff/phase-N-...-review-request.md
      # - updates LOOP_STATE.json (status=awaiting_qa, last_handoff, history note)
      # - prints copy-paste ready prompt for local claude (per ClaudeQA.md)
      # Does NOT auto-run claude or the full loop; that is done by `ralph.sh <phases>` or human.
      local msg="${1:-phase inc complete}"
      echo "════════════════════════════════════════════════════════"
      echo "  ralph.sh complete-phase — generate handoff + await QA"
      echo "════════════════════════════════════════════════════════"

      # 1. Git must be clean (or only untracked we intend to leave)
      # Note: use || true after grep to be robust under set -euo pipefail (grep exits 1 on 0 matches)
      local dirty
      dirty=$(git status --porcelain 2>/dev/null | grep -E '^(M|A|D|R|C|\?\?)' | grep -v '^?? handoffs/' | grep -v '^?? .ralph/' | grep -v 'claude_report.txt' | grep -v '__pycache__' || true | wc -l | tr -d ' ')
      if [[ "$dirty" -gt 0 ]]; then
        fail "Git working tree not clean. Commit or stash changes before complete-phase."
        echo "Dirty (excluding handoffs/ + temps):"
        git status --porcelain | grep -E '^(M|A|D|R|C|\?\?)' | grep -v 'handoffs/' | grep -v '.ralph/' | grep -v claude_report | grep -v pycache | head -10
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
$(sed -n "/^## Phase ${phase} /,/^## /p" docs/PHASES.md | head -60 || echo "(see docs/PHASES.md)")
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

      # Update LOOP_STATE for the handoff
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
# append note for this handoff if not duplicate
note = f"Handoff generated: { 'handoffs/${hname}' }"
if not any(note in str(h) for h in hist[-3:]):
    if isinstance(hist, list):
        # best effort append to last entry or add
        if hist and isinstance(hist[-1], dict):
            hist[-1].setdefault("notes", []).append(note)
        else:
            hist.append({"phase": ph, "notes": [note]})
data["notes"] = data.get("notes", "") + f"; complete-phase at ${ts}"
with open("docs/LOOP_STATE.json", "w") as f:
    json.dump(data, f, indent=2)
print("LOOP_STATE updated for awaiting_qa")
PYEOF

      ok "Handoff written: $handoff"
      echo
      echo "════════════════════════════════════════════════════════"
      echo "COPY-PASTE PROMPT FOR CLAUDE (local claude CLI):"
      echo "════════════════════════════════════════════════════════"
      cat <<PROMPT
You are the independent auditor. Follow this ClaudeQA.md document with absolute discipline.

=== ClaudeQA.md ===
$(cat "$CLAUDEQA_FILE" 2>/dev/null || echo "(ClaudeQA.md not readable here; use file)")
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
PROMPT
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
  ./tools/ralph.sh status                            # print current loop state, git, handoffs
  ./tools/ralph.sh complete-phase "short description of increment"
  ./tools/ralph.sh help

complete-phase: checks git clean, writes handoffs/phase-N-...-review-request.md,
updates LOOP_STATE to awaiting_qa, prints ready-to-paste claude prompt.
Use this (not full ralph run) when you have manually implemented per PGR.

The script drives Grok (implementer per PGR.md) then Claude (QA per ClaudeQA.md).
It updates LOOP_STATE.json and produces handoffs/ on increments.

See docs/PGR.md for workflow and success criteria (status + complete-phase must run cleanly, etc).
EOF
      exit 0
      ;;
  esac
}

# ── helpers (hoisted early so handle_subcommand for complete-phase/status can call them) ──
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

# Detect if first positional after implicit is a subcommand (or if PGR was defaulted but 1st arg looks like cmd)
if [[ "$PGR_FILE" == "status" || "$PGR_FILE" == "help" || "$PGR_FILE" == "--help" || "$PGR_FILE" == "-h" || "$PGR_FILE" == "--status" || "$PGR_FILE" == "complete-phase" ]]; then
  handle_subcommand "$PGR_FILE"
elif [[ "$START_PHASE" == "status" || "$START_PHASE" == "help" || "$START_PHASE" == "--help" || "$START_PHASE" == "-h" || "$START_PHASE" == "--status" || "$START_PHASE" == "complete-phase" ]]; then
  handle_subcommand "$START_PHASE"
fi

if [[ ! -f "$PGR_FILE" ]]; then
  echo "Error: PGR file '$PGR_FILE' not found." >&2
  exit 1
fi
if [[ ! -f "$CLAUDEQA_FILE" ]]; then
  echo "Error: ClaudeQA file '$CLAUDEQA_FILE' not found." >&2
  exit 1
fi

MAX_RETRIES=3

# (helpers current_phase/phase_cleared hoisted earlier for subcommand dispatch)

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
    prompt="*** QA REJECTION — RETRY ${attempt}/${MAX_RETRIES} ***

Read the previous claude_report.txt now. Fix every issue the auditor raised before writing new code.
Address all blockers and majors first.

You are still the Implementer. Follow PGR.md.

=== PGR.md (reminder) ===
${pgr_content}
=== END PGR.md ===

Current Phase: ${phase}
This is retry ${attempt}.

Previous auditor report:
${last_report}

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
  log "Running Claude (auditor) — Phase ${phase}..."

  # Lean prompt: tell claude to read the actual files from the workspace using its tools.
  # This avoids embedding the entire ClaudeQA.md + huge context every time (the main cause of timeouts/hangs).
  local claude_prompt="You are the independent auditor. Follow exactly the instructions in the file docs/ClaudeQA.md (use the Read tool on it).

Current phase: ${phase}

Handoff for this increment:
- Recent changes: run Bash(git log --oneline -5) and Bash(git diff HEAD~1 --name-only) to see what Grok just did.
- Read the most recent handoff file: ls handoffs/phase-0-*.md | tail -1 then Read it.
- If claude_report.txt exists, read the prior attempt.

Produce the FULL structured Ralph Loop QA Review report (use the exact format from ClaudeQA.md).
Write the complete report to claude_report.txt (overwrite the file).
At the very end of claude_report.txt (on its own line) output exactly one of:
CLEARED TO CONTINUE
PHASE COMPLETE - CLEARED TO ADVANCE
NEEDS WORK - DO NOT ADVANCE

Also print a short one-line summary to stdout at the end."

  # Use timeout to prevent hard hangs. Claude Code can be slow on first reads but should not hang forever.
  # The --dangerously-skip-permissions helps with non-interactive runs.
  if ! timeout 180 claude --dangerously-skip-permissions -p "$claude_prompt" >> claude_report.txt 2>&1; then
    echo "[ERROR] Local Claude review timed out or failed on Phase ${phase}." >> claude_report.txt
    fail "Claude QA CLI timed out or errored on Phase ${phase}."
    return 1
  fi

  ok "Claude QA complete for Phase ${phase}. Report appended to claude_report.txt"
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
