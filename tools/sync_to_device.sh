#!/usr/bin/env bash
# Sync SuperCalc.OG MicroPython tree to a connected PicoCalc (mpremote).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
echo "Device:"
mpremote connect list || true
echo "Creating /mp ..."
mpremote mkdir :mp 2>/dev/null || true
mpremote mkdir :mp/lib 2>/dev/null || true
mpremote mkdir :mp/lang 2>/dev/null || true
mpremote mkdir :mp/ui 2>/dev/null || true
mpremote mkdir :mp/apps 2>/dev/null || true
mpremote mkdir :examples 2>/dev/null || true
echo "Pushing mp/ + examples/hw_smoke* + sc.py ..."
mpremote cp -r mp/lib/:mp/lib/
mpremote cp -r mp/lang/:mp/lang/
mpremote cp -r mp/ui/:mp/ui/
# apps if present
if [ -d mp/apps ]; then mpremote cp -r mp/apps/:mp/apps/ || true; fi
# package markers
for f in mp/__init__.py mp/lib/__init__.py mp/lang/__init__.py mp/ui/__init__.py; do
  [ -f "$f" ] && mpremote cp "$f" ":$f" || true
done
mpremote cp sc.py :sc.py
mpremote cp examples/hw_smoke_phase0.py :examples/hw_smoke_phase0.py 2>/dev/null || mpremote mkdir :examples && mpremote cp examples/hw_smoke_phase0.py :examples/hw_smoke_phase0.py
mpremote cp examples/hw_smoke_phase7.py :examples/hw_smoke_phase7.py
echo "Done. Try: mpremote repl"
echo "  >>> from mp.ui.calc_repl import run_demo; run_demo()"
