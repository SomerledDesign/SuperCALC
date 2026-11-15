"""SuperCalc.OG - CAS surface over the Eigenmath C module (2026-11-14).

Firmware exposes eigenmath.EigenMath(heap_bytes) with .run(cmd, True) -> bytearray.
The engine is created lazily on the first CAS command (picocalc.eigen) and freed
again with release(); a command that runs out of engine memory is retried once on
a bigger engine when free RAM allows.

Launcher commands (see command()):
  simplify E | expand E | factor E | d E[,x[,n]] | int E[,x[,a,b]]
  solve E[=F][,x] | taylor E[,x,n[,a]] | eig <raw eigenmath> | cas [clear|free]
RPN words kept for calc_repl: simplify / solve / diff -> Symbolic results.
On a host without eigenmath everything falls back to "stub:" strings.
"""

import gc

HAS_CAS = False
_CAS_BACKEND = "stub (no eigenmath in firmware)"
_EIGEN = None          # the eigenmath module
# Engine lifecycle (firmware 20261114b+): created lazily on the first CAS command,
# freed with release() (SuperCalc exit, before 12C/plot, "cas free"). Start sizes
# (KB) are tried largest first while keeping _RESERVE free; on "out of memory" a
# command is retried once on a bigger engine (_GROW) if RAM allows.
_SIZES = (96,)              # 20261114c firmware: 96K is plenty for normal algebra
_GROW = (160, 128)          # one retry on a bigger engine when a command runs out
_RESERVE = 40 * 1024        # keep free beside the engine for SuperCalc's own work
_GROW_RESERVE = 24 * 1024   # bigger engines are a one-off; released before 12C/plot
# (12C sheets and plot no longer need room beside the engine: SuperCalc frees it first.)
MAXDEG = 24


class Symbolic(str):
    """Symbolic result on the RPL stack (str subclass, keeps sto/rcl/.s working)."""
    pass


class CASError(Exception):
    pass


def _try_import_eigen():
    # Only the real C module. The old candidate list included "cas", which could
    # import this very file (or /sd/... copies) and report a fake backend.
    global HAS_CAS, _CAS_BACKEND, _EIGEN
    try:
        import eigenmath as mod
        if hasattr(mod, "EigenMath"):
            _EIGEN = mod
            HAS_CAS = True
            _CAS_BACKEND = "eigenmath"
            return
    except Exception:
        pass
    HAS_CAS = False
    _CAS_BACKEND = "stub (no eigenmath in firmware)"


_try_import_eigen()


def _holder():
    try:
        import picocalc
        return picocalc
    except Exception:
        return None


def _min_heap():
    return getattr(_EIGEN, "MIN_HEAP", 65536) if _EIGEN is not None else 65536


def _mem_free():
    mf = getattr(gc, "mem_free", None)
    return mf() if mf is not None else None


def _get():
    h = _holder()
    if h is not None:
        return getattr(h, "eigen", None), getattr(h, "eigen_heap", 0)
    return globals().get("_ENG"), globals().get("_ENG_N", 0)


def _set(e, n):
    h = _holder()
    if h is not None:
        h.eigen = e
        h.eigen_heap = n
    else:
        globals()["_ENG"] = e
        globals()["_ENG_N"] = n


def heap_size():
    return _get()[1] if _get()[0] is not None else 0


def release():
    """Free the engine's heap (all CAS variables are lost). Safe to call any time."""
    e, n = _get()
    _set(None, 0)
    if e is not None:
        try:
            e.deinit()
        except Exception:
            pass
        e = None
    gc.collect()
    return n


def _create(sizes, reserve):
    lo = _min_heap()
    for kb in sizes:
        n = max(kb * 1024, lo)
        gc.collect()
        mf = _mem_free()
        if mf is not None and mf - n < reserve:
            continue
        try:
            e = _EIGEN.EigenMath(n)
        except (MemoryError, ValueError):
            continue
        _set(e, n)
        return e
    return None


