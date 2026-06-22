"""
SuperCalc.OG Phase 7 inc2 — CalcREPL driver (REPL + UI integration + CAS surface + dispatch/ help hygiene)

Unified calculator REPL experience on top of the hybrid engine:
- enter(line): tries infix algebraic first (friendly default, hits C rpn_eval hot path via eval_infix),
  falls back to RPN/str stack words (eval_rpn_str) for HP-style direct entry and program words.
  Pure stack manip ("dup" etc) and "len"/stats on pre-pushed list data are driven directly against
  the REPL-visible stack for correct interactive semantics.
- Maintains visible stack + env (vars + first-class Programs) with full side-effect visibility.
- Dot-commands (.s, .plot, .solve, .help, .demo, ...) for immediate value from prior libs
  (solver, ascii plot, stats via hybrid, prog sto/run).
- LASTx + abs HP words (lift on entry, rpn visible, sto lastx special, mirrored for infix resolve).
- batch_run(lines) for deterministic host tests and scripted demos (no input()).
- run_demo(): self-contained tour exercising *every* major prior capability in one go.

RPL spirit: stack is always visible/inspectable, programs are first-class and callable by name
or via "run", side-effects (sto during solve/plot) are observable after the operation.

Thin boundary (Phase 6 strengthened): zero new numeric or parsing logic — only orchestration + LASTx register + presentation.
Re-uses exactly:
  mp.lang.expr.{eval_infix, eval_rpn_str, to_rpn, execute_rpn_body}
  mp.lang.prog.{make_prog, is_program}
  mp.lib.solver.find_root
  mp.plot.{ascii_plot, cartesian_sample}
  mp.lib.hybrid (indirectly via above + version)
  mp.lib.cas (Phase 7: simplify/solve/diff via eigenmath or stub)
execute_rpn_body is the single dispatch source; CalcREPL passes its live self.stack for visible stepwise + RPL inline run semantics.

Host: pure Python, works in any REPL.
Device: run from base firmware REPL/terminal (text only; pixels in later ui inc).
320x320 aware in spirit (plot defaults, future render will use).

Offline, double baseline. No network in any path.

Public:
    from mp.ui.calc_repl import CalcREPL, run_demo
    r = CalcREPL()
    r.enter("2+3*sin(pi/2)")   # infix path (C accelerated when present)
    r.enter("dup")                 # rpn stack word (direct manip)
    print(r.stack)
    r.enter(".s")                  # show stack
    r.enter(".plot sin(x)")
    run_demo()
"""
import os
import sys

# MicroPython-safe: no typing imports / __future__ annotations anywhere in import graph
# (expr/prog/etc purged of runtime annots). Phase 5 QA MPy blocker fully addressed.
# Project root on path for standalone (matches other mp/ modules + tests).
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from mp.lang.expr import eval_infix, eval_rpn_str, eval_rpn, HAS_C_MATH, execute_rpn_body
from mp.lang.prog import make_prog, is_program
from mp.lib.solver import find_root
from mp.plot import ascii_plot, cartesian_sample
# Phase 7 CAS (thin; eigenmath when in firmware else stub; used for .cas + direct words)
from mp.lib.cas import HAS_CAS as HAS_CAS_SYM, simplify as _cas_simplify, solve as _cas_solve, diff as _cas_diff, info as _cas_info

# Unary scientific functions for direct visible RPN apply (stepwise like "1.57 sin" after prior result).
# (Binary ops like + typically entered in one line; 1-line rpn text paths use full eval_rpn which supports all.)
from mp.lib.hybrid import (
    sin, cos, tan, sqrt, log, log10, exp, fabs, asin, acos, atan
)
_FUNC_NAMES = {"sin", "cos", "tan", "sqrt", "log", "log10", "exp", "abs", "fabs", "asin", "acos", "atan", "atan2"}


def _is_number(tok):
    return isinstance(tok, (int, float))


