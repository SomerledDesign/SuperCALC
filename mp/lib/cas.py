"""
SuperCalc.OG — Thin CAS / symbolic surface (Phase 7 inc2).

Leverages eigenmath (or common aliases) when present in the base firmware
(zenodante/LofiFren-style builds often include it as a prebuilt MPy module).
Falls back to a documented stub on host or ports without eigenmath.
All core paths remain offline; no network, no heavy deps.

Thin boundary: MPy orchestration here (like solver/plot). No C changes.
inc1: basic simplify/solve/diff as RPN + .cas + stub.
inc2: Symbolic first-class wrapper (str subclass for RPL compat + future mixing guard),
dispatch hygiene in expr, help text for solve RPN layout, full RPN word test cov, nits closed.

RPL spirit: results are first-class stack values (Symbolic for symbolic; sto/rcl/use in progs),
visible in REPL .s etc. Future numeric-on-symbolic will be able to detect via isinstance.
"""

HAS_CAS = False
_CAS_BACKEND = "stub"
_EIGEN = None


class Symbolic(str):
    """First-class symbolic result on the RPL stack (str subclass).

    Keeps full compatibility with existing str paths (sto/rcl, prog bodies, REPL display,
    .s etc) while allowing future detection to avoid treating symbolic forms as
    literal string data or feeding them blindly to numeric ops.

    On eigenmath: holds the backend's printed result form.
    On stub: "stub:..." forms for immediate host/demo/test usability.
    """
    pass


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
        return Symbolic(f"stub:simplify({s})")
    try:
        # Common eigenmath surface patterns (defensive; ports vary slightly)
        if hasattr(_EIGEN, "simplify"):
            res = _EIGEN.simplify(s)
            return Symbolic(str(res))
        if hasattr(_EIGEN, "eval"):
            # Some builds expose eval("simplify(...)")
            res = _EIGEN.eval("simplify(" + s + ")")
            return Symbolic(str(res))
        # Fallback: pass through if no known entry (still "has_cas" true)
        return Symbolic(s)
    except Exception as e:
        return Symbolic(f"cas-err:simplify:{e}")

def solve(eq, var="x"):
    """
    Symbolic solve stub (eq as str, e.g. 'x^2-2'). Returns solution form or stub.
    Mirrors contract of numeric solver but for symbolic result (string on stack).
    """
    s = str(eq)
    v = str(var)
    if not HAS_CAS or _EIGEN is None:
        return Symbolic(f"stub:solve({s}, {v})")
    try:
        if hasattr(_EIGEN, "solve"):
            res = _EIGEN.solve(s, v)
            return Symbolic(str(res))
        if hasattr(_EIGEN, "eval"):
            res = _EIGEN.eval("solve(" + s + ", " + v + ")")
            return Symbolic(str(res))
        return Symbolic(f"eigenmath-solve({s},{v})")
    except Exception as e:
        return Symbolic(f"cas-err:solve:{e}")

# Small set of additional surface words for RPL/REPL experimentation (inc1 minimal; inc2: typed)
def diff(expr, var="x"):
    """Differentiate expr w.r.t. var (stub or eigenmath delegation). Returns Symbolic result."""
    if not HAS_CAS or _EIGEN is None:
        return Symbolic(f"stub:diff({expr}, {var})")
    try:
        if hasattr(_EIGEN, "diff"):
            return Symbolic(str(_EIGEN.diff(str(expr), var)))
        return Symbolic(f"eigenmath-diff({expr},{var})")
    except Exception as e:
        return Symbolic(f"cas-err:diff:{e}")

__all__ = ["HAS_CAS", "Symbolic", "version", "info", "simplify", "solve", "diff"]
