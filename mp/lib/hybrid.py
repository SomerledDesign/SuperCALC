"""
Thin hybrid math interface for SuperCalc.OG (Phase 1 core math + expr, Phase 2 math surface).
Tries the fast C extension (picocalc_math) first, falls back to Python math.
This is the canonical thin boundary: UI/lang in MPy, hot numeric in C when available.

On real hardware after custom UF2 build: HAS_C_MATH=True and calls are native.
On host/dev machine: always falls back (C module not importable outside MP build).
"""

import math as _py_math

try:
    import picocalc_math as _c
    HAS_C_MATH = True
except ImportError:
    HAS_C_MATH = False

def version():
    if HAS_C_MATH:
        return _c.version()
    return "pure-python-fallback-0.6-phase4"

def add(a, b):
    if HAS_C_MATH:
        return _c.add(a, b)
    return a + b

def sub(a, b):
    if HAS_C_MATH:
        return _c.sub(a, b)
    return a - b

def mul(a, b):
    if HAS_C_MATH:
        return _c.mul(a, b)
    return a * b

def div(a, b):
    if HAS_C_MATH:
        return _c.div(a, b)
    if b == 0:
        raise ValueError("division by zero")
    return a / b

def sin(x):
    if HAS_C_MATH:
        return _c.sin(x)
    return _py_math.sin(x)

def cos(x):
    if HAS_C_MATH:
        return _c.cos(x)
    return _py_math.cos(x)

def tan(x):
    if HAS_C_MATH:
        return _c.tan(x)
    return _py_math.tan(x)

def asin(x):
    if HAS_C_MATH:
        return _c.asin(x)
    if x < -1 or x > 1:
        raise ValueError("asin domain error")
    return _py_math.asin(x)

def acos(x):
    if HAS_C_MATH:
        return _c.acos(x)
    if x < -1 or x > 1:
        raise ValueError("acos domain error")
    return _py_math.acos(x)

def atan(x):
    if HAS_C_MATH:
        return _c.atan(x)
    return _py_math.atan(x)

def atan2(y, x):
    if HAS_C_MATH:
        return _c.atan2(y, x)
    return _py_math.atan2(y, x)

def sqrt(x):
    if HAS_C_MATH:
        return _c.sqrt(x)
    if x < 0:
        raise ValueError("sqrt of negative")
    return _py_math.sqrt(x)

def exp(x):
    if HAS_C_MATH:
        return _c.exp(x)
    return _py_math.exp(x)

def log(x):
    if HAS_C_MATH:
        return _c.log(x)
    if x <= 0:
        raise ValueError("log of non-positive")
    return _py_math.log(x)

def log10(x):
    if HAS_C_MATH:
        return _c.log10(x)
    if x <= 0:
        raise ValueError("log10 of non-positive")
    return _py_math.log10(x)

def pow(x, y):
    if HAS_C_MATH:
        return _c.pow(x, y)
    # Match C path behavior for negative base with non-integer exponent:
    # C returns NaN (deliberate, see DECISIONS.md); guard here so host fallback
    # is a faithful proxy (instead of raising ValueError from _py_math.pow).
    if x < 0 and not (isinstance(y, (int, float)) and y == int(y)):
        return float('nan')
    return _py_math.pow(x, y)

def fabs(x):
    if HAS_C_MATH:
        return _c.fabs(x)
    return _py_math.fabs(x)

