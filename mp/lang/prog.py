"""
SuperCalc.OG — Phase 2 programmable language skeleton (first-class programs).

RPL-inspired: programs are first-class objects that can be stored in variables (sto/rcl),
passed around, and executed. For this inc1, bodies are RPN token lists (reusing the
Phase 1 expr machinery for parsing/execution). Execution uses the shared-stack
_execute_rpn_body (via eval_rpn) so programs run "inline" on the caller's stack + env
for authentic RPL semantics (results left on stack, side effects visible).

Thin boundary preserved:
- MPy (here + expr): program objects, source management, high-level "run" semantics.
- C (future picocalc_vm): will own fast interpretation, bytecode, control flow dispatch,
  locals frame, call/return stack. This skel introduces the module placeholder + hybrid glue.

No control structures (IF/THEN, loops) or locals syntax (->) in inc1 — those come in
later increments once the basic first-class + exec model is solid and hardware-proven.

Offline-first. Double baseline. 320x320 later for UI.

Public API:
  from mp.lang.prog import Program, make_prog, run_prog, is_program, EVAL_ALIASES
  p = make_prog("demo", [2, 3, "+"], env)   # stores in env too if passed
  res = run_prog(p)                          # or run_prog("demo", env)
  # from rpn:  [ "rcl", "demo", "run" ]  works via expr.eval_rpn after import side-effect

Integration: expr.eval_rpn and eval_rpn_str recognize the EVAL_ALIASES ("run"/"eval"/"xeq")
ops and will execute a Program found on the top of stack (or resolved via rcl) using the
shared body executor. Duck-types on having a .body attribute + exact isinstance.
"""
# MicroPython / device compatibility: no 'from __future__ annotations' and no 'typing'
# imports (guarded or bare) at all. Type annotations stripped from runtime sigs below
# so importing this module (transitively used by solver/calc_repl/plot/apps) succeeds
# on plain firmware without a typing module. (Addresses Phase 5 QA Blocker.)
# expr imports these at load (see mp/lang/expr.py). We do not import expr at top level
# to keep load order clean; inside run() we import locally for the top-level driver.

class Program:
    """First-class program object.

    body: list of RPN tokens (numbers, op strs, ('var', name), or nested Programs).
    source: optional original text for editing/re-display (future use).
    name: optional symbolic name (mostly for __repr__ and catalog).
    Constructor supports test-friendly forms:
        Program(body_list, name="foo")
        Program(body_list)
        Program(name="foo", body=...)
    """
    def __init__(self, body=None, name=None, source=None, **kw):
        # Flexible binding for pre-written tests + clean API
        if body is None and "body" in kw:
            body = kw["body"]
        if name is None and "name" in kw:
            name = kw["name"]
        if isinstance(body, (list, tuple)):
            self.body = list(body)
            self.name = name
        elif isinstance(body, str) and name is None:
            # called as Program("name", body_list?) rare; treat first as name
            self.name = body
            b2 = kw.get("body")
            self.body = list(b2) if isinstance(b2, (list, tuple)) else []
        else:
            self.body = list(body) if isinstance(body, (list, tuple)) else []
            self.name = name
        self.source = source

    def run(self, env=None):
        """Execute the program body (inline shared stack+env via expr) and return result."""
        from .expr import eval_rpn
        return eval_rpn(self.body, env)

    def __repr__(self):
        nm = self.name or "<anon>"
        return f"<Program {nm} len={len(self.body)}>"

    def __eq__(self, other):
        if not isinstance(other, Program):
            return False
        return (self.name == other.name and self.body == other.body and
                self.source == other.source)


def make_prog(name, body, env=None, source=None):
    """Create a Program and optionally store it in env (first-class STO pattern)."""
    p = Program(body, name=name, source=source)
    if env is not None and name is not None:
        env[name] = p
    return p


def run_prog(p_or_name, env=None):
    """Run a program given the object or its name (looked up in env)."""
    if isinstance(p_or_name, str):
        if env is None or p_or_name not in env:
            raise ValueError(f"undefined program: {p_or_name}")
        p = env[p_or_name]
    else:
        p = p_or_name
    if not is_program(p):
        raise ValueError("run_prog target must be a Program or name of one")
    if hasattr(p, "run"):
        return p.run(env)
    from .expr import eval_rpn
    return eval_rpn(p.body, env)


def is_program(obj):
    """Duck-type + exact check used by expr shared executor and rpn dispatch."""
    if isinstance(obj, Program):
        return True
    return (hasattr(obj, "body") and
            isinstance(getattr(obj, "body", None), (list, tuple)))


def store_program(name, prog, env):
    """Store a program object under name in env (first-class STO helper matching test expectations)."""
    if env is not None:
        env[name] = prog
    if hasattr(prog, "name") and getattr(prog, "name", None) is None:
        try:
            prog.name = name
        except Exception:
            pass
    return prog


# Aliases recognized as "execute the program object on top of stack" (RPL EVAL/XEQ).
EVAL_ALIASES = {"run", "eval", "xeq", "call", "EVAL"}

__all__ = ["Program", "make_prog", "run_prog", "store_program", "is_program", "EVAL_ALIASES"]