def engine():
    """Return the shared EigenMath instance, creating it on first use."""
    if not HAS_CAS:
        raise CASError("no eigenmath in this firmware")
    e = _get()[0]
    if e is not None:
        return e
    e = _create(_SIZES, _RESERVE) or _create((80, 64), 16 * 1024)
    if e is None:
        mf = _mem_free() or 0
        raise CASError("not enough free RAM for the CAS engine (%dK free)" % (mf // 1024))
    return e


def grow():
    """Swap in a bigger engine (variables are lost). True if it got bigger."""
    if not HAS_CAS:
        return False
    old = heap_size()
    release()
    bigger = tuple(kb for kb in _GROW if kb * 1024 > old)
    if bigger and _create(bigger, _GROW_RESERVE) is not None:
        return True
    if old:
        _create((old // 1024,) + _SIZES, 0)   # put back a working engine
    return False


class _OOM(CASError):
    pass


_LAST_TRY = True   # False during command()'s first pass (it may grow and retry)


_OOM_MSG = "ran out of CAS memory (too big, or no closed form)"


def run(cmd):
    """Run raw Eigenmath text, return its printed result (str). Raise CASError on 'Stop:'."""
    for attempt in (0, 1):
        e = engine()
        try:
            out = e.run(cmd, True)
            break
        except ValueError:
            # deinitialized, or another EigenMath took over: take it back / recreate
            try:
                e.reset()
                continue
            except Exception:
                _set(None, 0)
                if attempt:
                    raise CASError("CAS engine was lost; try again")
        except MemoryError:
            try:
                e.reset()
            except Exception:
                release()
            raise _OOM(_OOM_MSG)
    s = bytes(out).decode() if out is not None else ""
    i = s.find("Stop:")
    if i >= 0:
        msg = s[i + 5:].strip()
        if "atoms" in msg or "memory" in msg or "heap" in msg:
            raise _OOM(_OOM_MSG)
        raise CASError(msg)
    return s.strip()


def version():
    return _CAS_BACKEND


def info():
    return {"has_cas": HAS_CAS, "backend": _CAS_BACKEND}


# ---------------------------------------------------------------- rationals
def _gcd(a, b):
    a = -a if a < 0 else a
    b = -b if b < 0 else b
    while b:
        a, b = b, a % b
    return a


def _q(n, d=1):
    if d < 0:
        n, d = -n, -d
    g = _gcd(n, d) or 1
    return (n // g, d // g)


def _qadd(a, b):
    return _q(a[0] * b[1] + b[0] * a[1], a[1] * b[1])


def _qmul(a, b):
    return _q(a[0] * b[0], a[1] * b[1])


def _qdiv(a, b):
    return _q(a[0] * b[1], a[1] * b[0])


def _qstr(a):
    return str(a[0]) if a[1] == 1 else "%d/%d" % a


def _parse_q(s):
    """'-3/4' -> (-3, 4); anything non-rational -> None."""
    s = s.replace(" ", "")
    if not s:
        return None
    neg = s[0] == "-"
    if neg:
        s = s[1:]
    p = s.split("/")
    if len(p) > 2:
        return None
    for t in p:
        if not t or not t.isdigit():
            return None
    n = int(p[0])
    d = int(p[1]) if len(p) == 2 else 1
    if d == 0:
        return None
    return _q(-n if neg else n, d)


# ---------------------------------------------------------------- polynomials
def _coeffs(expr, v):
    """Rational coefficients [c0..cn] of expr in v, or None if not such a polynomial."""
    run("zzq=(" + expr + ")")
    cs = []
    fact = 1
    try:
        for k in range(MAXDEG + 2):
            if k:
                fact *= k
            c = _parse_q(run("eval(zzq,%s,0)/%d" % (v, fact)))
            if c is None:
                return None
            cs.append(c)
            run("zzq=d(zzq,%s)" % v)
            if run("zzq+0") == "0":
                break
        else:
            return None
    except _OOM:
        raise
    except CASError:
        return None
    finally:
        try:
            run("zzq=quote(zzq)")
        except Exception:
            pass
    while len(cs) > 1 and cs[-1][0] == 0:
        cs.pop()
    return cs


def _horner(cs, r):
    acc = (0, 1)
    for c in reversed(cs):
        acc = _qadd(_qmul(acc, r), c)
    return acc


def _deflate(cs, r):
    """Divide poly (low->high coeffs) by (x - r); return quotient."""
    n = len(cs) - 1
    out = [None] * n
    acc = (0, 1)
    for i in range(n, 0, -1):
        acc = _qadd(_qmul(acc, r), cs[i])
        out[i - 1] = acc
    return out


def _rational_roots(expr, v):
    s = run("roots(" + expr + "," + v + ")")
    if not s:
        return []
    if s[0] == "(" and s[-1] == ")":
        s = s[1:-1]
    rs = []
    for t in s.split(","):
        q = _parse_q(t)
        if q is not None:
            rs.append(q)
    return rs


def _split_roots(expr, v, cs):
    """-> ([(root, mult)], remaining_coeffs) using exact rational roots."""
    found = []
    for r in _rational_roots(expr, v):
        m = 0
        while len(cs) > 1 and _horner(cs, r)[0] == 0:
            cs = _deflate(cs, r)
            m += 1
        if m:
            found.append((r, m))
    return found, cs


def _term(c, k, v, first):
    n, d = c
    neg = n < 0
    a = (-n, d) if neg else (n, d)
    sign = ("-" if neg else "") if first else (" - " if neg else " + ")
    if k == 0:
        return sign + _qstr(a)
    xs = v if k == 1 else "%s^%d" % (v, k)
    if a == (1, 1):
        return sign + xs
    return sign + _qstr(a) + " " + xs


def _pstr(cs, v):
    out = ""
    for k in range(len(cs) - 1, -1, -1):
        if cs[k][0] != 0:
            out += _term(cs[k], k, v, not out)
    return out or "0"


def _content(cs):
    """Rational c so that cs/c has coprime integer coeffs and positive leading coeff."""
    g = 0
    den = 1
    for c in cs:
        den = den * c[1] // (_gcd(den, c[1]) or 1)
    for c in cs:
        g = _gcd(g, c[0] * (den // c[1]))
    if g == 0:
        return (1, 1)
    c = _q(g, den)
    if cs[-1][0] < 0:
        c = (-c[0], c[1])
    return c


# ---------------------------------------------------------------- numeric roots
def _fmt(x):
    if isinstance(x, complex):
        re_, im = x.real, x.imag
        if abs(im) <= 1e-12 * max(1.0, abs(re_)):
            return _fmt(re_)
        if abs(re_) <= 1e-12 * max(1.0, abs(im)):
            re_ = 0.0
        s = "-" if im < 0 else "+"
        a = abs(im)
        ims = "i" if abs(a - 1.0) < 1e-15 else "%.12g i" % a
        if re_ == 0.0:
            return ("-" if im < 0 else "") + ims
        return "%.12g %s %s" % (re_, s, ims)
    if abs(x) < 1e-300:
        return "0"
    return "%.15g" % x


def _num_roots(cs):
    """All roots of a rational-coefficient polynomial in doubles (Durand-Kerner + Newton)."""
    a = [c[0] / c[1] for c in cs]
    n = len(a) - 1
    lead = a[-1]
    a = [x / lead for x in a]
    z = [complex(0.4, 0.9) ** k for k in range(n)]

    def p(x, cs=a):
        acc = 0j
        for c in reversed(cs):
            acc = acc * x + c
        return acc

    for _ in range(500):
        delta = 0.0
        for i in range(n):
            den = 1 + 0j
            for j in range(n):
                if i != j:
                    den *= z[i] - z[j]
            if den == 0:
                den = 1e-12
            step = p(z[i]) / den
            z[i] -= step
            delta = max(delta, abs(step))
        if delta < 1e-15:
            break
    da = [a[k] * k for k in range(1, n + 1)]
    for i in range(n):
        for _ in range(3):
            dp = p(z[i], da)
            if dp == 0:
                break
            z[i] -= p(z[i]) / dp
    z.sort(key=lambda w: (abs(w.imag) > 1e-9, w.real, w.imag))
    return z


# ---------------------------------------------------------------- argument helpers
def _args(rest):
    """Split 'expr, x, 2' on top-level commas."""
    out = []
    depth = 0
    cur = ""
    for ch in rest:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


def _equation(e):
    e = e.replace("==", "=")
    if "=" in e:
        l, r = e.split("=", 1)
        return "(" + l + ")-(" + r + ")"
    return e


def _approx(s):
    """Append a 15-digit value for a plain rational answer like 7/3."""
    q = _parse_q(s)
    if q is not None and q[1] != 1:
        return s + "  (= %s)" % _fmt(q[0] / q[1])
    return s


# ---------------------------------------------------------------- operations
def _pmod(a, b):
    a = a[:]
    while len(a) >= len(b) and any(c[0] for c in a):
        f = _qdiv(a[-1], b[-1])
        k = len(a) - len(b)
        for i in range(len(b)):
            a[k + i] = _qadd(a[k + i], _qmul((-f[0], f[1]), b[i]))
        a.pop()
    while len(a) > 1 and a[-1][0] == 0:
        a.pop()
    return a or [(0, 1)]


def _pdiv(a, b):
    a = a[:]
    out = [(0, 1)] * (len(a) - len(b) + 1)
    while len(a) >= len(b):
        f = _qdiv(a[-1], b[-1])
        k = len(a) - len(b)
        out[k] = f
        for i in range(len(b)):
            a[k + i] = _qadd(a[k + i], _qmul((-f[0], f[1]), b[i]))
        a.pop()
    return out


def _pgcd(a, b):
    while len(b) > 1 or b[0][0]:
        a, b = b, _pmod(a, b)
    return a


def _cancel(e, v="x"):
    """(x^2-1)/(x-1) -> x + 1: cancel common polynomial factors of numerator/denominator."""
    den = run("denominator(" + e + ")")
    if den == "1" or not den:
        return None
    nc = _coeffs("numerator(" + e + ")", v)
    dc = _coeffs(den, v)
    if not nc or not dc or len(dc) < 2:
        return None
    g = _pgcd(nc, dc)
    if len(g) > 1:
        nc = _pdiv(nc, g)
        dc = _pdiv(dc, g)
    if len(dc) == 1:
        return _pstr([_qdiv(c, dc[0]) for c in nc], v)
    c = _content(dc)
    nc = [_qdiv(x, c) for x in nc]
    dc = [_qdiv(x, c) for x in dc]
    n = _pstr(nc, v)
    return ("(" + n + ")" if len(nc) > 1 and " " in n else n) + " / (" + _pstr(dc, v) + ")"


def do_simplify(e):
    c = None
    if "/" in e:
        # rational function in x: cancel common factors exactly (cheap, and
        # Eigenmath's simplify() can run out of atoms on these)
        try:
            c = _cancel(e)
        except CASError:
            c = None
    try:
        s = run("simplify(" + e + ")")
    except CASError as ex:
        if c:
            return c
        if "memory" not in str(ex):
            raise
        if not _LAST_TRY:
            raise   # command() retries on a bigger engine first
        return run("(" + e + ")") + "\n  (left as is: simplify ran out of CAS memory)"
    if c and len(c) <= len(s):
        return c
    return s


def do_expand(e):
    return run("(" + e + ")")


def do_diff(e, v="x", n=None):
    return run("d(" + e + "," + v + ("," + n if n else "") + ")")


def do_integral(e, v="x", a=None, b=None):
    if a is not None and b is not None:
        s = run("defint(" + e + "," + v + "," + a + "," + b + ")")
        try:
            f = run("float(" + s + ")")
            if f and f != s:
                q = _parse_q(s)
                return s + "  (= %s)" % (_fmt(q[0] / q[1]) if q else f)
        except CASError:
            pass
        return s
    s = _tidy_atan(run("integral(" + e + "," + v + ")"))
    return s + " + C"


def _tidy_atan(s):
    """Eigenmath prints arctan(y,x); arctan(u,1) is just arctan(u)."""
    out = []
    i = 0
    while True:
        j = s.find("arctan(", i)
        if j < 0:
            out.append(s[i:])
            return "".join(out)
        k = j + 7
        depth = 1
        comma = -1
        while k < len(s) and depth:
            ch = s[k]
            if ch in "([":
                depth += 1
            elif ch in ")]":
                depth -= 1
            elif ch == "," and depth == 1:
                comma = k
            k += 1
        if depth == 0 and comma > 0 and s[comma + 1:k - 1].strip() == "1":
            out.append(s[i:comma] + ")")
        else:
            out.append(s[i:k])
        i = k


def do_factor(e, v="x"):
    q = _parse_q(e)
    if q is not None and q[1] == 1:
        return _factor_int(q[0])
    cs = _coeffs(e, v)
    if cs is None:
        raise CASError("factor needs a polynomial in %s with numeric coefficients" % v)
    if len(cs) < 2:
        return _qstr(cs[0])
    found, rem = _split_roots(e, v, cs)
    parts = []
    for r, m in found:
        p, d = r
        lin = _pstr([(-p, 1), (d, 1)], v)
        rem = [_qdiv(c, (d ** m, 1)) for c in rem]
        if p != 0:
            lin = "(" + lin + ")"
        parts.append(lin + ("^%d" % m if m > 1 else ""))
    c = _content(rem)
    rem = [_qdiv(x, c) for x in rem]
    if len(rem) > 1:
        parts.append("(" + _pstr(rem, v) + ")" if parts or c != (1, 1) else _pstr(rem, v))
    lead = "" if c == (1, 1) else ("-" if c == (-1, 1) else _qstr(c) + " ")
    out = lead + " ".join(parts)
    if len(rem) > 2 and not found:
        out += "   (no rational roots)"
    return out


def _factor_int(n):
    if n in (0, 1, -1):
        return str(n)
    out = []
    neg = n < 0
    if neg:
        n = -n
    d = 2
    steps = 0
    while d * d <= n and steps < 200000:
        k = 0
        while n % d == 0:
            n //= d
            k += 1
        if k:
            out.append(str(d) + ("^%d" % k if k > 1 else ""))
        d += 1 if d == 2 else 2
        steps += 1
    if n > 1:
        out.append(str(n) + ("" if d * d > n else " (not fully checked)"))
    return ("-" if neg else "") + " * ".join(out)


def do_solve(e, v="x"):
    """Lines like 'x = 3'. Exact rational roots, exact quadratics, else 15-digit numeric."""
    p = _equation(e)
    cs = _coeffs(p, v)
    if cs is None:
        s = ""
        try:
            s = run("roots(" + p + "," + v + ")")
        except CASError:
            pass
        if s:
            return [v + " = " + s]
        raise CASError("solve needs a polynomial in %s with numeric coefficients (numeric root of any f: .solve f a b)" % v)
    if len(cs) < 2:
        return ["identity (always true)" if cs[0][0] == 0 else "no solution"]
    found, rem = _split_roots(p, v, cs)
    out = []
    for r, m in found:
        out.append(v + " = " + _approx(_qstr(r)) + ("   (x%d)" % m if m > 1 else ""))
    if len(rem) == 3:
        c, b, a = [_qstr(x) for x in rem]
        disc = "(%s)^2-4*(%s)*(%s)" % (b, a, c)
        nums = _num_roots(rem)
        for sg, z in zip(("-", "+"), nums):
            try:
                ex = run("(-(%s)%ssqrt(%s))/(2*(%s))" % (b, sg, disc, a))
            except CASError:
                ex = None
            if ex and ex.replace("-", "") in ("i", "1 i"):
                ex = None
            out.append(v + " = " + (ex + "  (= " + _fmt(z) + ")" if ex else _fmt(z)))
    elif len(rem) > 3:
        try:
            for z in _num_roots(rem):
                out.append(v + " ~ " + _fmt(z))
        except Exception:
            out.append(v + " ~ " + run("nroots(" + _pstr(rem, v) + "," + v + ")"))
    elif len(rem) == 2:
        out.append(v + " = " + _approx(_qstr(_q(-rem[0][0] * rem[1][1], rem[0][1] * rem[1][0]))))
    return out or ["no solution"]


def do_taylor(e, v="x", n="6", a=None):
    return run("taylor(" + e + "," + v + "," + n + ("," + a if a else "") + ")")


def status():
    if not HAS_CAS:
        return "CAS: " + _CAS_BACKEND
    if _get()[0] is None:
        mf = _mem_free()
        return "CAS: eigenmath, engine off (starts on first use%s)" % (
            ", %dK RAM free" % (mf // 1024) if mf is not None else "")
    size = heap_size()
    free = "?"
    for ln in run("status").split("\n"):
        if ln.startswith("free_count"):
            free = ln.split()[-1]
    return "CAS: eigenmath, heap %dK, %s atoms free" % (size // 1024, free)


_WORDS = {
    "simplify": "s", "simp": "s",
    "expand": "e",
    "factor": "f",
    "d": "d", "diff": "d", "deriv": "d", "derivative": "d",
    "int": "i", "integral": "i", "integrate": "i", "defint": "i",
    "solve": "v", "roots": "v",
    "taylor": "t",
    "eig": "r", "cas": "c",
}

USAGE = (
    "CAS (Eigenmath): simplify E | expand E | factor E\n"
    "  d E[,x[,n]] | int E[,x[,a,b]] | solve E[=F][,x]\n"
    "  taylor E[,x,n[,a]] | eig <raw> | cas [clear|free]"
)


def is_command(line):
    w = line.split(None, 1)
    if not w:
        return False
    k = w[0].lower()
    if k not in _WORDS:
        return False
    return len(w) == 2 or k in ("cas", "eig")


def command(line):
    """Run a launcher CAS line. Returns display text, or None if the line is not a CAS command."""
    global _LAST_TRY
    if not is_command(line):
        return None
    w = line.split(None, 1)
    op = _WORDS[w[0].lower()]
    rest = w[1].strip() if len(w) > 1 else ""
    try:
        try:
            _LAST_TRY = False
            return _command(op, rest)
        except _OOM:
            _LAST_TRY = True
            if not (grow() or op == "s"):
                raise
            return _command(op, rest)
        finally:
            _LAST_TRY = True
    except CASError as ex:
        return "! CAS: " + str(ex)
    except MemoryError:
        gc.collect()
        return "! CAS: out of memory"
    except Exception as ex:
        return "! CAS error: " + repr(ex)[:90]
    return USAGE


def _command(op, rest):
    if op == "c":
        if rest.lower() == "clear":
            if _get()[0] is not None:
                run("clear")
            gc.collect()
            return "CAS variables cleared"
        if rest.lower() in ("free", "off", "release"):
            n = release()
            return "CAS engine freed (%dK back)" % (n // 1024) if n else "CAS engine was not running"
        if rest:
            return run(rest)
        return status() + "\n" + USAGE
    if op == "r":
        if not rest:
            return USAGE
        return run(rest) or "ok"
    a = _args(rest)
    if not a:
        return USAGE
    e = a[0]
    v = a[1] if len(a) > 1 and a[1] else "x"
    if op == "s":
        return do_simplify(e)
    if op == "e":
        return do_expand(e)
    if op == "f":
        return do_factor(e, v)
    if op == "d":
        return do_diff(e, v, a[2] if len(a) > 2 else None)
    if op == "i":
        if len(a) >= 4:
            return do_integral(e, v, a[2], a[3])
        return do_integral(e, v)
    if op == "v":
        return "\n".join(do_solve(e, v))
    if op == "t":
        return do_taylor(e, v, a[2] if len(a) > 2 else "6", a[3] if len(a) > 3 else None)
    return USAGE


# ---------------------------------------------------------------- RPN words (calc_repl)
def simplify(expr):
    s = str(expr)
    if not HAS_CAS:
        return Symbolic("stub:simplify(" + s + ")")
    try:
        return Symbolic(do_simplify(s))
    except Exception as e:
        return Symbolic("cas-err:simplify:" + str(e))


def solve(eq, var="x"):
    s = str(eq)
    v = str(var)
    if not HAS_CAS:
        return Symbolic("stub:solve(" + s + ", " + v + ")")
    try:
        return Symbolic("; ".join(do_solve(s, v)))
    except Exception as e:
        return Symbolic("cas-err:solve:" + str(e))


def diff(expr, var="x"):
    if not HAS_CAS:
        return Symbolic("stub:diff(%s, %s)" % (expr, var))
    try:
        return Symbolic(do_diff(str(expr), str(var)))
    except Exception as e:
        return Symbolic("cas-err:diff:" + str(e))


__all__ = ["HAS_CAS", "Symbolic", "CASError", "version", "info", "simplify", "solve",
           "diff", "command", "is_command", "run", "engine", "release", "heap_size"]