# rpn_eval: C hot path when available (Phase 1 expression kernel).
# tokens: iterable of float/int + op strings (see C for supported set).
# Fallback implements equivalent small RPN engine in pure Python.
def rpn_eval(tokens):
    if HAS_C_MATH:
        return _c.rpn_eval(tokens)
    # pure py fallback (matches C semantics for host tests)
    stack = []
    for tok in tokens:
        if isinstance(tok, (int, float)):
            stack.append(float(tok))
            continue
        if not isinstance(tok, str):
            raise ValueError("rpn token must be number or op str")
        op = tok
        if op in ("+", "add"):
            if len(stack) < 2: raise ValueError("rpn stack underflow")
            b = stack.pop()
            a = stack.pop()
            stack.append(a + b)
        elif op in ("-", "sub"):
            if len(stack) < 2: raise ValueError("rpn stack underflow")
            b = stack.pop()
            a = stack.pop()
            stack.append(a - b)
        elif op in ("*", "mul"):
            if len(stack) < 2: raise ValueError("rpn stack underflow")
            b = stack.pop()
            a = stack.pop()
            stack.append(a * b)
        elif op in ("/", "div"):
            if len(stack) < 2: raise ValueError("rpn stack underflow")
            b = stack.pop()
            a = stack.pop()
            if b == 0: raise ValueError("division by zero")
            stack.append(a / b)
        elif op in ("pow", "^"):
            if len(stack) < 2: raise ValueError("rpn stack underflow")
            b = stack.pop()
            a = stack.pop()
            # Match leaf/C behavior for negative^non-int (return NaN, do not raise)
            if a < 0 and not (isinstance(b, (int, float)) and b == int(b)):
                stack.append(float('nan'))
            else:
                stack.append(_py_math.pow(a, b))
        elif op == "sin":
            if len(stack) < 1: raise ValueError("rpn stack underflow")
            a = stack.pop()
            stack.append(_py_math.sin(a))
        elif op == "cos":
            if len(stack) < 1: raise ValueError("rpn stack underflow")
            a = stack.pop()
            stack.append(_py_math.cos(a))
        elif op == "tan":
            if len(stack) < 1: raise ValueError("rpn stack underflow")
            a = stack.pop()
            stack.append(_py_math.tan(a))
        elif op == "asin":
            if len(stack) < 1: raise ValueError("rpn stack underflow")
            a = stack.pop()
            if a < -1 or a > 1: raise ValueError("asin domain error")
            stack.append(_py_math.asin(a))
        elif op == "acos":
            if len(stack) < 1: raise ValueError("rpn stack underflow")
            a = stack.pop()
            if a < -1 or a > 1: raise ValueError("acos domain error")
            stack.append(_py_math.acos(a))
        elif op == "atan":
            if len(stack) < 1: raise ValueError("rpn stack underflow")
            a = stack.pop()
            stack.append(_py_math.atan(a))
        elif op == "atan2":
            if len(stack) < 2: raise ValueError("rpn stack underflow")
            b = stack.pop()
            a = stack.pop()
            stack.append(_py_math.atan2(a, b))
        elif op == "sqrt":
            if len(stack) < 1: raise ValueError("rpn stack underflow")
            a = stack.pop()
            if a < 0: raise ValueError("sqrt of negative")
            stack.append(_py_math.sqrt(a))
        elif op == "log":
            if len(stack) < 1: raise ValueError("rpn stack underflow")
            a = stack.pop()
            if a <= 0: raise ValueError("log of non-positive")
            stack.append(_py_math.log(a))
        elif op == "log10":
            if len(stack) < 1: raise ValueError("rpn stack underflow")
            a = stack.pop()
            if a <= 0: raise ValueError("log10 of non-positive")
            stack.append(_py_math.log10(a))
        elif op == "exp":
            if len(stack) < 1: raise ValueError("rpn stack underflow")
            a = stack.pop()
            stack.append(_py_math.exp(a))
        elif op in ("fabs", "abs"):
            if len(stack) < 1: raise ValueError("rpn stack underflow")
            a = stack.pop()
            stack.append(_py_math.fabs(a))
        elif op in ("neg", "chs"):
            if len(stack) < 1: raise ValueError("rpn stack underflow")
            a = stack.pop()
            stack.append(-a)
        elif op == "dup":
            if len(stack) < 1: raise ValueError("rpn stack underflow")
            stack.append(stack[-1])
        elif op == "drop":
            if len(stack) < 1: raise ValueError("rpn stack underflow")
            stack.pop()
        elif op == "swap":
            if len(stack) < 2: raise ValueError("rpn stack underflow")
            stack[-1], stack[-2] = stack[-2], stack[-1]
        elif op == "over":
            if len(stack) < 2: raise ValueError("rpn stack underflow")
            stack.append(stack[-2])
        else:
            raise ValueError("unknown rpn op: " + op)
    if len(stack) < 1:
        raise ValueError("rpn empty stack at end")
    return stack[-1]

# Note: infix parsing + variable store live in mp/lang/ (MPy for iteration speed).
# rpn_eval is the C-accelerated kernel for evaluation (hot numeric dispatch + stack).
# Variables / sto / rcl are handled by the lang layer (side effects outside pure compute).

