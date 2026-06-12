"""
SuperCalc.OG — Phase 1 core expression system (infix + RPN) + stack + variables.

MPy layer (rapid iteration per DECISIONS): 
- infix parser (shunting-yard lite) -> RPN token stream
- RPN driver with HP spirit stack ops (dup, drop, swap, over, neg/chs)
- Variable support: env dict for RCL (read) + STO (write) — side effects here.
- Thin calls to hybrid.rpn_eval / leafs for the numeric kernel (C when present).

C (picocalc_math): rpn_eval for pure-numeric hot paths + all math primitives.
Offline first. No network. Double baseline.

Usage (host or device after flash):
  from mp.lang.expr import eval_infix, eval_rpn, to_rpn
  print(eval_infix("2 + 3 * sin(pi/2)"))   # uses predefined 'pi'
  print(eval_rpn([2, 3, "+", 4, "*"]))     # 20
  env = {}
  eval_rpn([3.14159, "sto", "pi", "rcl", "pi", 2, "*"], env)  # stores, recalls
"""

import math as _m
from mp.lib.hybrid import (
    HAS_C_MATH, rpn_eval as _hybrid_rpn,
    sin, cos, tan, sqrt, log, exp, fabs, add, sub, mul, div, pow as hpow
)

# Predefined constants (RCL-able; can be shadowed by user env)
_PREDEFS = {
    "pi": _m.pi,
    "e": _m.e,
    "phi": (1 + _m.sqrt(5)) / 2,
}

def _is_number(tok):
    return isinstance(tok, (int, float))

def _resolve_var(name, env):
    if env and name in env:
        return env[name]
    if name in _PREDEFS:
        return _PREDEFS[name]
    raise ValueError(f"undefined variable: {name}")

# --- Infix to RPN (small shunting-yard supporting + - * / ^ , parens, unary-, funcs) ---
# Tokens: numbers become float, idents become ('var', name), calls/ops as str op.
# Funcs supported: sin cos tan sqrt log exp abs (written sin(...) etc)
_FUNC_NAMES = {"sin", "cos", "tan", "sqrt", "log", "exp", "abs", "fabs"}

def to_rpn(infix: str):
    """
    Return list of RPN tokens: float | str(op) | ('var', name)
    Very small, no full lexer — sufficient for Phase 1 inc1 verifiable slice.
    """
    s = infix.strip()
    out = []
    op_stack = []
    i = 0
    n = len(s)
    prev_was_op_or_start = True  # for unary minus detection

    def push_op(op):
        while op_stack and op_stack[-1] != "(" and _precedence(op_stack[-1]) >= _precedence(op):
            out.append(op_stack.pop())
        op_stack.append(op)

    while i < n:
        c = s[i]
        if c.isspace():
            i += 1
            continue
        if c.isdigit() or c == ".":
            # number literal
            j = i
            while j < n and (s[j].isdigit() or s[j] in ".eE+-"):
                # crude but ok for literals; stop at next obvious
                if s[j] in "+-" and j > i and s[j-1] not in "eE":
                    break
                j += 1
            numstr = s[i:j]
            try:
                val = float(numstr)
            except:
                raise ValueError(f"bad number at {i}: {numstr}")
            out.append(val)
            i = j
            prev_was_op_or_start = False
            continue
        if c.isalpha() or c == "_":
            # ident or func name
            j = i
            while j < n and (s[j].isalnum() or s[j] == "_"):
                j += 1
            name = s[i:j]
            i = j
            # peek for (
            while i < n and s[i].isspace(): i += 1
            if i < n and s[i] == "(":
                if name not in _FUNC_NAMES:
                    raise ValueError(f"unknown function: {name}")
                op_stack.append(name)  # func as op
                op_stack.append("(")
                i += 1  # consume (
                prev_was_op_or_start = True
            else:
                # variable
                out.append(("var", name))
                prev_was_op_or_start = False
            continue
        if c == "(":
            op_stack.append("(")
            i += 1
            prev_was_op_or_start = True
            continue
        if c == ")":
            while op_stack and op_stack[-1] != "(":
                out.append(op_stack.pop())
            if not op_stack or op_stack[-1] != "(":
                raise ValueError("mismatched )")
            op_stack.pop()  # (
            if op_stack and op_stack[-1] in _FUNC_NAMES:
                out.append(op_stack.pop())  # the func name as postfix op
            i += 1
            prev_was_op_or_start = False
            continue
        if c in "+-*/^":
            op = c
            if c == "-" and prev_was_op_or_start:
                op = "neg"  # unary
            push_op(op)
            i += 1
            prev_was_op_or_start = True
            continue
        raise ValueError(f"unexpected char in infix: {c}")
    while op_stack:
        o = op_stack.pop()
        if o == "(":
            raise ValueError("mismatched (")
        out.append(o)
    return out

