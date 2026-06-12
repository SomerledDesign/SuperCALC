"""
Thin hybrid math interface for SuperCalc.OG (Phase 1 core math + expr).
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
    return "pure-python-fallback-0.3"

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

def pow(x, y):
    if HAS_C_MATH:
        return _c.pow(x, y)
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