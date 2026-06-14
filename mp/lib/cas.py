"""
SuperCalc.OG — Thin CAS / symbolic surface (Phase 7 inc1).

Leverages eigenmath (or common aliases) when present in the base firmware
(zenodante/LofiFren-style builds often include it as a prebuilt MPy module).
Falls back to a documented stub on host or ports without eigenmath.
All core paths remain offline; no network, no heavy deps.

Thin boundary: MPy orchestration here (like solver/plot). No C changes in inc1.
Future: richer surface (diff/integrate/series, ulab interop, C numeric CAS fallback)
or direct src/math dispatch if eigenmath absent in a build.

RPL spirit: results (currently str for symbolic) are first-class stack values,
storable/recallable, usable inside Programs, visible in REPL .s etc.
"""

HAS_CAS = False
_CAS_BACKEND = "stub"
_EIGEN = None

def _try_import_eigen():
    global HAS_CAS, _CAS_BACKEND, _EIGEN
    # Common names observed in community PicoCalc MPy ports that bundle eigenmath
    candidates = ("eigenmath", "em", "cas", "eigen")
    for name in candidates:
        try:
            mod = __import__(name)
            _EIGEN = mod
            HAS_CAS = True
            # Try to get a version string if the module exposes one
            ver = None
            if hasattr(mod, "version"):
                try:
                    ver = mod.version() if callable(mod.version) else mod.version
                except Exception:
                    ver = None
            _CAS_BACKEND = ver or "eigenmath"
            return
        except Exception:
            continue
    HAS_CAS = False
    _CAS_BACKEND = "stub (no eigenmath in firmware)"

_try_import_eigen()

def version():
    """Return short backend info string."""
    return _CAS_BACKEND

def info():
    """Dict with has_cas + backend for REPL / debug."""
    return {"has_cas": HAS_CAS, "backend": _CAS_BACKEND}

def simplify(expr):
    """
    Simplify a symbolic expr (str form preferred, e.g. 'x^2 + 2*x + 1' or 'sin(x)^2+cos(x)^2').
    On real firmware with eigenmath: delegates to it (best-effort; interface is port-dependent).
    On host / no-eigen: returns informative stub string (e.g. 'stub:simplify(x+x)') so
    demos, tests, and RPL programs remain runnable and observable without crashing.
    Numeric inputs are stringified for consistency.
    """
    s = str(expr)
    if not HAS_CAS or _EIGEN is None:
        # Host-friendly stub: immediately shows "CAS path taken" in demo/REPL without external dep.
        return f"stub:simplify({s})"
    try:
        # Common eigenmath surface patterns (defensive; ports vary slightly)
        if hasattr(_EIGEN, "simplify"):
            res = _EIGEN.simplify(s)
            return str(res)
        if hasattr(_EIGEN, "eval"):
            # Some builds expose eval("simplify(...)")
            res = _EIGEN.eval("simplify(" + s + ")")
            return str(res)
        # Fallback: pass through if no known entry (still "has_cas" true)
        return s
    except Exception as e:
        return f"cas-err:simplify:{e}"

def solve(eq, var="x"):
    """
    Symbolic solve stub (eq as str, e.g. 'x^2-2'). Returns solution form or stub.
    Mirrors contract of numeric solver but for symbolic result (string on stack).
    """
    s = str(eq)
    v = str(var)
    if not HAS_CAS or _EIGEN is None:
        return f"stub:solve({s}, {v})"
    try:
        if hasattr(_EIGEN, "solve"):
            res = _EIGEN.solve(s, v)
            return str(res)
        if hasattr(_EIGEN, "eval"):
            res = _EIGEN.eval("solve(" + s + ", " + v + ")")
            return str(res)
        return f"eigenmath-solve({s},{v})"
    except Exception as e:
        return f"cas-err:solve:{e}"

# Small set of additional surface words for RPL/REPL experimentation (inc1 minimal)
def diff(expr, var="x"):
    if not HAS_CAS or _EIGEN is None:
        return f"stub:diff({expr}, {var})"
    try:
        if hasattr(_EIGEN, "diff"):
            return str(_EIGEN.diff(str(expr), var))
        return f"eigenmath-diff({expr},{var})"
    except Exception as e:
        return f"cas-err:diff:{e}"

__all__ = ["HAS_CAS", "version", "info", "simplify", "solve", "diff"]