def _precedence(op):
    if op in ("neg",):
        return 4
    if op in ("^", "pow"):
        return 3
    if op in ("*", "/",):
        return 2
    if op in ("+", "-",):
        return 1
    if op in _FUNC_NAMES:
        return 5
    return 0

def _rpn_to_numeric_tokens(rpn_with_vars, env):
    """Resolve ('var', name) to actual floats using env+predefs. Return pure numeric+op list for hybrid rpn."""
    res = []
    for t in rpn_with_vars:
        if isinstance(t, tuple) and t[0] == "var":
            res.append(_resolve_var(t[1], env))
        else:
            res.append(t)
    return res

def eval_infix(infix: str, env=None):
    """Evaluate infix algebraic expression. Supports vars from env or predefs (pi,e)."""
    rpn = to_rpn(infix)
    num_tokens = _rpn_to_numeric_tokens(rpn, env)
    # Use the C-accelerated (or fallback) rpn engine for the compute
    return _hybrid_rpn(num_tokens)

# --- RPN driver with variables + stack (HP spirit) ---
# tokens may contain numbers, ops, 'sto', 'rcl', and for rcl/sto the *next* token can be var name
# or use flat:  [ val, "sto", "x" ]   or [ "rcl", "x", 2, "*" ]
# We process sequentially using hybrid leafs for numeric, special case sto/rcl.