def _is_var_token(tok):
    """Var marker from rough/ smart tokenizers: ('var', name) or equiv. Must never be mis-treated as list data."""
    return isinstance(tok, (list, tuple)) and len(tok) == 2 and tok[0] == "var" and isinstance(tok[1], str)


def _parse_token(part):
    """Parse one raw part: quoted 'str'/'str' -> inner str (for CAS symbolic data etc),
    else float or ('var', name). Phase 7: enables 'expr' simplify etc in direct REPL entry.
    """
    p = (part or "").strip().strip(",")
    if not p:
        return None
    # quoted literal (single or double) for first-class string data (CAS expr, future use)
    if len(p) >= 2 and p[0] == p[-1] and p[0] in ("'", '"'):
        return p[1:-1]
    try:
        return float(p)
    except ValueError:
        return ("var", p)


class CalcREPL:
    """
    Thin orchestration driver (target <=200 LOC post Phase 6 refactor).
    Stack + env + LASTx register. enter() unifies infix + direct RPN words + dot cmds.
    Delegates all RPN execution to expr.execute_rpn_body (self.stack passed for visible + inline RPL).
    """

    def __init__(self):
        self.stack = []
        self.env = {}
        self.history = []
        self.last_result = None
        self.lastx = 0.0  # HP-style LASTx register: prior X captured before command that yields new result; mirrored to env['lastx'] for infix/rpn/prog resolve

    def _fmt(self, v):
        if isinstance(v, float):
            if abs(v) < 1e-12:
                return "0"
            if abs(v) > 1e6 or abs(v) < 1e-3:
                return f"{v:.6e}"
            return f"{v:.10g}"
        if isinstance(v, (list, tuple)):
            return "[" + ", ".join(self._fmt(x) for x in v) + "]"
        if is_program(v):
            nm = getattr(v, "name", None) or "<anon>"
            return f"<Prog {nm} len={len(getattr(v, 'body', []))}>"
        return str(v)

    def show_stack(self, title="stack"):
        if not self.stack:
            return f"[{title} empty]"
        lines = [f"  {i+1}: {self._fmt(v)}" for i, v in enumerate(self.stack)]
        return f"[{title} ({len(self.stack)})]\n" + "\n".join(lines)

    def show_vars(self):
        if not self.env:
            return "[vars empty]"
        items = []
        for k, v in sorted(self.env.items()):
            items.append(f"  {k} = {self._fmt(v)}")
        return "[vars]\n" + "\n".join(items)

    def enter(self, line):
        """
        Process one input line.
        - Dot-commands (.s .stack .vars .plot <expr> .solve <f> <a> <b> .help .demo .clear .prog)
        - Otherwise: try infix (algebraic, "2+3*sin(pi)", bare "42", "x") first.
          On alg-cue or no prog-name, else rpn fallback.
          Stack manip words and len/mean on list data are driven directly on visible self.stack.
        Returns the resulting scalar (or list/prog) when a value is produced, or None for cmds/side-effect only.
        Mutates self.stack / self.env. Appends to history.
        """
        line = (line or "").strip()
        if not line:
            return None
        self.history.append(line)

        # Dot-commands (REPL sugar, immediately useful, demonstrate integration)
        if line.startswith("."):
            return self._handle_dot(line)

        # Heuristic: alg cues or (no user prog name present) -> try infix first for friendly alg + C path
        parts = [p for p in line.split() if p]
        has_prog_name = any(p in self.env and is_program(self.env.get(p)) for p in parts)

        # HP LASTx discipline (REPL layer): capture current numeric top as lastx *before* this command runs
        # (LASTx holds X prior to the operation). Guard: skip lift for pure sto/rcl/lastx query lines so
        # "N sto lastx" or "lastx" query itself does not clobber a just-set register with pre-line top.
        is_sto_line = any(p in ("sto", "store", "->") for p in parts)
        is_rcl_line = any(p in ("rcl", "recall") for p in parts)
        is_lastx_line = any(p.lower() in ("lastx", "last_x", "last") for p in parts) if parts else False
        if not (is_sto_line or is_rcl_line or is_lastx_line):
            if self.stack and _is_number(self.stack[-1]):
                self.lastx = float(self.stack[-1])
                self.env["lastx"] = self.lastx
                self.env["last"] = self.lastx
                self.env["last_x"] = self.lastx  # aliases for bare-word resolve (addresses Phase 6 QA minor)
        has_alg_cue = any(c in line for c in "()^") or ("(" in line and ")" in line) or any(op + "(" in line for op in ("sin","cos","tan","sqrt","log"))
        has_infix_op = any(op in line for op in ("+", "-", "*", "/", "^"))
        if (has_alg_cue or has_infix_op) and not has_prog_name:
            try:
                val = eval_infix(line, self.env)
                if val is not None:
                    self.stack.append(float(val) if isinstance(val, (int, float)) else val)
                self.last_result = val
                if isinstance(val, (int, float)):
                    self.lastx = float(val)
                    self.env["lastx"] = self.lastx
                    self.env["last"] = self.lastx
                    self.env["last_x"] = self.lastx
                return val
            except Exception:
                pass  # fallthrough to rpn (e.g. real RPN containing operators as words)

        # Build rough toks for classification (for direct manip)
        toks = []
        for part in parts:
            if part in ("sto", "store", "->", "rcl", "recall", "dup", "drop", "swap", "over",
                        "neg", "chs", "sum", "mean", "stdev", "stats_sum", "stats_mean", "stats_stdev",
                        "len", "size", "run", "eval", "xeq", "call", "EVAL", "+", "-", "*", "/", "^",
                        "abs", "lastx", "LASTX", "last_x", "last", "simplify", "cas_simplify", "solve", "cas_solve", "diff", "cas_diff") or part in _FUNC_NAMES:
                toks.append(part)
            else:
                t = _parse_token(part)
                if t is not None:
                    toks.append(t)

        has_floats = any(isinstance(t, (int, float)) for t in toks)
        _MANIP_WORDS = ("dup","drop","swap","over","neg","chs","sto","store","->","rcl","recall","run","eval","xeq","call","EVAL","len","size","sum","mean","stdev","stats_sum","stats_mean","stats_stdev","abs","lastx","LASTX","last_x","last","simplify","cas_simplify","solve","cas_solve","diff","cas_diff")
        pure_manip = (not has_floats) and all(
            isinstance(t, str) and t in _MANIP_WORDS
            for t in toks if isinstance(t, str)
        )
        is_data_only = all(_is_number(t) or (isinstance(t, (list, tuple)) and not _is_var_token(t)) for t in toks) if toks else False
        has_nonword_str = any(isinstance(t, str) and t not in _MANIP_WORDS and t not in _FUNC_NAMES for t in toks)
        word_only = not has_floats and all(isinstance(t, str) for t in toks)
        if pure_manip or is_data_only or (word_only and not has_nonword_str):
            try:
                self._execute_visible_rpn_words(toks)
                self.last_result = self.stack[-1] if self.stack else None
                if isinstance(self.last_result, (int, float)):
                    self.lastx = float(self.last_result)
                    self.env["lastx"] = self.lastx
                    self.env["last"] = self.lastx
                    self.env["last_x"] = self.lastx
                return self.last_result
            except Exception:
                pass

        # Special: support documented "[ body ] 'name' sto" (and variants) by creating Program in REPL layer
        if "[" in line and any(s in line for s in (" sto", " store", " ->", "sto ", "store ", "-> ")):
            try:
                p = self._maybe_make_prog_from_text(line)
                if p is not None:
                    self.last_result = p
                    return p
            except Exception:
                pass

        # value rpn (or mixed) via *smart* eval (builds lists from [], collapses nums for sum/len one-liners, uses eval_rpn)
        try:
            val = self._eval_rpn_text(line)
            if val is not None:
                if not self.stack or self.stack[-1] != val:
                    if not isinstance(val, (list, tuple)) and not is_program(val):
                        self.stack.append(float(val) if isinstance(val, (int, float)) else val)
                    else:
                        self.stack.append(val)
            self.last_result = val
            if isinstance(val, (int, float)):
                self.lastx = float(val)
                self.env["lastx"] = self.lastx
                self.env["last"] = self.lastx
                self.env["last_x"] = self.lastx
            # sync dedicated lastx from env in case this line did a core sto lastx (e.g. "99 sto lastx" via _eval path not visible sto handler)
            if "lastx" in self.env and _is_number(self.env.get("lastx")):
                self.lastx = float(self.env["lastx"])
            return val
        except Exception as e_rpn:
            if "empty stack at end" in str(e_rpn):
                self.last_result = None
                return None
            # last try compact infix
            try:
                val = eval_infix(line, self.env)
                if val is not None:
                    self.stack.append(float(val) if isinstance(val, (int, float)) else val)
                self.last_result = val
                if isinstance(val, (int, float)):
                    self.lastx = float(val)
                    self.env["lastx"] = self.lastx
                    self.env["last"] = self.lastx
                    self.env["last_x"] = self.lastx
                return val
            except Exception as e2:
                raise ValueError(f"enter failed (tried rpn then infix): {e_rpn} / {e2}") from e_rpn

    def _execute_visible_rpn_words(self, toks):
        """Thin REPL-visible orchestration over the canonical expr.execute_rpn_body (Phase 6 dedup).

        Preserves: early list-data collection for "N N N stats" one-liners (REPL convenience),
        LASTx pre-mirror so body resolve sees dedicated register + post-sync after sto lastx etc,
        and direct manip on live self.stack for stepwise words.

        All dispatch (dup/drop/sto/rcl/unaries/atan2/stats/len/run/prog-by-name) now delegated;
        REPL lastx/env mirroring and the data-list special case are the only additions here.
        This collapses the prior ~141 LOC duplicate of _execute_rpn_body.
        """
        # nums-only or data list: collect/push as single list entry *only if 2+ nums* (so "1 2 3 4" -> list for stats; bare "42" or "7" stays scalar)
        # Exclude var marker tuples (('var', name)) -- they must resolve via name path, not become data lists (was source of silent corruption for bare "pi"/"a+0.5" compact etc).
        if toks and all(_is_number(t) or (isinstance(t, (list, tuple)) and not _is_var_token(t)) for t in toks):
            nums = [float(t) for t in toks if _is_number(t)]
            if len(nums) >= 2:
                self.stack.append(nums)
            elif len(nums) == 1:
                self.stack.append(nums[0])
            elif len(toks) == 1 and isinstance(toks[0], (list, tuple)) and not _is_var_token(toks[0]):
                self.stack.append(list(toks[0]))
            return

        # Pull latest dedicated LASTx from env (core _eval/infix paths or sto lastx may have written env since last visible use;
        # e.g. "99 sto lastx" via rpn-text path sets env but not self.lastx). Then publish to env for body resolve.
        # lastx is REPL-specific register; core body only knows env.
        if "lastx" in self.env and _is_number(self.env.get("lastx")):
            self.lastx = float(self.env["lastx"])
        if _is_number(self.lastx):
            self.env["lastx"] = self.lastx
            self.env["last"] = self.lastx
            self.env["last_x"] = self.lastx  # publish aliases so bare "last" resolves via execute_rpn_body bare-str path (Phase 6 QA minor addressed)

        # Delegate to single source of truth (expr). Body executes *on our live stack* for authentic RPL inline semantics
        # (e.g. "run" of prog or bare prog name now mutates visible stack directly instead of fresh+append-top).
        execute_rpn_body(toks, self.stack, self.env)

        # Post-sync LASTx dedicated from any sto lastx (or lastx-producing ops) performed by body.
        if "lastx" in self.env and _is_number(self.env.get("lastx")):
            self.lastx = float(self.env["lastx"])
            self.env["last"] = self.lastx
            self.env["last_x"] = self.lastx

    def _build_smart_tokens(self, line):
        """Tokenize rpn text, turning [ ... ] into embedded list tokens (for stats + prog bodies)."""
        parts = [p for p in line.strip().split() if p]
        toks = []
        i = 0
        while i < len(parts):
            p = parts[i]
            if p == "[":
                lst = []
                i += 1
                while i < len(parts) and parts[i] != "]":
                    pp = parts[i].strip().strip(",").strip("'\"")
                    if not pp: i += 1; continue
                    try: lst.append(float(pp))
                    except ValueError: lst.append(pp)
                    i += 1
                if i < len(parts) and parts[i] == "]": i += 1
                toks.append(lst)
                continue
            pc = p.strip(",").strip()
            if pc in ("sto", "store", "->", "rcl", "recall", "dup", "drop", "swap", "over", "neg", "chs", "sum", "mean", "stdev", "stats_sum", "stats_mean", "stats_stdev", "len", "size", "run", "eval", "xeq", "call", "EVAL", "+", "-", "*", "/", "^", "abs", "lastx", "LASTX", "last_x", "last", "simplify", "cas_simplify", "solve", "cas_solve", "diff", "cas_diff") or pc in _FUNC_NAMES:
                toks.append(pc)
            else:
                t = _parse_token(p)
                if t is not None:
                    toks.append(t)
            i += 1
        # normalize list name sto -> list sto name for engine
        for ii in range(len(toks)-2):
            if isinstance(toks[ii], (list,tuple)) and isinstance(toks[ii+2], str) and toks[ii+2] in ("sto","store","->"):
                nm = toks[ii+1]; st = toks[ii+2]; toks[ii+1]=st; toks[ii+2]=nm; break
        return toks

    def _eval_rpn_text(self, line):
        toks = self._build_smart_tokens(line)
        if not toks: return None
        list_ops = ("sum","mean","stdev","stats_sum","stats_mean","stats_stdev","len","size")
        if isinstance(toks[-1], str) and toks[-1] in list_ops:
            op = toks.pop()
            data = []
            while toks and _is_number(toks[-1]):
                data.insert(0, toks.pop())
            if data: toks.append(data)
            toks.append(op)
        return eval_rpn(toks, self.env)

    def _maybe_make_prog_from_text(self, line):
        toks = self._build_smart_tokens(line)
        for ii in range(len(toks)-2):
            v = toks[ii]
            if isinstance(v, (list, tuple)):
                for off in (1, 2):
                    if ii + off >= len(toks): continue
                    op = toks[ii + off]
                    if isinstance(op, str) and op in ("sto", "store", "->"):
                        nt = toks[ii + 1] if off == 2 else (toks[ii + 2] if ii + 2 < len(toks) else None)
                        if isinstance(nt, tuple) and nt[0] == "var": name = nt[1]
                        elif isinstance(nt, str): name = nt.strip("'\"")
                        else: continue
                        body = list(v)
                        if any(not _is_number(x) for x in body):
                            return make_prog(name, body, env=self.env)
                        return None
        return None

    def _handle_dot(self, line):
        parts = line.split(None, 1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd in (".s", ".stack"):
            print(self.show_stack())
            return None
        if cmd in (".v", ".vars"):
            print(self.show_vars())
            return None
        if cmd == ".clear":
            self.stack.clear()
            print("[stack cleared]")
            return None
        if cmd == ".help":
            print(self._help_text())
            return None
        if cmd == ".demo":
            return self._run_internal_demo()
        if cmd == ".plot":
            if not arg:
                print("usage: .plot <infix-or-rpn-or-progname>")
                return None
            try:
                pts = cartesian_sample(arg, -6.28, 6.28, n=48, env=self.env)
                print(ascii_plot(pts, width=48, height=12, title=arg[:32]))
            except Exception as e:
                print(f"plot error: {e}")
            return None
        if cmd == ".solve":
            toks = arg.split()
            if len(toks) < 3:
                print("usage: .solve <f-expr-or-prog> <lo> <hi>")
                return None
            fspec = toks[0]
            try:
                a = float(toks[1])
                b = float(toks[2])
                if fspec in self.env and is_program(self.env[fspec]):
                    fspec = self.env[fspec]
                root = find_root(fspec, a, b, env=self.env)
                self.stack.append(root)
                self.last_result = root
                if isinstance(root, (int, float)):
                    self.env["lastx"] = float(root)
                    self.env["last"] = float(root)
                    self.env["last_x"] = float(root)
                print(f"root ~ {self._fmt(root)}  (pushed to stack; env may have side-effects)")
                return root
            except Exception as e:
                print(f"solve error: {e}")
                return None
        if cmd == ".prog":
            toks = arg.split()
            if len(toks) < 2:
                print("usage: .prog <name> <rpn tokens...>")
                return None
            name = toks[0]
            body = []
            for t in toks[1:]:
                try:
                    body.append(float(t))
                except ValueError:
                    body.append(t)
            p = make_prog(name, body, env=self.env)
            # stored {p}  (debug removed for clean demo output)
            return p
        if cmd == ".cas":
            # Phase 7: thin CAS surface via dot (e.g. .cas simplify <expr> or bare .cas <expr> for implicit simplify)
            # Support info/version/help explicitly; avoid treating them as expr for simplify.
            dparts = [p for p in arg.split()]
            sub = (dparts[0].lower() if dparts else "")
            rest = " ".join(dparts[1:]) if len(dparts) > 1 else ""
            try:
                if sub in ("info", "version"):
                    inf = _cas_info()
                    print("cas info:", inf)
                    return inf
                if sub in ("help",):
                    print("cas: simplify|diff|solve <expr> [var]; quoted strings supported in main entry e.g. 'x+x' simplify")
                    return None
                if sub in ("simplify", "cas_simplify"):
                    expr = rest or (arg if sub == "" else "")
                    res = _cas_simplify(expr)
                    self.stack.append(res)
                    print(f"cas: {res}")
                    return res
                if sub in ("solve", "cas_solve"):
                    toks = (rest or "").split() or ([arg] if arg and sub == "" else [])
                    eq = toks[0] if toks else (arg if not sub else "")
                    var = toks[1] if len(toks) > 1 else "x"
                    res = _cas_solve(eq, var)
                    self.stack.append(res)
                    print(f"cas: {res}")
                    return res
                if sub in ("diff", "cas_diff"):
                    toks = (rest or "").split() or ([arg] if arg and sub == "" else [])
                    arg0 = toks[0] if toks else (arg if not sub else "")
                    v = toks[1] if len(toks) > 1 else "x"
                    res = _cas_diff(arg0, v)
                    self.stack.append(res)
                    print(f"cas: {res}")
                    return res
                # default: implicit simplify for ".cas <expr>" (no recognized verb as first word)
                if arg:
                    res = _cas_simplify(arg)
                    self.stack.append(res)
                    print(f"cas: {res}")
                    return res
            except Exception as e:
                print(f"cas error: {e}")
            return None
        print(f"unknown cmd {cmd}  (try .help)")
        return None

    def _help_text(self):
        return (
            "SuperCalc.OG REPL (phase7 inc2 CAS + nits)\n"
            "  algebraic: 2+3*sin(pi/2)   |   2^3 + sqrt(9)\n"
            "  rpn/stack:  2 3 + dup *    |   rcl x 2 *   |   dup drop swap over\n"
            "  sto/rcl:    5 sto x        |   rcl x\n"
            "  lastx/abs:  2+3  lastx *    |   -4 abs     (HP LASTx = prior X before cmd; abs on stack; last/last_x aliases too)\n"
            "  progs:      .prog dbl 2 *  then  3 rcl dbl run\n"
            "  cas:        'x+x' simplify |   .cas simplify x^2+2*x+1  |  .cas solve x^2-2 x\n"
            "              RPN solve note: push <eq> <var> solve  (e.g. 'x^2-25' 'x' solve); .cas form clearer for arg order\n"
            "  cmds: .s .stack .v .vars .plot <f> .solve <f> <a> <b> .prog <n> <body...> .cas ... .demo .clear .help\n"
            "  solve/plot observe 'x' and sto side-effects (RPL)\n"
        )

    def batch_run(self, lines, echo=False):
        """Feed multiple lines (for tests/demos). Returns list of enter() results."""
        results = []
        for ln in lines:
            if echo:
                print(f"> {ln}")
            try:
                res = self.enter(ln)
                results.append(res)
            except Exception as e:
                results.append(e)
                if echo:
                    print(f"!! {e}")
        return results

    def _run_internal_demo(self):
        """Scripted tour used by .demo and run_demo(). Returns summary string."""
        out = []
        # 1. basic infix + stack
        self.enter("2 + 3 * 4")
        out.append("infix: 2+3*4 => " + self._fmt(self.stack[-1]))

        # lastx (HP): after result, entering new cmd lifts prior X into lastx; "lastx" pushes it
        self.enter("lastx")
        out.append("lastx after infix (pre-lift): " + self._fmt(self.stack[-1]))
        self.enter("-5 abs")
        out.append("abs(-5): " + self._fmt(self.stack[-1]))

        # 2. list data + stats (Phase4) -- push list object (text [] literals not in parser scope)
        self.stack.append([1.0, 2.0, 3.0, 4.0])
        self.enter("len")
        out.append("list len: " + self._fmt(self.stack[-1]))
        self.stack.append([1.0, 2.0, 3.0, 4.0])
        self.enter("sum")
        out.append("sum on list: " + self._fmt(self.stack[-1]))

        # 3. first-class prog (Phase2) + sto/rcl via .prog helper
        self.enter(".prog dbl 2 *")
        self.enter("7 rcl dbl run")
        out.append("prog dbl via rcl+run: " + self._fmt(self.stack[-1]))

        # 4. solver on prog body (Phase4) with side effect
        p = make_prog("quad", [("var", "x"), 2, "pow", 2, "-"], env=self.env)
        try:
            root = find_root(p, 1.0, 2.0, env=self.env)
            self.stack.append(root)
            out.append("solve prog x^2-2: ~" + self._fmt(root) + " (last_x=" + self._fmt(self.env.get("x")) + ")")
        except Exception as e:
            out.append("solve err: " + str(e))

        # 5. ascii plot (Phase3)
        pts = cartesian_sample("sin(x)", -3.14, 3.14, n=16, env=self.env)
        out.append("ascii plot sin(x) produced " + str(len(pts)) + " pts")

        # 6. hybrid visibility
        out.append("hybrid C math: " + str(HAS_C_MATH))

        # 7. CAS (Phase 7 inc2): exercises thin cas layer + Symbolic results (eigenmath or stub on host)
        # Quoted literal + word now supported: e.g. enter("'x+x' simplify")
        self.stack.append("x+x")
        cres = self.enter("simplify")
        out.append("cas simplify stub: " + str(cres)[:40])
        # also demonstrate direct quoted syntax (now supported)
        qcas = self.enter("'x^2' diff")
        out.append("cas quoted diff: " + str(qcas)[:40])
        try:
            cinfo = _cas_info()
            out.append("cas info has=" + str(cinfo.get("has_cas")))
        except Exception:
            pass

        summary = "DEMO: " + " | ".join(out)
        print(summary)
        return summary

    def __repr__(self):
        return f"<CalcREPL stack={len(self.stack)} vars={len(self.env)}>"


def run_demo():
    """Run the built-in demo tour (exercises expr + prog + solver + stats + plot + cas)."""
    r = CalcREPL()
    print("=== SuperCalc.OG Phase 7 REPL demo (CAS inc2) ===")
    r._run_internal_demo()
    print("=== end demo (stack now has results; .s to inspect) ===")
    print(r.show_stack("final demo stack"))


def batch_run_demo_lines(lines, echo=True):
    """Convenience for external tests."""
    r = CalcREPL()
    return r.batch_run(lines, echo=echo)


if __name__ == "__main__":
    run_demo()