# --- Phase 2: thin vm boundary (picocalc_vm C module) ---
# For inc1 this is a skeleton: version + exec stub.
# Full VM (bytecode, control flow, call stack) lives in src/core/picocalc_vm.c and
# will be driven from mp/lang later. On host we fall back to the prog/expr layer so
# higher-level tests remain runnable.
try:
    import picocalc_vm as _vm
    HAS_VM = True
except ImportError:
    HAS_VM = False

def vm_version():
    if HAS_VM:
        return _vm.version()
    return "vm-py-fallback-0.5"

def vm_exec(obj):
    """Skeleton exec. If obj is a Program (or name), delegates to lang.prog run.
    If plain rpn token list, falls back to expr rpn (or C rpn_eval when wired).
    Real C impl will take bytecode or token form for speed.
    """
    if HAS_VM:
        # When real C module present, prefer its entry (future incs will define shape)
        try:
            return _vm.exec(obj)  # placeholder name; adjust when C impl added
        except NotImplementedError:
            pass  # C skel; fall through to py (intentional for skeleton period)
        # Other exceptions from a real C impl will propagate (do not swallow)
    # py fallback path (host/dev)
    from mp.lang.prog import is_program, run_prog
    if is_program(obj):
        return run_prog(obj)
    # treat as rpn token list (re-use expr for full var/sto support in skel)
    from mp.lang.expr import eval_rpn
    return eval_rpn(obj)

# --- Phase 3: thin plot boundary (picocalc_plot C module) ---
# For inc1 this is a skeleton: version + sample stub (raises NotImpl).
# Real sampling (cartesian + future polar) implemented in mp/plot/plot.py
# (re-uses expr + hybrid math for host continuity and rapid iteration).
# C will later own dense sampling loops + raster for speed on 320x320.
try:
    import picocalc_plot as _plot
    HAS_PLOT = True
except ImportError:
    HAS_PLOT = False

def plot_version():
    if HAS_PLOT:
        return _plot.version()
    return "plot-py-fallback-0.5"

def plot_sample(obj):
    """Skeleton entry (signature will evolve). Real work for inc1 is in mp.plot.
    When C present and implemented, this (or new entrypoints taking buffers)
    will accelerate f(x) sampling and drawing.
    """
    if HAS_PLOT:
        try:
            return _plot.sample(obj)
        except NotImplementedError:
            pass  # C skel; fall through
    # py path (always works on host; on device too until C wired)
    from mp.plot import cartesian_sample
    # minimal passthrough example; real callers use the mp.plot API directly
    return cartesian_sample(obj) if isinstance(obj, str) else None

# --- Phase 4 inc1: stats (thin boundary to C reduce or py) ---
# HAS_STATS True when C math present (stats are in same module).
HAS_STATS = HAS_C_MATH

def _ensure_list(it):
    if isinstance(it, (list, tuple)):
        return list(it)
    # accept any iterable for host py path
    return list(it)

def stats_sum(xs):
    if HAS_C_MATH:
        return _c.stats_sum(xs)
    xs = _ensure_list(xs)
    if not xs:
        raise ValueError("stats empty input")
    # use fsum for better accuracy on host; validate numerics for error parity with C
    import math as _m
    try:
        vals = [float(x) for x in xs]
    except Exception:
        raise ValueError("stats expected numeric iterable")
    return _m.fsum(vals)

def stats_mean(xs):
    if HAS_C_MATH:
        return _c.stats_mean(xs)
    xs = _ensure_list(xs)
    if not xs:
        raise ValueError("stats empty input")
    import math as _m
    try:
        vals = [float(x) for x in xs]
    except Exception:
        raise ValueError("stats expected numeric iterable")
    return _m.fsum(vals) / len(vals)

def stats_stdev(xs):
    if HAS_C_MATH:
        return _c.stats_stdev(xs)
    xs = _ensure_list(xs)
    n = len(xs)
    if n < 2:
        raise ValueError("stdev requires at least 2 values")
    import math as _m
    # Welford mirror for host fidelity; validate
    try:
        vals = [float(v) for v in xs]
    except Exception:
        raise ValueError("stats expected numeric iterable")
    mean = 0.0
    m2 = 0.0
    for i, x in enumerate(vals):
        ncur = i + 1
        delta = x - mean
        mean += delta / ncur
        m2 += delta * (x - mean)
    var = m2 / (n - 1)
    return _m.sqrt(var if var > 0 else 0.0)