def eval_rpn(tokens, env=None):
    """
    RPN with full stack + variables.
    env: dict mutated for sto (and used for rcl). If None, fresh dict.
    Returns final top-of-stack value (after any trailing sto etc).
    Also returns env for caller if needed (side effect on passed or new).
    """
    if env is None:
        env = {}
    stack = []
    i = 0
    n = len(tokens)
    while i < n:
        tok = tokens[i]
        if _is_number(tok):
            stack.append(float(tok))
            i += 1
            continue
        if isinstance(tok, tuple) and tok[0] == "var":
            stack.append(_resolve_var(tok[1], env))
            i += 1
            continue
        if not isinstance(tok, str):
            raise ValueError("bad rpn token")
        op = tok
        if op in ("sto", "store", "->"):  # HP-ish
            if i + 1 >= n:
                raise ValueError("sto missing target name")
            if len(stack) < 1:
                raise ValueError("rpn stack underflow for sto")
            val = stack.pop()
            name_tok = tokens[i+1]
            if isinstance(name_tok, str):
                name = name_tok
            elif isinstance(name_tok, tuple) and name_tok[0] == "var":
                name = name_tok[1]
            else:
                raise ValueError("sto target must be name")
            env[name] = val
            i += 2
            continue
        if op in ("rcl", "recall"):
            if i + 1 >= n:
                raise ValueError("rcl missing name")
            name_tok = tokens[i+1]
            if isinstance(name_tok, str):
                name = name_tok
            elif isinstance(name_tok, tuple) and name_tok[0] == "var":
                name = name_tok[1]
            else:
                raise ValueError("rcl target must be name")
            val = _resolve_var(name, env)
            stack.append(val)
            i += 2
            continue
        # numeric or stack op: delegate as much as possible to hybrid (C)
        # For single op we feed a  mini rpn list
        if op in ("+", "-", "*", "/", "^", "pow", "sin", "cos", "tan", "sqrt", "log", "exp", "fabs", "abs", "neg", "chs", "dup", "drop", "swap", "over"):
            # build a 1 or 2 (or 0 for dup etc) arg mini program from current stack state
            # simplest: use leaf calls for numeric, direct manip for stack
            if op in ("dup", "drop", "swap", "over"):
                if op == "dup":
                    if not stack: raise ValueError("rpn stack underflow")
                    stack.append(stack[-1])
                elif op == "drop":
                    if not stack: raise ValueError("rpn stack underflow")
                    stack.pop()
                elif op == "swap":
                    if len(stack) < 2: raise ValueError("rpn stack underflow")
                    stack[-1], stack[-2] = stack[-2], stack[-1]
                elif op == "over":
                    if len(stack) < 2: raise ValueError("rpn stack underflow")
                    stack.append(stack[-2])
                i += 1
                continue
            # numeric apply via leaf hybrid (C accelerated)
            if op in ("+", "add"):
                if len(stack) < 2: raise ValueError("rpn stack underflow")
                b = stack.pop()
                a = stack.pop()
                stack.append(add(a, b))
            elif op in ("-", "sub"):
                if len(stack) < 2: raise ValueError("rpn stack underflow")
                b = stack.pop()
                a = stack.pop()
                stack.append(sub(a, b))
            elif op in ("*", "mul"):
                if len(stack) < 2: raise ValueError("rpn stack underflow")
                b = stack.pop()
                a = stack.pop()
                stack.append(mul(a, b))
            elif op in ("/", "div"):
                if len(stack) < 2: raise ValueError("rpn stack underflow")
                b = stack.pop()
                a = stack.pop()
                stack.append(div(a, b))
            elif op in ("^", "pow"):
                if len(stack) < 2: raise ValueError("rpn stack underflow")
                b = stack.pop()
                a = stack.pop()
                stack.append(hpow(a, b))
            elif op == "sin":
                if not stack: raise ValueError("rpn stack underflow")
                a = stack.pop()
                stack.append(sin(a))
            elif op == "cos":
                if not stack: raise ValueError("rpn stack underflow")
                a = stack.pop()
                stack.append(cos(a))
            elif op == "tan":
                if not stack: raise ValueError("rpn stack underflow")
                a = stack.pop()
                stack.append(tan(a))
            elif op == "sqrt":
                if not stack: raise ValueError("rpn stack underflow")
                a = stack.pop()
                stack.append(sqrt(a))
            elif op == "log":
                if not stack: raise ValueError("rpn stack underflow")
                a = stack.pop()
                stack.append(log(a))
            elif op == "exp":
                if not stack: raise ValueError("rpn stack underflow")
                a = stack.pop()
                stack.append(exp(a))
            elif op in ("fabs", "abs"):
                if not stack: raise ValueError("rpn stack underflow")
                a = stack.pop()
                stack.append(fabs(a))
            elif op in ("neg", "chs"):
                if not stack: raise ValueError("rpn stack underflow")
                a = stack.pop()
                stack.append(-a)
            else:
                raise ValueError("unknown rpn op: " + op)
            i += 1
            continue
        # unknown at top level
        raise ValueError("unknown rpn op or token: " + str(op))
    if not stack:
        raise ValueError("rpn empty stack at end")
    return stack[-1]

# convenience
def eval_rpn_str(rpn_text: str, env=None):
    """Accepts space separated like '2 3 + 4 *' or with names '3.14 sto pi rcl pi 2 *'."""
    toks = []
    for part in rpn_text.strip().split():
        if part in ("sto", "rcl", "store", "recall", "dup", "drop", "swap", "over", "neg", "chs") or part in _FUNC_NAMES or part in "+-*/^":
            toks.append(part)
        else:
            # number or bare var? treat bare idents after sto/rcl as names, but for general, if not num try var later
            try:
                toks.append(float(part))
            except ValueError:
                toks.append(("var", part))  # will resolve or be used by sto/rcl
    return eval_rpn(toks, env)

__all__ = ["to_rpn", "eval_infix", "eval_rpn", "eval_rpn_str", "HAS_C_MATH"]