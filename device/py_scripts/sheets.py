# picocalc-hide  (library; launched by hp12c.py or the SuperCalc 'hp12c' command)
"""HP12C-style financial worksheets for SuperCalc (12C mode).

Plain fill-in sheets for time value of money, mortgage amortization,
loan payoff, savings, NPV/IRR, date math, percent/APR, and Black-Scholes options. This is
not an HP product and does not reproduce an HP keyboard or manual.
Formulas are the ordinary finance identities.

Cash-out-is-negative applies on the TVM sheet (same sign convention
the 12C popularized). Other sheets use positive amounts where that
is easier to type.
"""

import gc

try:
    import utime
except ImportError:
    import time as _time

    class _UTime(object):
        def ticks_ms(self):
            return int(_time.time() * 1000)

        def ticks_diff(self, a, b):
            return a - b

        def sleep_ms(self, ms):
            _time.sleep(ms / 1000.0)

    utime = _UTime()

import math

COLS = 52
ROWS = 31
FG = 15
DIM = 9
RES = 12
ERR = 6
BAR = 2
HI = 3

# PicoCalc key codes (and CSI arrows, in case a layer translates them)
_K_ESC = 0x1B
_K_ESC2 = 0xB1
_K_UP = 0xB5
_K_DOWN = 0xB6
_K_LEFT = 0xB4
_K_RIGHT = 0xB7
_K_TAB = 0x09
_K_F1 = 0x81
_K_F5 = 0x85  # PicoCalc keyboard.h KEY_F5; also CSI ESC [ 15 ~
_K_INS = 0xD1
_K_DEL = 0xD4
_K_HOME = 0xD2
_K_END = 0xD5
_K_PGUP = 0xD6
_K_PGDN = 0xD7


# ---------------------------------------------------------------------------
# Formatting / parsing (shared by math tests and the UI)
# ---------------------------------------------------------------------------

def _finite(x):
    return x == x and abs(x) < 1e300


def _cents(x):
    if x >= 0:
        return int(x * 100.0 + 0.5)
    return -int((-x) * 100.0 + 0.5)


def round_cents(x):
    return _cents(x) / 100.0


def parse_num(s):
    """Parse a field. Empty -> None. Accepts $, commas, trailing %."""
    if s is None:
        return None
    t = str(s).strip()
    if not t or t == "-" or t == "." or t == "-.":
        return None
    if t.endswith("%"):
        t = t[:-1].strip()
    if t.startswith("$"):
        t = t[1:].strip()
    t = t.replace(",", "").replace(" ", "")
    try:
        return float(t)
    except ValueError:
        raise ValueError("not a number: %s" % s)


def _commas(s):
    neg = s[:1] == "-"
    if neg:
        s = s[1:]
    if "." in s:
        a, b = s.split(".", 1)
    else:
        a, b = s, None
    parts = []
    while len(a) > 3:
        parts.append(a[-3:])
        a = a[:-3]
    parts.append(a)
    a = ",".join(reversed(parts))
    if b is not None:
        a = a + "." + b
    if neg:
        a = "-" + a
    return a


def fmt_money(v, places=2):
    if v is None:
        return ""
    if not _finite(v):
        return "n/a"
    n = 10 ** places
    if v >= 0:
        iv = int(v * n + 0.5)
    else:
        iv = -int((-v) * n + 0.5)
    neg = iv < 0
    iv = abs(iv)
    whole = iv // n
    frac = iv % n
    s = str(whole)
    if places:
        fs = str(frac)
        while len(fs) < places:
            fs = "0" + fs
        s = s + "." + fs
    s = _commas(s)
    if neg:
        s = "-" + s
    return s


def fmt_num(v, places=None):
    if v is None:
        return ""
    if not _finite(v):
        return "n/a"
    if places is not None:
        return fmt_money(v, places)
    if abs(v) < 1e-12:
        return "0"
    if abs(v) >= 1e10 or (abs(v) < 1e-4 and v != 0):
        return "%.8e" % v
    s = "%.10g" % v
    return s


def fmt_months(n):
    if n is None or not _finite(n):
        return "n/a"
    if abs(n - round(n)) < 1e-6:
        n = int(round(n))
        y, m = divmod(n, 12)
        return "%d mo  (%d y %d mo)" % (n, y, m)
    y = int(n // 12)
    m = n - 12 * y
    return "%.2f mo  (%d y %.1f mo)" % (n, y, m)


# ---------------------------------------------------------------------------
# TVM  (end / begin mode).  Unknown is one of: n, iyr, pv, pmt, fv
# iyr is a nominal annual percent; i is the periodic rate.
# ---------------------------------------------------------------------------

def tvm_i(iyr, pyr):
    if pyr is None or pyr == 0:
        raise ValueError("P/YR must be greater than 0")
    return (iyr / 100.0) / pyr


def tvm_balance(i, n, pv, pmt, fv, begin):
    """TVM equation residual; a root in i is the periodic rate."""
    if not _finite(i) or not _finite(n):
        return 1e300
    if abs(i) < 1e-16:
        return pv + pmt * n + fv
    try:
        a = (1.0 + i) ** n
    except OverflowError:
        return 1e300
    if not _finite(a):
        return 1e300 if a > 0 else -1e300
    if begin:
        pfac = pmt * (1.0 + i) * (a - 1.0) / i
    else:
        pfac = pmt * (a - 1.0) / i
    r = pv * a + pfac + fv
    if not _finite(r):
        return 1e300 if (r != r or r > 0) else -1e300
    return r


def tvm_pmt(n, i, pv, fv, begin=False):
    if n == 0:
        raise ValueError("N must not be 0")
    if abs(i) < 1e-16:
        return -(pv + fv) / n
    a = (1.0 + i) ** n
    if not _finite(a):
        raise ValueError("overflow computing payment")
    den = (a - 1.0) / i
    if begin:
        den *= (1.0 + i)
    if abs(den) < 1e-18:
        raise ValueError("cannot solve for PMT")
    return -(pv * a + fv) / den


def tvm_pv(n, i, pmt, fv, begin=False):
    if abs(i) < 1e-16:
        return -(pmt * n + fv)
    a = (1.0 + i) ** n
    if not _finite(a) or a == 0:
        raise ValueError("overflow computing PV")
    if begin:
        pfac = pmt * (1.0 + i) * (a - 1.0) / i
    else:
        pfac = pmt * (a - 1.0) / i
    return -(fv + pfac) / a


def tvm_fv(n, i, pv, pmt, begin=False):
    if abs(i) < 1e-16:
        return -(pv + pmt * n)
    a = (1.0 + i) ** n
    if not _finite(a):
        raise ValueError("overflow computing FV")
    if begin:
        pfac = pmt * (1.0 + i) * (a - 1.0) / i
    else:
        pfac = pmt * (a - 1.0) / i
    return -(pv * a + pfac)


def tvm_n(i, pv, pmt, fv, begin=False):
    if abs(i) < 1e-16:
        if abs(pmt) < 1e-18:
            raise ValueError("cannot solve for N")
        n = -(pv + fv) / pmt
        if n < 0:
            raise ValueError("N would be negative; check signs")
        return n
    if begin:
        adj = pmt * (1.0 + i)
    else:
        adj = pmt
    # a^n = (adj/i - fv) / (pv + adj/i)
    num = adj / i - fv
    den = pv + adj / i
    if abs(den) < 1e-18:
        raise ValueError("cannot solve for N")
    ratio = num / den
    if ratio <= 0:
        raise ValueError("cannot solve for N; payment may be too small")
    n = math.log(ratio) / math.log(1.0 + i)
    if not _finite(n) or n < 0:
        raise ValueError("cannot solve for N")
    return n


def _find_root(f, lo, hi, flo=None, fhi=None, tol=1e-14, maxiter=80):
    if flo is None:
        flo = f(lo)
    if fhi is None:
        fhi = f(hi)
    if not _finite(flo) or not _finite(fhi):
        return None
    if flo == 0:
        return lo
    if fhi == 0:
        return hi
    if flo * fhi > 0:
        return None
    a, b, fa, fb = lo, hi, flo, fhi
    for _ in range(maxiter):
        if abs(fb - fa) > 1e-30:
            # secant candidate
            mid = b - fb * (b - a) / (fb - fa)
            if mid <= min(a, b) or mid >= max(a, b):
                mid = 0.5 * (a + b)
        else:
            mid = 0.5 * (a + b)
        fm = f(mid)
        if not _finite(fm):
            mid = 0.5 * (a + b)
            fm = f(mid)
            if not _finite(fm):
                return None
        if abs(fm) < tol or abs(b - a) < tol * max(1.0, abs(mid)):
            return mid
        if fa * fm <= 0:
            b, fb = mid, fm
        else:
            a, fa = mid, fm
    return 0.5 * (a + b)


def tvm_rate(n, pv, pmt, fv, begin=False):
    """Periodic rate i that satisfies the TVM equation."""
    if abs(tvm_balance(0.0, n, pv, pmt, fv, begin)) < 1e-9:
        return 0.0

    def f(i):
        return tvm_balance(i, n, pv, pmt, fv, begin)

    # Sample a wide set of brackets (negative and positive rates).
    grid = (
        -0.9, -0.5, -0.2, -0.1, -0.05, -0.02, -0.01, -0.005, -0.001,
        0.0, 0.0005, 0.001, 0.002, 0.005, 0.008, 0.01, 0.015, 0.02,
        0.03, 0.05, 0.08, 0.1, 0.15, 0.2, 0.3, 0.5, 1.0, 2.0, 5.0
    )
    samples = []
    for x in grid:
        y = f(x)
        samples.append((x, y))
    found = None
    for k in range(len(samples) - 1):
        x1, y1 = samples[k]
        x2, y2 = samples[k + 1]
        if not _finite(y1) or not _finite(y2):
            continue
        root = _find_root(f, x1, x2, y1, y2)
        if root is not None and _finite(root):
            # Prefer a root near common loan rates if several exist.
            if found is None or abs(root) < abs(found):
                found = root
    if found is not None:
        return found
    raise ValueError("cannot solve for the interest rate")


def tvm_solve(unknown, n=None, iyr=None, pv=None, pmt=None, fv=None,
              pyr=12, begin=False):
    """Solve for unknown in ('n','iyr','pv','pmt','fv'). Returns a float.

    iyr is the nominal annual percent (6.5 means 6.5 %). pyr is payments
    per year. begin=True is annuity-due (payments at start of period).
    """
    unk = unknown.lower()
    if pyr is None or pyr == 0:
        raise ValueError("P/YR must be greater than 0")
    if unk != "iyr":
        if iyr is None:
            raise ValueError("I/YR is required")
        i = tvm_i(iyr, pyr)
    if unk == "pmt":
        return tvm_pmt(n, i, pv, fv, begin)
    if unk == "pv":
        return tvm_pv(n, i, pmt, fv, begin)
    if unk == "fv":
        return tvm_fv(n, i, pv, pmt, begin)
    if unk == "n":
        return tvm_n(i, pv, pmt, fv, begin)
    if unk == "iyr":
        i = tvm_rate(n, pv, pmt, fv, begin)
        return i * pyr * 100.0
    raise ValueError("unknown TVM field: %s" % unknown)


## @brief Years for money to double at a nominal rate.
#
#  exact = ln(2) / (m * ln(1 + r/m)), m = P/YR (the sheet's compounding),
#  rule72 = 72 / rate%.  A zero or negative rate never doubles, so both
#  come back None (the sheet shows "--").  P/YR <= 0 also gives None.
#
#  @param iyr  nominal annual rate in percent
#  @param pyr  compounding periods per year (m)
#  @return (exact_years_or_None, rule72_years_or_None)
def tvm_double(iyr, pyr):
    if iyr is None or not _finite(iyr) or iyr <= 0:
        return None, None
    r72 = 72.0 / iyr
    if pyr is None or pyr <= 0:
        return None, r72
    g = 1.0 + (iyr / 100.0) / pyr
    if g <= 1.0:
        return None, r72  # rate too small to register in a float
    return math.log(2.0) / (pyr * math.log(g)), r72


## @brief Two-phase TVM: deposits for N periods, then hands off for a while.
#
#  Phase 1 is the ordinary TVM sheet: N periods of PMT on top of PV give
#  FV1 (the sheet's FV, END or BEGIN already applied by the caller).
#  Phase 2 adds no deposits; FV1 simply compounds at the same periodic
#  rate for the hold.  Give the hold either as extra years after the
#  deposits stop (hold_years) or as the total horizon counted from the
#  first deposit (total_years).  If both are given, total_years wins.
#  If neither is given, the hold is 0 and the final value equals FV1.
#
#  Signs follow the TVM sheet (cash out negative): deposits are negative,
#  FV1 comes back positive.  "contributed" is reported as a positive
#  amount of money put in, -(PV + PMT*N), and growth = final - contributed.
#
#  Floats only, no lists, safe for MicroPython.
#
#  @param n            deposit periods (N on the sheet)
#  @param iyr          nominal annual rate in percent (I/YR)
#  @param pyr          periods per year (P/YR), > 0
#  @param pv           PV from the sheet (signed)
#  @param pmt          PMT from the sheet (signed)
#  @param fv1          FV after the deposits (signed, from the sheet)
#  @param hold_years   years left untouched after the last deposit, or None
#  @param total_years  years from the first deposit to the end, or None
#  @return dict: hold_years, total_years, n2 (hold periods), fv_final,
#          contributed, growth
#  @throws ValueError on a negative hold or a total shorter than N/P/YR
def tvm_hold(n, iyr, pyr, pv, pmt, fv1, hold_years=None, total_years=None):
    if pyr is None or pyr <= 0:
        raise ValueError("P/YR must be greater than 0")
    dep_years = n / float(pyr)
    if total_years is not None:
        if total_years < dep_years - 1e-9:
            raise ValueError("Total years must be at least the deposit years (%s)"
                             % fmt_num(dep_years))
        hold_years = total_years - dep_years
        if hold_years < 0.0:
            hold_years = 0.0  # rounding guard, N/P/YR vs total
    elif hold_years is None:
        hold_years = 0.0
    if hold_years < 0:
        raise ValueError("Hold years must not be negative")
    n2 = hold_years * pyr
    i = tvm_i(iyr, pyr)
    if abs(i) < 1e-16 or n2 == 0:
        grow = 1.0
    else:
        try:
            grow = (1.0 + i) ** n2
        except OverflowError:
            raise ValueError("overflow computing final FV")
        if not _finite(grow):
            raise ValueError("overflow computing final FV")
    fv_final = fv1 * grow
    contributed = -((pv or 0.0) + (pmt or 0.0) * n)
    return {
        "hold_years": hold_years,
        "total_years": dep_years + hold_years,
        "n2": n2,
        "fv_final": fv_final,
        "contributed": contributed,
        "growth": fv_final - contributed,
    }


# ---------------------------------------------------------------------------
# Mortgage / loan / savings
# ---------------------------------------------------------------------------

def mortgage_payment(loan, annual_rate, years, pyr=12):
    """Scheduled payment as a positive amount (ordinary mortgage)."""
    if loan is None or years is None:
        raise ValueError("loan and years are required")
    if years <= 0 or loan <= 0:
        raise ValueError("loan and years must be positive")
    n = years * pyr
    i = (annual_rate / 100.0) / pyr if annual_rate else 0.0
    # PV = +loan received, FV = 0, PMT is negative (cash out)
    pmt = tvm_pmt(n, i, loan, 0.0, False)
    return -pmt


def amort_rows(loan, annual_rate, years, extra=0.0, pyr=12, yearly=False):
    """Build an amortization table.

    Returns (info, rows). Each row is (period, payment, interest,
    principal, balance) as floats. Period is a month number, or a year
    number when yearly=True. info has payment, total_interest, n_payments,
    n_scheduled, months_saved, interest_saved, total_paid.
    """
    if extra is None:
        extra = 0.0
    if extra < 0:
        raise ValueError("extra payment cannot be negative")
    sched = mortgage_payment(loan, annual_rate, years, pyr)
    pay = round_cents(sched + extra)
    if pay <= 0:
        raise ValueError("payment must be positive")
    i = (annual_rate / 100.0) / pyr if annual_rate else 0.0
    n_sched = int(round(years * pyr))
    bal_c = _cents(loan)
    interest_c = 0
    rows_m = []
    month = 0
    # Cap at a long but finite horizon in case the payment barely covers interest.
    cap = max(n_sched * 3, 12) + 2
    while bal_c > 0 and month < cap:
        month += 1
        int_c = _cents((bal_c / 100.0) * i)
        due = bal_c + int_c
        pmt_c = _cents(pay)
        if pmt_c >= due:
            pmt_c = due
        prin_c = pmt_c - int_c
        if prin_c <= 0 and pmt_c < due:
            raise ValueError("payment is too small to pay off the loan")
        bal_c -= prin_c
        if bal_c < 0:
            bal_c = 0
        interest_c += int_c
        rows_m.append((
            month,
            pmt_c / 100.0,
            int_c / 100.0,
            prin_c / 100.0,
            bal_c / 100.0,
        ))
    if bal_c > 0:
        raise ValueError("payment is too small to pay off the loan")
    # Interest on the scheduled loan (no extra), for the "saved" figures.
    interest_saved = 0.0
    months_saved = 0
    if extra > 0:
        info0, _ = amort_rows(loan, annual_rate, years, 0.0, pyr, False)
        interest_saved = info0["total_interest"] - interest_c / 100.0
        months_saved = info0["n_payments"] - month
    info = {
        "payment": sched,
        "payment_with_extra": sched + extra,
        "total_interest": interest_c / 100.0,
        "total_paid": (interest_c + _cents(loan)) / 100.0,
        "n_payments": month,
        "n_scheduled": n_sched,
        "months_saved": months_saved,
        "interest_saved": interest_saved,
        "extra": extra,
    }
    if not yearly:
        return info, rows_m
    rows_y = []
    y = 0
    acc_p = acc_i = acc_r = 0.0
    end_bal = loan
    for (mo, pmt, inte, prin, bal) in rows_m:
        acc_p += pmt
        acc_i += inte
        acc_r += prin
        end_bal = bal
        if mo % 12 == 0 or mo == len(rows_m):
            y += 1
            rows_y.append((y, acc_p, acc_i, acc_r, end_bal))
            acc_p = acc_i = acc_r = 0.0
    return info, rows_y


def loan_payoff(balance, annual_rate, payment, pyr=12):
    """Months to pay off a balance at a fixed payment, plus total interest."""
    if balance <= 0:
        raise ValueError("balance must be positive")
    if payment <= 0:
        raise ValueError("payment must be positive")
    i = (annual_rate / 100.0) / pyr if annual_rate else 0.0
    if i > 0 and payment <= round_cents(balance * i):
        raise ValueError("payment is too small to pay off the loan")
    # Reuse the amort engine: pick a long horizon as "years".
    years = 80
    # scheduled payment is computed from years; we want a fixed payment,
    # so feed extra = payment - scheduled, but easier to walk here.
    bal_c = _cents(balance)
    interest_c = 0
    month = 0
    pmt_req = round_cents(payment)
    cap = years * pyr
    while bal_c > 0 and month < cap:
        month += 1
        int_c = _cents((bal_c / 100.0) * i)
        due = bal_c + int_c
        pmt_c = _cents(pmt_req)
        if pmt_c >= due:
            pmt_c = due
        prin_c = pmt_c - int_c
        if prin_c <= 0 and pmt_c < due:
            raise ValueError("payment is too small to pay off the loan")
        bal_c -= prin_c
        interest_c += int_c
    if bal_c > 0:
        raise ValueError("payment is too small to pay off the loan")
    return {
        "n_payments": month,
        "total_interest": interest_c / 100.0,
        "total_paid": (interest_c + _cents(balance)) / 100.0,
    }


def savings_solve(unknown, target=None, years=None, annual_rate=None,
                  start=None, deposit=None, pyr=12, begin=False):
    """Savings sheet, all amounts positive. unknown is one of
    target, years, annual_rate, start, deposit.
    Deposits are monthly (or pyr times a year). End mode is the default.
    """
    unk = unknown.lower()
    n = None if years is None else years * pyr
    i = None
    if annual_rate is not None:
        i = (annual_rate / 100.0) / pyr
    # Map onto TVM with sign convention: start and deposits are cash out
    # (negative), target is a future receipt (positive) if you withdraw it,
    # but the usual identity is: FV_account = start*(1+i)^n + dep*sinking.
    # In TVM: PV = -start, PMT = -deposit, FV = +target, residual 0.
    pv = None if start is None else -start
    pmt = None if deposit is None else -deposit
    fv = target
    if unk == "deposit":
        p = tvm_solve("pmt", n=n, iyr=annual_rate, pv=pv, fv=fv, pyr=pyr, begin=begin)
        return -p
    if unk == "target":
        return tvm_solve("fv", n=n, iyr=annual_rate, pv=pv, pmt=pmt, pyr=pyr, begin=begin)
    if unk == "start":
        return -tvm_solve("pv", n=n, iyr=annual_rate, pmt=pmt, fv=fv, pyr=pyr, begin=begin)
    if unk == "years":
        nn = tvm_solve("n", iyr=annual_rate, pv=pv, pmt=pmt, fv=fv, pyr=pyr, begin=begin)
        return nn / float(pyr)
    if unk in ("annual_rate", "rate", "iyr"):
        return tvm_solve("iyr", n=n, pv=pv, pmt=pmt, fv=fv, pyr=pyr, begin=begin)
    raise ValueError("unknown savings field: %s" % unknown)


# ---------------------------------------------------------------------------
# NPV / IRR
# ---------------------------------------------------------------------------

def npv(rate_pct, cashflows):
    """NPV at a per-period percent rate. CF0 is at t=0 (not discounted)."""
    r = rate_pct / 100.0
    total = 0.0
    for t, cf in enumerate(cashflows):
        if r == -1.0 and t > 0:
            raise ValueError("discount rate of -100% is not usable")
        den = (1.0 + r) ** t
        if den == 0 or not _finite(den):
            raise ValueError("overflow computing NPV")
        total += cf / den
    return total


def _cf_sign_changes(cashflows):
    n = 0
    last = 0
    for cf in cashflows:
        s = 0
        if cf > 1e-15:
            s = 1
        elif cf < -1e-15:
            s = -1
        if s != 0:
            if last != 0 and s != last:
                n += 1
            last = s
    return n


def irr(cashflows, guess=None):
    """Internal rate of return as a percent per period."""
    if _cf_sign_changes(cashflows) < 1:
        raise ValueError("no IRR (cash flows do not change sign)")

    def f(r):
        # r is a decimal rate, not percent
        try:
            return npv(r * 100.0, cashflows)
        except (ValueError, OverflowError):
            return 1e300

    grid = (
        -0.9, -0.5, -0.2, -0.1, -0.05, 0.0, 0.02, 0.05, 0.08, 0.1,
        0.12, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.75, 1.0, 1.5, 2.0, 5.0
    )
    if guess is not None:
        grid = (guess / 100.0,) + grid
    samples = []
    for x in grid:
        samples.append((x, f(x)))
    roots = []
    for k in range(len(samples) - 1):
        x1, y1 = samples[k]
        x2, y2 = samples[k + 1]
        if not _finite(y1) or not _finite(y2):
            continue
        root = _find_root(f, x1, x2, y1, y2)
        if root is not None and _finite(root):
            # de-duplicate
            dup = False
            for q in roots:
                if abs(q - root) < 1e-7:
                    dup = True
                    break
            if not dup:
                roots.append(root)
    if not roots:
        raise ValueError("cannot solve for IRR")
    # Prefer a modest positive root, else the one closest to zero.
    roots.sort(key=lambda z: (0 if 0 <= z <= 1 else 1, abs(z)))
    return roots[0] * 100.0, len(roots)


# ---------------------------------------------------------------------------
# Date math (proleptic Gregorian, matches Python's datetime.toordinal)
# ---------------------------------------------------------------------------

def is_leap(y):
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


def date_to_ord(y, m, d):
    """Day number, 1 = 0001-01-01 (same as datetime.date.toordinal)."""
    if m < 1 or m > 12:
        raise ValueError("month must be 1..12")
    dim = (31, 29 if is_leap(y) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    if d < 1 or d > dim[m - 1]:
        raise ValueError("bad day for that month")
    if y < 1:
        raise ValueError("year must be 1 or later")
    days = 0
    # years 1 .. y-1
    y0 = y - 1
    days = y0 * 365 + y0 // 4 - y0 // 100 + y0 // 400
    mdays = (0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334)
    days += mdays[m - 1]
    if m > 2 and is_leap(y):
        days += 1
    days += d
    return days


def ord_to_date(n):
    if n < 1:
        raise ValueError("date is out of range")
    # Binary search the year, then walk the month. Fine for UI dates.
    lo, hi = 1, 9999
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if date_to_ord(mid, 1, 1) <= n:
            lo = mid
        else:
            hi = mid - 1
    y = lo
    base = date_to_ord(y, 1, 1)
    doy = n - base + 1
    dim = (31, 29 if is_leap(y) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    m = 1
    while m <= 12 and doy > dim[m - 1]:
        doy -= dim[m - 1]
        m += 1
    return y, m, doy


def parse_date(s):
    t = str(s).strip()
    sep = "-"
    if "/" in t and "-" not in t:
        sep = "/"
    parts = t.split(sep)
    if len(parts) != 3:
        raise ValueError("date must be YYYY-MM-DD")
    try:
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        raise ValueError("date must be YYYY-MM-DD")
    # If someone types MM-DD-YYYY with a 4-digit last part, reject clearly.
    if y < 100 and parts[2] and len(parts[2]) == 4:
        raise ValueError("use YYYY-MM-DD")
    date_to_ord(y, m, d)  # validate
    return y, m, d


def fmt_date(y, m, d):
    return "%04d-%02d-%02d" % (y, m, d)


def days_between(a, b):
    """b - a in days. Each arg is a 'YYYY-MM-DD' string or (y,m,d)."""
    if isinstance(a, str):
        a = parse_date(a)
    if isinstance(b, str):
        b = parse_date(b)
    return date_to_ord(b[0], b[1], b[2]) - date_to_ord(a[0], a[1], a[2])


def add_days(a, n):
    if isinstance(a, str):
        a = parse_date(a)
    o = date_to_ord(a[0], a[1], a[2]) + int(n)
    return ord_to_date(o)


# ---------------------------------------------------------------------------
# Percent / APR
# ---------------------------------------------------------------------------

def pct_change(old, new):
    if old == 0:
        raise ValueError("starting value is 0")
    return (new - old) / old * 100.0


def pct_new(old, change):
    return old * (1.0 + change / 100.0)


def pct_old(new, change):
    if change == -100:
        raise ValueError("a -100% change has no starting value")
    return new / (1.0 + change / 100.0)


def markup(cost, price):
    if cost == 0:
        raise ValueError("cost is 0")
    return (price - cost) / cost * 100.0


def margin(cost, price):
    if price == 0:
        raise ValueError("price is 0")
    return (price - cost) / price * 100.0


def price_from_markup(cost, mu):
    return cost * (1.0 + mu / 100.0)


def cost_from_markup(price, mu):
    if mu == -100:
        raise ValueError("markup of -100% is not usable")
    return price / (1.0 + mu / 100.0)


def price_from_margin(cost, mg):
    if mg >= 100:
        raise ValueError("margin must be under 100%")
    return cost / (1.0 - mg / 100.0)


def cost_from_margin(price, mg):
    return price * (1.0 - mg / 100.0)


def apr_to_apy(apr_pct, periods):
    """Nominal APR (percent) to effective APY (percent).

    periods is compounds per year. periods <= 0 means continuous.
    """
    r = apr_pct / 100.0
    if periods is None or periods <= 0:
        return (math.exp(r) - 1.0) * 100.0
    return ((1.0 + r / periods) ** periods - 1.0) * 100.0


def apy_to_apr(apy_pct, periods):
    a = apy_pct / 100.0
    if periods is None or periods <= 0:
        return math.log(1.0 + a) * 100.0
    return (periods * ((1.0 + a) ** (1.0 / periods) - 1.0)) * 100.0




# ---------------------------------------------------------------------------
# Options (Black-Scholes, European, continuous dividend yield)
# ---------------------------------------------------------------------------

# Day-count for T. 365 calendar days = 1 year.
BS_DAYS_PER_YEAR = 365.0


def _erf(x):
    """Error function: math.erf when present, else Abramowitz-Stegun 7.1.26."""
    erf = getattr(math, "erf", None)
    if callable(erf):
        return erf(x)
    # Abramowitz and Stegun handbook, formula 7.1.26 (abs error < 1.5e-7)
    ax = abs(x)
    t = 1.0 / (1.0 + 0.3275911 * ax)
    a1, a2, a3, a4, a5 = 0.254829592, -0.284496736, 1.421413741, -1.453152027, 1.061405429
    y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * math.exp(-ax * ax)
    if x < 0:
        return -y
    return y


def norm_cdf(x):
    return 0.5 * (1.0 + _erf(x / math.sqrt(2.0)))


def norm_pdf(x):
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def bs_d1_d2(s, k, t, r, sigma, q=0.0):
    """Return (d1, d2). t is in years, r/sigma/q are decimals."""
    if s <= 0 or k <= 0:
        raise ValueError("stock and strike must be positive")
    if t < 0:
        raise ValueError("days to expiry cannot be negative")
    if sigma < 0:
        raise ValueError("volatility cannot be negative")
    if t == 0 or sigma == 0:
        # Defined in the limit; callers should special-case expiry / zero vol.
        return None, None
    vs = sigma * math.sqrt(t)
    if vs < 1e-18:
        return None, None
    d1 = (math.log(s / k) + (r - q + 0.5 * sigma * sigma) * t) / vs
    d2 = d1 - vs
    return d1, d2


def _bs_intrinsic(s, k, t, r, q, call):
    df_r = math.exp(-r * t)
    df_q = math.exp(-q * t)
    if call:
        v = df_q * s - df_r * k
    else:
        v = df_r * k - df_q * s
    if v < 0:
        return 0.0
    return v


def black_scholes(s, k, t, r, sigma, q=0.0):
    """European call and put plus greeks.

    t in years, r/sigma/q as decimals (0.05 = 5%).  Returns a dict:
      call, put, call_delta, put_delta, gamma,
      call_theta, put_theta  (per day),
      vega (per 1 vol point), rho_call, rho_put (per 1 rate point).
    """
    if s <= 0 or k <= 0:
        raise ValueError("stock and strike must be positive")
    if t < 0:
        raise ValueError("days to expiry cannot be negative")
    if sigma < 0:
        raise ValueError("volatility cannot be negative")
    # At expiry, or with zero vol, the option is worth the (forward) intrinsic.
    if t <= 0 or sigma <= 0:
        call = _bs_intrinsic(s, k, max(t, 0.0), r, q, True)
        put = _bs_intrinsic(s, k, max(t, 0.0), r, q, False)
        # Digital-like delta at the strike is left as 0.5 * e^{-qT} for t=0
        # only when exactly at the money; otherwise 0 or e^{-qT}.
        df_q = math.exp(-q * max(t, 0.0))
        if s > k:
            cd, pd = df_q, 0.0
        elif s < k:
            cd, pd = 0.0, -df_q
        else:
            cd, pd = 0.5 * df_q, -0.5 * df_q
        return {
            "call": call, "put": put,
            "call_delta": cd, "put_delta": pd,
            "gamma": 0.0,
            "call_theta": 0.0, "put_theta": 0.0,
            "vega": 0.0, "rho_call": 0.0, "rho_put": 0.0,
        }
    d1, d2 = bs_d1_d2(s, k, t, r, sigma, q)
    nd1 = norm_cdf(d1)
    nd2 = norm_cdf(d2)
    nmd1 = norm_cdf(-d1)
    nmd2 = norm_cdf(-d2)
    npd1 = norm_pdf(d1)
    df_r = math.exp(-r * t)
    df_q = math.exp(-q * t)
    call = s * df_q * nd1 - k * df_r * nd2
    put = k * df_r * nmd2 - s * df_q * nmd1
    call_delta = df_q * nd1
    put_delta = -df_q * nmd1
    sqrt_t = math.sqrt(t)
    gamma = df_q * npd1 / (s * sigma * sqrt_t)
    # Annual theta, then per calendar day.
    theta_common = -s * df_q * npd1 * sigma / (2.0 * sqrt_t)
    call_theta_yr = theta_common - r * k * df_r * nd2 + q * s * df_q * nd1
    put_theta_yr = theta_common + r * k * df_r * nmd2 - q * s * df_q * nmd1
    # Vega: dPrice / d sigma (sigma as a decimal). Per 1 vol point = * 0.01.
    vega_1 = s * df_q * npd1 * sqrt_t * 0.01
    # Rho: dPrice / d r (r as a decimal). Per 1 rate point = * 0.01.
    rho_call = k * t * df_r * nd2 * 0.01
    rho_put = -k * t * df_r * nmd2 * 0.01
    return {
        "call": call, "put": put,
        "call_delta": call_delta, "put_delta": put_delta,
        "gamma": gamma,
        "call_theta": call_theta_yr / BS_DAYS_PER_YEAR,
        "put_theta": put_theta_yr / BS_DAYS_PER_YEAR,
        "vega": vega_1,
        "rho_call": rho_call, "rho_put": rho_put,
    }


def implied_vol(s, k, t, r, price, q=0.0, call=True, lo=1e-6, hi=5.0):
    """Solve for annual volatility (as a percent) given a market price."""
    if t <= 0:
        raise ValueError("need days to expiry to solve for volatility")
    if price is None or price < 0:
        raise ValueError("market price must be zero or more")
    lower = _bs_intrinsic(s, k, t, r, q, call)
    # Tight upper bound: discounted asset (call) or discounted strike (put).
    if call:
        upper = s * math.exp(-q * t)
    else:
        upper = k * math.exp(-r * t)
    # Allow a tiny numerical sliver past the bounds.
    if price < lower - 1e-8:
        raise ValueError("price is below the option's lower bound (%.4f)" % lower)
    if price > upper + 1e-8:
        raise ValueError("price is above the option's upper bound (%.4f)" % upper)

    def f(sig):
        out = black_scholes(s, k, t, r, sig, q)
        return (out["call"] if call else out["put"]) - price

    flo = f(lo)
    fhi = f(hi)
    # Expand the high end if the price is a very high-vol option.
    tries = 0
    while flo * fhi > 0 and hi < 20 and tries < 8:
        hi *= 2
        fhi = f(hi)
        tries += 1
    root = _find_root(f, lo, hi, flo, fhi, tol=1e-10, maxiter=100)
    if root is None or not _finite(root) or root < 0:
        raise ValueError("cannot solve for implied volatility")
    return root * 100.0


# ---------------------------------------------------------------------------
# Keyboard / drawing helpers
# ---------------------------------------------------------------------------

_KEYLOG = []


def _getkey(kb, buf):
    while True:
        n = kb.readinto(buf) if kb else None
        if n:
            if len(_KEYLOG) < 40:
                _KEYLOG.append(buf[0])
            return buf[0]
        utime.sleep_ms(15)


def _drain(kb, buf, ms=280):
    if not kb:
        return
    t0 = utime.ticks_ms()
    while utime.ticks_diff(utime.ticks_ms(), t0) < ms:
        kb.readinto(buf)
        utime.sleep_ms(20)


def _csi_params(seq):
    """Bytes of a CSI sequence without the final character, as a string."""
    if not seq:
        return ""
    out = []
    for b in seq[:-1]:
        out.append(chr(b) if 32 <= b < 127 else "?")
    return "".join(out)


def _map_csi(seq):
    """Map a CSI body (after ESC [) to a key name. seq includes the final byte."""
    if not seq:
        return "esc"
    final = seq[-1]
    if final in (0x41, 0x42, 0x43, 0x44):
        return {0x41: "up", 0x42: "down", 0x43: "right", 0x44: "left"}[final]
    if final == 0x48:  # H
        return "home"
    if final == 0x46:  # F
        return "end"
    if final != 0x7E:  # ~
        return "esc"
    p = _csi_params(seq)
    num = p.split(";")[0] if p else ""
    if num == "15":
        return "clear"  # F5, VT/xterm
    if num == "11":
        return "solve"  # F1
    if num == "3":
        return "del"
    if num in ("1", "7"):
        return "home"
    if num in ("4", "8"):
        return "end"
    if num == "2":
        return "ins"
    if num == "5":
        return "pgup"
    if num == "6":
        return "pgdn"
    return "esc"


def _read_csi_body(kb, buf, first):
    """Read the rest of a CSI sequence; first is the byte already consumed after '['."""
    seq = [first]
    if first >= 0x40:
        return seq
    t0 = utime.ticks_ms()
    while utime.ticks_diff(utime.ticks_ms(), t0) < 60:
        n = kb.readinto(buf) if kb else None
        if n:
            seq.append(buf[0])
            if buf[0] >= 0x40:
                return seq
            t0 = utime.ticks_ms()
        else:
            utime.sleep_ms(5)
    return seq


def _read_key(kb, buf):
    k = _getkey(kb, buf)
    if k == _K_ESC:
        utime.sleep_ms(20)
        n = kb.readinto(buf) if kb else None
        if not n:
            return "esc"
        if buf[0] in (_K_ESC, _K_ESC2):
            return "esc"
        if buf[0] == 0x5B:  # '['  CSI
            n = kb.readinto(buf) if kb else None
            if not n:
                return "esc"
            return _map_csi(_read_csi_body(kb, buf, buf[0]))
        if buf[0] == 0x4F:  # 'O'  SS3 (some layers send ESC O t for F5)
            t0 = utime.ticks_ms()
            while utime.ticks_diff(utime.ticks_ms(), t0) < 40:
                n = kb.readinto(buf) if kb else None
                if n:
                    if buf[0] == 0x74:  # t
                        return "clear"
                    if buf[0] == 0x50:  # P, F1
                        return "solve"
                    return "esc"
                utime.sleep_ms(5)
            return "esc"
        return "esc"
    if k == _K_ESC2:
        return "esc"
    if k == _K_UP:
        return "up"
    if k == _K_DOWN:
        return "down"
    if k == _K_LEFT:
        return "left"
    if k == _K_RIGHT:
        return "right"
    if k == _K_TAB:
        return "tab"
    if k == _K_F1:
        return "solve"
    if k == _K_F5:
        return "clear"
    if k == _K_INS:
        return "ins"
    if k == _K_DEL:
        return "del"
    if k == _K_HOME:
        return "home"
    if k == _K_END:
        return "end"
    if k == _K_PGUP:
        return "pgup"
    if k == _K_PGDN:
        return "pgdn"
    if k in (0x08, 0x7F):
        return "bksp"
    if k in (0x0D, 0x0A):
        # Swallow the mate of a CR/LF pair so Enter is not handled twice.
        t0 = utime.ticks_ms()
        while utime.ticks_diff(utime.ticks_ms(), t0) < 40:
            n = kb.readinto(buf)
            if n and buf[0] not in (0x0A, 0x0D):
                # rare: a real next key; we dropped it. keep drain short.
                break
            utime.sleep_ms(10)
        return "enter"
    if k == 0x20:
        return " "
    if 32 <= k <= 126:
        return chr(k)
    return None


def _text(d, s, x, y, c=FG):
    if s:
        d.text(str(s)[:COLS], x, y, c)


def _hline_row(d, y, c=4):
    d.hline(0, y, 320, c)


# ---------------------------------------------------------------------------
# Story layout: sentences with inline [ blanks ]
# ---------------------------------------------------------------------------

def fmt_ym(n):
    """Short payoff time, e.g. '30y 0m'."""
    if n is None or not _finite(n):
        return "n/a"
    if abs(n - round(n)) < 1e-6:
        n = int(round(n))
        y, mo = divmod(n, 12)
        return "%dy %dm" % (y, mo)
    y = int(n // 12)
    mo = n - 12 * y
    return "%dy %.1fm" % (y, mo)


def parse_story(template):
    """Split a story template into ('text', s) / ('field', key) parts."""
    parts = []
    i = 0
    n = len(template)
    while i < n:
        j = template.find("{", i)
        if j < 0:
            if i < n:
                parts.append(("text", template[i:]))
            break
        if j > i:
            parts.append(("text", template[i:j]))
        k = template.find("}", j)
        if k < 0:
            parts.append(("text", template[j:]))
            break
        parts.append(("field", template[j + 1:k]))
        i = k + 1
    return parts


def field_bracket(field):
    """Render one blank as '[ value ]', padded to the field's width."""
    kind = field.get("kind", "num")
    if kind == "toggle":
        opts = field.get("options") or ["OFF", "ON"]
        raw = opts[int(field.get("on", 0))]
        w = max(len(o) for o in opts)
    else:
        raw = str(field.get("text", ""))
        w = int(field.get("width", 8))
        if not raw.strip():
            raw = "_" * max(4, min(w, 8))
    inner = " " + raw
    need = w + 1  # leading space + content
    if len(inner) < need:
        inner = inner + (" " * (need - len(inner)))
    if inner[-1:] != " ":
        inner = inner + " "
    return "[" + inner + "]"


def layout_story(template, fields, cols=None):
    """Word-wrap a story to `cols` (default 52).

    Returns (lines, marks). Each mark is a dict with key, line, col, width
    in reading order. A blank is never split across lines. A short prefix
    such as '$' stuck to a blank wraps with it.
    """
    if cols is None:
        cols = COLS
    bykey = {}
    if isinstance(fields, dict):
        bykey = fields
    else:
        for f in fields:
            if "key" in f:
                bykey[f["key"]] = f
    parts = list(parse_story(template))
    lines = [""]
    marks = []

    def newline():
        lines.append("")

    def add_chunk(chunk, mark_key=None, width=None):
        if not chunk:
            return
        cur = lines[-1]
        if cur and len(cur) + len(chunk) > cols:
            newline()
            cur = lines[-1]
        if not cur and len(chunk) > cols:
            # extremely wide blank: keep it on one line anyway
            lines[-1] = chunk
            if mark_key is not None:
                marks.append({
                    "key": mark_key, "line": len(lines) - 1,
                    "col": 0, "width": len(chunk) if width is None else width,
                })
            newline()
            return
        col = len(lines[-1])
        lines[-1] = lines[-1] + chunk
        if mark_key is not None:
            marks.append({
                "key": mark_key, "line": len(lines) - 1,
                "col": col, "width": len(chunk) if width is None else width,
            })

    def add_text(text):
        # Hard newlines start a new line. Paragraphs wrap at spaces.
        segs = text.split("\n")
        for si, seg in enumerate(segs):
            if si:
                newline()
            rest = seg
            while rest:
                cur = lines[-1]
                room = cols - len(cur)
                if room <= 0:
                    newline()
                    rest = rest.lstrip(" ")
                    continue
                if len(rest) <= room:
                    lines[-1] = cur + rest
                    break
                # Prefer a break at the last space that fits.
                cut = rest.rfind(" ", 0, room)
                if cut > 0:
                    lines[-1] = cur + rest[:cut]
                    rest = rest[cut + 1:]
                    newline()
                    continue
                if cur:
                    # No space in the remaining room; wrap to a new line.
                    newline()
                    rest = rest.lstrip(" ")
                    continue
                # A single word longer than cols: hard-split.
                lines[-1] = rest[:cols]
                rest = rest[cols:]
                newline()

    def take_suffix(i):
        # Punctuation glued after a blank ('.', '%', '%.', ',') wraps with
        # the blank, so a line never starts with a lone '.'.
        if i + 1 < nparts and parts[i + 1][0] == "text":
            t = parts[i + 1][1]
            j = 0
            while j < len(t) and j < 3 and t[j] not in " \t\n":
                j += 1
            if j:
                parts[i + 1] = ("text", t[j:])
                return t[:j]
        return ""

    i = 0
    nparts = len(parts)
    while i < nparts:
        typ, val = parts[i]
        if typ == "text":
            # If this text ends with a short no-space prefix (e.g. '$')
            # and a field follows, hold the prefix so it wraps with the blank.
            prefix = ""
            body = val
            if i + 1 < nparts and parts[i + 1][0] == "field":
                # peel a trailing '$', '+', or similar
                t = val
                j = len(t)
                while j > 0 and t[j - 1] not in " \t\n":
                    j -= 1
                held = t[j:]
                if held and len(held) <= 2:
                    body = t[:j]
                    prefix = held
            add_text(body)
            if prefix:
                # attach to next field
                i += 1
                key = parts[i][1]
                f = bykey.get(key)
                br = field_bracket(f) if f else "[ ? ]"
                suf = take_suffix(i)
                add_chunk(prefix + br + suf, key, len(prefix + br))
            i += 1
            continue
        # field
        f = bykey.get(val)
        br = field_bracket(f) if f else "[ ? ]"
        suf = take_suffix(i)
        add_chunk(br + suf, val, len(br))
        i += 1

    # Drop a trailing empty line left by a final newline in the template.
    while len(lines) > 1 and lines[-1] == "":
        lines.pop()
    return lines, marks


def story_keys(template, fields):
    """Field keys in reading order (as they appear in the story)."""
    _lines, marks = layout_story(template, fields)
    return [m["key"] for m in marks]


# ---------------------------------------------------------------------------
# Story form
# ---------------------------------------------------------------------------

def _blank(field):
    if field.get("kind") == "toggle":
        return False
    return not str(field.get("text", "")).strip() or set(str(field.get("text", "")).strip()) == set("_")


def _num_of(field):
    t = str(field.get("text", "")).strip()
    if not t or set(t) == set("_"):
        return None
    return parse_num(t)


def _fields_by_key(fields):
    out = {}
    for f in fields:
        if "key" in f:
            out[f["key"]] = f
    return out


def _set_solved(field, value, money=False, places=None, ym=False):
    if ym:
        field["text"] = fmt_ym(value)
    elif money:
        field["text"] = fmt_money(value)
    elif places is not None:
        field["text"] = fmt_num(value, places)
    else:
        field["text"] = fmt_num(value)
    field["solved"] = True


def _next_editable(fields, i, step):
    n = len(fields)
    j = i
    for _ in range(n):
        j = (j + step) % n
        if fields[j].get("hidden"):
            continue
        if fields[j].get("kind", "num") != "sep" and "key" in fields[j]:
            return j
    return i


def _draw_story(d, title, lines, marks, cur_key, fields_by_key, status,
                status_err, footer, scroll):
    d.beginDraw()
    d.fill(0)
    d.fill_rect(0, 0, 320, 11, BAR)
    _text(d, title, 2, 2, FG)
    body_top = 16
    footer_y = 320 - 11
    status_h = 0
    status_bits = []
    if status:
        raw = str(status)
        for part in raw.split("\n"):
            while len(part) > COLS:
                status_bits.append(part[:COLS])
                part = part[COLS:]
            status_bits.append(part)
        if len(status_bits) > 2:
            status_bits = status_bits[:2]
        status_h = 10 * len(status_bits)
    vis = max(4, (footer_y - status_h - 4 - body_top) // 10)
    if scroll < 0:
        scroll = 0
    max_scroll = max(0, len(lines) - vis)
    if scroll > max_scroll:
        scroll = max_scroll
    # highlight / text
    for li in range(scroll, min(len(lines), scroll + vis)):
        y = body_top + (li - scroll) * 10
        line = lines[li]
        _text(d, line, 2, y, FG)
        for m in marks:
            if m["line"] != li:
                continue
            x = 2 + m["col"] * 6
            w = m["width"] * 6
            f = fields_by_key.get(m["key"])
            if m["key"] == cur_key:
                d.fill_rect(x, y - 1, w, 10, HI)
                _text(d, line[m["col"]:m["col"] + m["width"]], x, y, FG)
                # cursor at the end of the typed value, inside the bracket
                cx = x + w - 6
                d.fill_rect(cx, y, 6, 8, DIM)
            elif f and f.get("solved"):
                _text(d, line[m["col"]:m["col"] + m["width"]], x, y, RES)
    y = footer_y - status_h
    if status_bits:
        col = ERR if status_err else RES
        for part in status_bits:
            _text(d, part[:COLS], 2, y, col)
            y += 10
    d.fill_rect(0, footer_y, 320, 11, BAR)
    _text(d, (footer or "")[:COLS], 2, footer_y + 2, FG)
    d.show()
    return scroll, vis


def _clone_field(f):
    c = {}
    for k, v in f.items():
        if isinstance(v, list):
            c[k] = list(v)
        else:
            c[k] = v
    return c


def _clone_fields(fields):
    return [_clone_field(f) for f in fields]


def _restore_fields(fields, opening):
    """Replace the contents of fields in place with a deep copy of opening."""
    n = len(opening)
    while len(fields) > n:
        fields.pop()
    for i, src in enumerate(opening):
        copied = _clone_field(src)
        if i < len(fields):
            fields[i].clear()
            fields[i].update(copied)
        else:
            fields.append(copied)


def _first_editable(fields):
    cur = 0
    while cur < len(fields) and (
            fields[cur].get("kind") == "sep" or "key" not in fields[cur]
            or fields[cur].get("hidden")):
        cur += 1
    if cur >= len(fields):
        cur = _next_editable(fields, 0, 1)
    return cur


def field_state(fields):
    """Comparable snapshot of a sheet's fields (for tests and equality)."""
    out = []
    for f in fields:
        out.append({
            "key": f.get("key"),
            "text": f.get("text", ""),
            "kind": f.get("kind", "num"),
            "on": f.get("on", 0),
            "hidden": bool(f.get("hidden")),
            "solved": bool(f.get("solved")),
        })
    return out


def apply_sheet_clear(fields, opening, on_clear=None):
    """Reset a sheet to its opening field state. Returns the first editable index."""
    if on_clear:
        on_clear(fields)
    _restore_fields(fields, opening)
    return _first_editable(fields)


def run_form(d, kb, title, story, fields, on_solve, footer=None, on_key=None,
             story_fn=None, on_clear=None):
    """Story form. on_solve(fields) -> (err_or_None, status_or_None).

    story is a template with {key} blanks. story_fn(fields), if set, is
    used instead (for sheets whose text changes, e.g. NPV cash flows).
    F5 (or CSI ESC [ 15 ~) resets every field to the opening defaults.
    """
    buf = bytearray(1)
    _drain(kb, buf, 250)
    cur = 0
    while cur < len(fields) and (fields[cur].get("kind") == "sep" or "key" not in fields[cur] or fields[cur].get("hidden")):
        cur += 1
    scroll = 0
    status = ""
    status_err = False
    replace = True
    if footer is None:
        footer = "Tab/arrows  Enter solves  F5 clears  ESC back"
    opening = _clone_fields(fields)

    def current_story():
        if story_fn:
            return story_fn(fields)
        return story

    while True:
        tmpl = current_story()
        lines, marks = layout_story(tmpl, fields)
        bykey = _fields_by_key(fields)
        # If the current blank was hidden after a solve, move off it.
        if cur >= len(fields) or fields[cur].get("hidden") or "key" not in fields[cur]:
            cur = _next_editable(fields, cur if cur < len(fields) else 0, 1)
        cur_key = fields[cur]["key"] if cur < len(fields) and "key" in fields[cur] else None
        # Keep the current blank in view.
        cur_line = 0
        for m in marks:
            if m["key"] == cur_key:
                cur_line = m["line"]
                break
        # Provisional vis to compute scroll; draw returns the used scroll.
        vis_guess = 24
        if cur_line < scroll:
            scroll = cur_line
        elif cur_line >= scroll + vis_guess:
            scroll = cur_line - vis_guess + 1
        if d is not None:
            scroll, vis = _draw_story(
                d, title, lines, marks, cur_key, bykey, status, status_err,
                footer, scroll)
            if cur_line < scroll:
                scroll = cur_line
                scroll, vis = _draw_story(
                    d, title, lines, marks, cur_key, bykey, status, status_err,
                    footer, scroll)
            elif cur_line >= scroll + vis:
                scroll = cur_line - vis + 1
                scroll, vis = _draw_story(
                    d, title, lines, marks, cur_key, bykey, status, status_err,
                    footer, scroll)
        k = _read_key(kb, buf)
        if k is None:
            continue
        if on_key:
            r = on_key(k, fields, cur)
            if r:
                if r[0] == "handled":
                    if len(r) > 1:
                        cur = r[1]
                        if cur >= len(fields):
                            cur = len(fields) - 1
                        if cur < 0:
                            cur = 0
                    replace = True
                    continue
                if r[0] == "leave":
                    return r[1] if len(r) > 1 else None
                if r[0] == "status":
                    status = r[1]
                    status_err = bool(r[2]) if len(r) > 2 else False
                    continue
                if r[0] == "clear":
                    k = "clear"
        if k == "clear":
            cur = apply_sheet_clear(fields, opening, on_clear)
            status, status_err = "sheet cleared", False
            replace = True
            scroll = 0
            continue
        if k == "esc":
            return None
        if k == "up":
            cur = _next_editable(fields, cur, -1)
            replace = True
            continue
        if k in ("down", "tab"):
            cur = _next_editable(fields, cur, 1)
            replace = True
            continue
        if k == "home":
            cur = _next_editable(fields, 0, -1)
            cur = _next_editable(fields, cur, 1)
            replace = True
            continue
        if k == "end":
            cur = _next_editable(fields, len(fields) - 1, 1)
            cur = _next_editable(fields, cur, -1)
            replace = True
            continue
        f = fields[cur]
        kind = f.get("kind", "num")
        if kind == "toggle" and k in (" ",):
            opts = f.get("options") or ["OFF", "ON"]
            f["on"] = (int(f.get("on", 0)) + 1) % len(opts)
            f["solved"] = False
            continue
        if k == "left":
            cur = _next_editable(fields, cur, -1)
            replace = True
            continue
        if k == "right":
            cur = _next_editable(fields, cur, 1)
            replace = True
            continue
        if k == "del":
            if kind != "toggle":
                f["text"] = ""
                f["solved"] = False
                replace = True
            continue
        if k == "bksp":
            if kind != "toggle":
                t = str(f.get("text", ""))
                f["text"] = t[:-1]
                f["solved"] = False
                replace = False
            continue
        if k in ("enter", "solve", "="):
            try:
                err, msg = on_solve(fields)
            except Exception as e:
                err, msg = str(e), None
            if err:
                status, status_err = err, True
            else:
                status, status_err = (msg or "solved"), False
            _drain(kb, buf, 80)
            continue
        if kind != "toggle" and isinstance(k, str) and len(k) == 1 and 32 <= ord(k) <= 126:
            if k == "=":
                try:
                    err, msg = on_solve(fields)
                except Exception as e:
                    err, msg = str(e), None
                if err:
                    status, status_err = err, True
                else:
                    status, status_err = (msg or "solved"), False
                continue
            if k == " ":
                continue
            t = str(f.get("text", ""))
            if replace:
                t = ""
                replace = False
            if len(t) < 20:
                t = t + k
            f["text"] = t
            f["solved"] = False
            status = ""


# ---------------------------------------------------------------------------
# Scrollable table (amortization)
# ---------------------------------------------------------------------------

def show_table(d, kb, heading, headers, rows, footer=None, on_key=None):
    """Scroll through rows. on_key may return ('rows', new_rows, heading) or 'leave'."""
    buf = bytearray(1)
    _drain(kb, buf, 200)
    top = 0
    if footer is None:
        footer = "Up/Down/PgUp/PgDn  F5 clears  ESC back"
    while True:
        d.beginDraw()
        d.fill(0)
        d.fill_rect(0, 0, 320, 11, BAR)
        _text(d, heading, 2, 2, FG)
        _text(d, headers, 2, 14, DIM)
        _hline_row(d, 23, 4)
        body = ROWS - 5
        if top < 0:
            top = 0
        max_top = max(0, len(rows) - body)
        if top > max_top:
            top = max_top
        y = 26
        for i in range(top, min(len(rows), top + body)):
            _text(d, rows[i], 2, y, FG)
            y += 10
        d.fill_rect(0, 320 - 11, 320, 11, BAR)
        more = footer
        if rows:
            more = "%s  %d-%d/%d" % (footer, top + 1, min(len(rows), top + body), len(rows))
        _text(d, more[:COLS], 2, 320 - 9, FG)
        d.show()
        k = _read_key(kb, buf)
        if k == "esc":
            return
        if k == "clear":
            return "clear"
        if k in ("up", "left"):
            top -= 1
        elif k in ("down", "right", "tab"):
            top += 1
        elif k == "pgup" or k == "home":
            top -= body if k == "pgup" else top
        elif k == "pgdn" or k == "end":
            top += body if k == "pgdn" else max_top
        elif on_key:
            r = on_key(k)
            if r == "leave":
                return
            if r and r[0] == "rows":
                rows = r[1]
                if len(r) > 2:
                    heading = r[2]
                top = 0


def _row_line(period, pmt, inte, prin, bal, width_p=4):
    def m(v):
        s = fmt_money(v)
        if len(s) > 11:
            s = fmt_num(v, 2)
        return s.rjust(11)

    return str(period).rjust(width_p) + m(pmt) + m(inte) + m(prin) + m(bal)


# ---------------------------------------------------------------------------
# Sheet specs (story + fields). Used by the UI and by host tests.
# ---------------------------------------------------------------------------

STORY = {}


def _F(key, label, text="", width=8, kind="num", options=None, on=0):
    f = {"key": key, "label": label, "text": text, "width": width, "kind": kind}
    if kind == "toggle":
        f["options"] = options or ["OFF", "ON"]
        f["on"] = on
    return f


## @brief TVM story. Total yrs is the default horizon; hold is the alternate.
#
#  The hold-result lines (final FV, put-in, growth) are omitted when the
#  effective hold is 0, including when total yrs equals the deposit years.
#  The doubling line always stays: it is rate information, not a hold result.
def tvm_story(fields=None):
    show_extra = False
    if fields:
        m = _fields_by_key(fields)
        fvh = m.get("fvh")
        if fvh and not fvh.get("hidden", True) and not _blank(fvh):
            show_extra = True
    head = (
        "Over {n} periods, at {iyr}% a year, with {pyr} payments "
        "a year at the {mode} of each period, a present value of "
        "${pv} and a future value of ${fv} means the payment is "
        "${pmt} each period.\n"
        "\n"
        "That's {total} years in all"
    )
    if show_extra:
        head += (
            ", including {hold} years after the deposits stop. "
            "It grows to ${fvh}. Put in ${paid}, so the growth "
            "is ${gain}."
        )
    else:
        head += (
            ". Hold for {hold} more years after the deposits stop."
        )
    tail = (
        "\n"
        "\n"
        "At this rate money doubles in {dbl} years (rule of "
        "72 says {r72}).\n"
        "\n"
        "Cash out is negative, cash in is positive."
    )
    return head + tail


def spec_tvm():
    fields = [
        _F("n", "N", "", 6),
        _F("iyr", "I/YR %", "", 6),
        _F("pyr", "P/YR", "12", 4),
        _F("mode", "When", kind="toggle", options=["END", "BEGIN"], on=0, width=5),
        _F("pv", "PV", "", 10),
        _F("fv", "FV", "0", 10),
        _F("pmt", "PMT", "", 10),
        # Total yrs is the default horizon input; hold yrs is the alternate.
        # Typing in one clears the other. N is periods, not years.
        _F("total", "total yrs", "", 5),
        _F("hold", "hold yrs", "", 5),
        # Hold-result lines: hidden until the effective hold is > 0.
        _F("fvh", "final FV", "", 10),
        _F("paid", "put in", "", 10),
        _F("gain", "growth", "", 10),
        # Doubling time at the entered rate (results only; always shown).
        _F("dbl", "double yrs", "", 6),
        _F("r72", "rule of 72", "", 6),
    ]
    for k in ("fvh", "paid", "gain"):
        for f in fields:
            if f.get("key") == k:
                f["hidden"] = True
                break
    story = tvm_story(fields)
    return {"title": "12C mode  |  TVM", "story": story, "fields": fields,
            "footer": "Tab  Enter  Space END/BEGIN  F5 clears  ESC back",
            "story_fn": tvm_story}


def spec_mortgage():
    fields = [
        _F("loan", "loan", "", 10),
        _F("rate", "rate", "", 6),
        _F("years", "years", "", 5),
        _F("extra", "extra", "0", 8),
        _F("pmt", "payment", "", 10),
        _F("interest", "interest", "", 10),
        _F("payoff", "payoff", "", 9),
        _F("saved", "time saved", "", 9),
        _F("isaved", "interest saved", "", 10),
    ]
    story = (
        "I borrow ${loan} at {rate}% a year\n"
        "for {years} years, and I add ${extra} extra\n"
        "each month.\n"
        "\n"
        "My payment is ${pmt} a month.\n"
        "Over the loan I pay ${interest} in interest,\n"
        "and it's paid off in {payoff}.\n"
        "The extra payment saves {saved} and ${isaved} in interest."
    )
    return {"title": "12C mode  |  Mortgage", "story": story, "fields": fields,
            "footer": "Enter solves  A table  F5 clears  ESC back"}


def spec_loan():
    fields = [
        _F("bal", "balance", "", 10),
        _F("rate", "rate", "", 6),
        _F("pmt", "payment", "", 10),
        _F("months", "payoff", "", 9),
        _F("interest", "interest", "", 10),
        _F("total", "total paid", "", 10),
    ]
    story = (
        "I still owe ${bal} at {rate}% a year.\n"
        "If I pay ${pmt} each month, I will be done in {months}, "
        "having paid ${interest} in interest and ${total} in total."
    )
    return {"title": "12C mode  |  Loan payoff", "story": story, "fields": fields,
            "footer": "Tab  Enter solves  F5 clears  ESC back"}


def spec_savings():
    fields = [
        _F("target", "target", "", 10),
        _F("years", "years", "", 5),
        _F("start", "start", "0", 10),
        _F("rate", "rate", "", 6),
        _F("mode", "When", kind="toggle", options=["END", "BEGIN"], on=0, width=5),
        _F("deposit", "deposit", "", 10),
    ]
    story = (
        "I want ${target} in {years} years. I already have ${start}, "
        "and I earn {rate}% a year, with deposits at the {mode} of "
        "each month.\n"
        "\n"
        "I need to put away ${deposit} each month."
    )
    return {"title": "12C mode  |  Savings goal", "story": story, "fields": fields,
            "footer": "Tab  Enter  Space END/BEGIN  F5 clears  ESC back"}


def spec_npv(n_cf=2):
    fields = [_F("rate", "rate", "", 6)]
    if n_cf < 1:
        n_cf = 1
    for i in range(n_cf):
        fields.append(_F("cf%d" % i, "CF%d" % i, "", 10))
    fields.append(_F("npv", "NPV", "", 10))
    fields.append(_F("irr", "IRR", "", 8))
    return {"title": "12C mode  |  NPV / IRR", "fields": fields,
            "footer": "Enter  A add  R remove  F5 clears  ESC back"}


def npv_story(fields):
    n_cf = 0
    for f in fields:
        if str(f.get("key", "")).startswith("cf"):
            n_cf += 1
    bits = [
        "At a discount rate of {rate}% per period, these cash flows "
        "have an NPV of ${npv} and an IRR of {irr}%.\n",
        ""
    ]
    for i in range(n_cf):
        bits.append("CF%d is ${cf%d}." % (i, i))
    return "\n".join(bits)


def spec_dates():
    fields = [
        _F("a", "date A", "", 12, kind="text"),
        _F("b", "date B", "", 12, kind="text"),
        _F("n", "days", "", 7),
    ]
    story = (
        "Date A is {a} and date B is {b}.\n"
        "From A to B is {n} days."
    )
    return {"title": "12C mode  |  Date math", "story": story, "fields": fields,
            "footer": "YYYY-MM-DD.  Enter solves  F5 clears  ESC back"}


def spec_percent():
    fields = [
        _F("old", "old", "", 8),
        _F("new", "new", "", 8),
        _F("chg", "change %", "", 7),
        _F("cost", "cost", "", 8),
        _F("price", "price", "", 8),
        _F("mu", "markup %", "", 7),
        _F("mg", "margin %", "", 7),
        _F("apr", "APR %", "", 7),
        _F("periods", "comp/yr", "12", 4),
        _F("apy", "APY %", "", 8),
    ]
    story = (
        "A value of {old} changed to {new} is a {chg}% change.\n"
        "\n"
        "An item that costs ${cost} and sells for ${price} has a "
        "{mu}% markup and a {mg}% margin.\n"
        "\n"
        "A {apr}% APR compounded {periods} times a year is a "
        "{apy}% effective APY.  (Comp/yr 0 means continuous.)"
    )
    return {"title": "12C mode  |  Percent / APR", "story": story, "fields": fields,
            "footer": "Leave one blank in a group.  F5 clears  Enter"}


def spec_options():
    fields = [
        _F("s", "stock", "", 8),
        _F("k", "strike", "", 8),
        _F("days", "days left", "", 6),
        _F("r", "rate", "", 6),
        _F("vol", "vol", "", 7),
        _F("q", "div yield", "0", 5),
        _F("call", "call", "", 8),
        _F("put", "put", "", 8),
        _F("cd", "call delta", "", 8),
        _F("pd", "put delta", "", 8),
        _F("gamma", "gamma", "", 8),
        _F("vega", "vega", "", 8),
        _F("ct", "call theta", "", 8),
        _F("pt", "put theta", "", 8),
        _F("rc", "call rho", "", 8),
        _F("rp", "put rho", "", 8),
        _F("cp", "mkt is", kind="toggle", options=["CALL", "PUT"], on=0, width=4),
        _F("mkt", "mkt price", "", 8),
        _F("iv", "implied vol", "", 7),
    ]
    story = (
        "A stock at ${s}, strike ${k}, with {days} days left, a "
        "{r}% risk-free rate, {vol}% volatility and a {q}% dividend "
        "yield, is worth ${call} as a call and ${put} as a put.\n"
        "\n"
        "Call delta is {cd}, put delta {pd}. Gamma is {gamma}, and "
        "vega is {vega} per 1% vol. Theta per day is {ct} for the "
        "call and {pt} for the put. Rho per 1% is {rc} for the call "
        "and {rp} for the put.\n"
        "\n"
        "A market {cp} priced at ${mkt} implies a volatility of {iv}%."
    )
    return {"title": "12C mode  |  Options (Black-Scholes)", "story": story,
            "fields": fields,
            "footer": "Enter solves  Space CALL/PUT  F5 clears  ESC"}


# Fill STORY with static templates for tests.
def _init_stories():
    for name, fn in (
        ("tvm", spec_tvm), ("mortgage", spec_mortgage), ("loan", spec_loan),
        ("savings", spec_savings), ("dates", spec_dates),
        ("percent", spec_percent), ("options", spec_options),
    ):
        STORY[name] = fn()["story"]
    STORY["npv"] = npv_story(spec_npv()["fields"])


_init_stories()


def sheet_spec(name):
    """Return a spec dict {title, story, fields, footer} for tests."""
    fn = {
        "tvm": spec_tvm, "mortgage": spec_mortgage, "loan": spec_loan,
        "savings": spec_savings, "npv": spec_npv, "dates": spec_dates,
        "percent": spec_percent, "options": spec_options,
    }.get(name)
    if not fn:
        return None
    spec = fn()
    if name == "npv" and "story" not in spec:
        spec["story"] = npv_story(spec["fields"])
        spec["story_fn"] = npv_story
    return spec


# ---------------------------------------------------------------------------
# Individual sheets
# ---------------------------------------------------------------------------

## @brief Format a year count: "30" when whole, else two places.
def _fmt_years(v):
    if abs(v - round(v)) < 1e-6:
        return str(int(round(v)))
    return fmt_num(v, 2)


## @brief Solve the TVM sheet (phase 1), then the invest-then-hold part.
#
#  Phase 1 is unchanged: leave exactly one of N, I/YR, PV, PMT, FV blank.
#  N is periods, not years.  Phase 2 then reads total yrs / hold yrs
#  (a typed total wins over hold; both blank means hold 0).  Total yrs
#  is the default horizon input; hold yrs is the alternate.  When the
#  effective hold is 0 (including when total yrs equals the deposit
#  years) the hold-result lines (final FV, put-in, growth) stay hidden.
#  The doubling line is always filled.  With a hold > 0 the missing
#  horizon field, final FV, put-in and growth are filled.
#
#  @param fs  the sheet's field list (spec_tvm()["fields"])
#  @return (error_or_None, status_or_None), as run_form expects
def tvm_sheet_solve(fs):
    m = _fields_by_key(fs)
    pyr = parse_num(m["pyr"]["text"])
    if not pyr:
        return "P/YR must be greater than 0", None
    begin = int(m["mode"].get("on", 0)) == 1
    keys = ("n", "iyr", "pv", "pmt", "fv")
    blank = [k for k in keys if _blank(m[k])]
    if len(blank) != 1:
        return "Leave exactly one of periods, rate, PV, payment, or FV blank", None
    unk = blank[0]
    kw = {"pyr": pyr, "begin": begin}
    for k in keys:
        if k != unk:
            kw[k] = _num_of(m[k])
            if kw[k] is None:
                return "Fill every blank except the one to solve", None
    val = tvm_solve(unk, **kw)
    money = unk in ("pv", "pmt", "fv")
    places = 6 if unk == "iyr" else (4 if unk == "n" else None)
    if unk == "n" and abs(val - round(val)) < 1e-8:
        _set_solved(m[unk], val, places=0)
    elif money:
        _set_solved(m[unk], val, money=True)
    else:
        _set_solved(m[unk], val, places=places if places else 6)
    msg = "solved %s = %s" % (m[unk]["label"], m[unk]["text"])

    # ---- doubling time at the (entered or solved) rate -----------------
    rate = val if unk == "iyr" else kw["iyr"]
    ex, r72 = tvm_double(rate, pyr)
    m["dbl"]["text"] = "--" if ex is None else fmt_num(ex, 2)
    m["r72"]["text"] = "--" if r72 is None else fmt_num(r72, 2)
    m["dbl"]["solved"] = True
    m["r72"]["solved"] = True

    # ---- phase 2: hands off (no deposits) ------------------------------
    kw[unk] = val
    for k in ("fvh", "paid", "gain"):
        m[k]["text"] = ""
        m[k]["solved"] = False
        m[k]["hidden"] = True
    tf = m["total"]
    hf = m["hold"]
    total_in = None
    hold_in = None
    if not _blank(tf) and not tf.get("solved"):
        total_in = _num_of(tf)
    elif not _blank(hf):
        hold_in = _num_of(hf)
    try:
        r = tvm_hold(kw["n"], kw["iyr"], pyr, kw["pv"], kw["pmt"], kw["fv"],
                     hold_years=hold_in, total_years=total_in)
    except ValueError as e:
        return str(e), None
    if total_in is not None:
        hf["text"] = _fmt_years(r["hold_years"])
        hf["solved"] = True
    else:
        tf["text"] = _fmt_years(r["total_years"])
        tf["solved"] = True
    if r["hold_years"] > 0:
        for k in ("fvh", "paid", "gain"):
            m[k]["hidden"] = False
        _set_solved(m["fvh"], r["fv_final"], money=True)
        _set_solved(m["paid"], r["contributed"], money=True)
        _set_solved(m["gain"], r["growth"], money=True)
        msg = msg + "\nyear %s: %s  growth %s" % (
            _fmt_years(r["total_years"]), m["fvh"]["text"], m["gain"]["text"])
    return None, msg


## @brief TVM key hook: typing in hold yrs clears total yrs and back.
#
#  Returns None so run_form still handles the key itself.
def _tvm_on_key(k, fs, cur):
    if cur >= len(fs):
        return None
    key = fs[cur].get("key")
    if key not in ("hold", "total"):
        return None
    edit = k in ("bksp", "del") or (
        isinstance(k, str) and len(k) == 1 and k not in (" ", "="))
    if edit:
        other = "total" if key == "hold" else "hold"
        for f in fs:
            if f.get("key") == other:
                f["text"] = ""
                f["solved"] = False
        fs[cur]["solved"] = False
    return None


def sheet_tvm(d, kb):
    spec = spec_tvm()
    fields = spec["fields"]
    run_form(d, kb, spec["title"], spec["story"], fields, tvm_sheet_solve,
             footer=spec["footer"], on_key=_tvm_on_key, story_fn=tvm_story)


def sheet_mortgage(d, kb):
    spec = spec_mortgage()
    fields = spec["fields"]
    state = {"info": None, "loan": None, "rate": None, "years": None, "extra": 0}

    def on_solve(fs):
        m = _fields_by_key(fs)
        loan = _num_of(m["loan"])
        rate = _num_of(m["rate"])
        years = _num_of(m["years"])
        extra = _num_of(m["extra"])
        pmt = _num_of(m["pmt"])
        if extra is None:
            extra = 0.0
            if _blank(m["extra"]):
                m["extra"]["text"] = "0"
        # interest / payoff / saved are always outputs
        unk = [k for k in ("loan", "rate", "years", "pmt") if _blank(m[k])]
        if len(unk) > 1:
            return "Leave one of loan, rate, years, or payment blank", None
        if len(unk) == 1:
            u = unk[0]
            try:
                if u == "pmt":
                    if loan is None or rate is None or years is None:
                        return "Fill loan, rate, and years to solve for payment", None
                    pmt = mortgage_payment(loan, rate, years)
                    _set_solved(m["pmt"], pmt, money=True)
                elif u == "loan":
                    if rate is None or years is None or pmt is None:
                        return "Fill rate, years, and payment to solve for the loan", None
                    loan = tvm_solve("pv", n=years * 12, iyr=rate, pmt=-pmt, fv=0.0, pyr=12)
                    _set_solved(m["loan"], loan, money=True)
                elif u == "rate":
                    if loan is None or years is None or pmt is None:
                        return "Fill loan, years, and payment to solve for the rate", None
                    rate = tvm_solve("iyr", n=years * 12, pv=loan, pmt=-pmt, fv=0.0, pyr=12)
                    _set_solved(m["rate"], rate, places=6)
                elif u == "years":
                    if loan is None or rate is None or pmt is None:
                        return "Fill loan, rate, and payment to solve for years", None
                    n = tvm_solve("n", iyr=rate, pv=loan, pmt=-pmt, fv=0.0, pyr=12)
                    years = n / 12.0
                    _set_solved(m["years"], years, places=3)
            except ValueError as e:
                return str(e), None
        if loan is None or rate is None or years is None:
            return "Fill loan, rate, and years", None
        info, _ = amort_rows(loan, rate, years, extra, 12, False)
        state["info"] = info
        state["loan"] = loan
        state["rate"] = rate
        state["years"] = years
        state["extra"] = extra
        if _blank(m["pmt"]) or m["pmt"].get("solved") or pmt is None:
            _set_solved(m["pmt"], info["payment"], money=True)
        _set_solved(m["interest"], info["total_interest"], money=True)
        _set_solved(m["payoff"], info["n_payments"], ym=True)
        _set_solved(m["saved"], info["months_saved"], ym=True)
        _set_solved(m["isaved"], info["interest_saved"], money=True)
        return None, "payment %s a month, paid off in %s" % (
            m["pmt"]["text"], m["payoff"]["text"])

    def on_clear(_fs):
        state["info"] = None
        state["loan"] = None
        state["rate"] = None
        state["years"] = None
        state["extra"] = 0

    def on_key(k, fs, cur):
        if k in ("a", "A", "t", "T"):
            if not state["info"]:
                return ("status", "solve the loan first (press Enter)", True)
            if _open_amort(d, kb, state) == "clear":
                return ("clear",)
            return ("handled", cur)
        return None

    run_form(d, kb, spec["title"], spec["story"], fields, on_solve,
             footer=spec["footer"], on_key=on_key, on_clear=on_clear)


def _open_amort(d, kb, state):
    yearly = [False]

    def build():
        info, rows = amort_rows(
            state["loan"], state["rate"], state["years"], state["extra"],
            12, yearly[0])
        kind = "yearly" if yearly[0] else "monthly"
        heading = "Amort  %s   pmt %s" % (kind, fmt_money(info["payment_with_extra"]))
        headers = "  %s    Payment   Interest  Principal    Balance" % (
            "Yr" if yearly[0] else "Mo")
        lines = [_row_line(p, a, b, c, e) for (p, a, b, c, e) in rows]
        return heading, headers, lines

    heading, headers, lines = build()

    def on_key(k):
        if k in ("y", "Y"):
            yearly[0] = not yearly[0]
            h, _, rows = build()
            return ("rows", rows, h)
        return None

    return show_table(d, kb, heading, headers, lines,
               footer="Y yearly/monthly  F5 clears  ESC back", on_key=on_key)


def sheet_loan(d, kb):
    spec = spec_loan()
    fields = spec["fields"]

    def on_solve(fs):
        m = _fields_by_key(fs)
        bal = _num_of(m["bal"])
        rate = _num_of(m["rate"])
        pmt = _num_of(m["pmt"])
        months = None
        if not _blank(m["months"]):
            try:
                months = _num_of(m["months"])
            except ValueError:
                # already a formatted payoff like '30y 0m'
                months = -1
        unk = [k for k in ("bal", "rate", "pmt", "months") if _blank(m[k])]
        if len(unk) > 1:
            return "Leave one of balance, rate, payment, or payoff time blank", None
        try:
            if unk == ["pmt"] or (not unk and pmt is None):
                if months is None or months < 0:
                    return "Fill payoff time to solve for the payment", None
                pmt = -tvm_solve("pmt", n=months, iyr=rate, pv=bal, fv=0.0, pyr=12)
                _set_solved(m["pmt"], pmt, money=True)
            elif unk == ["bal"]:
                if pmt is None:
                    return "Fill the payment to solve for the balance", None
                n = months if (months is not None and months > 0) else None
                if n is None:
                    return "Fill payoff time or the payment and rate first", None
                bal = tvm_solve("pv", n=n, iyr=rate, pmt=-pmt, fv=0.0, pyr=12)
                _set_solved(m["bal"], bal, money=True)
            elif unk == ["rate"]:
                if pmt is None or months is None or months < 0:
                    return "Fill payment and payoff time to solve for the rate", None
                rate = tvm_solve("iyr", n=months, pv=bal, pmt=-pmt, fv=0.0, pyr=12)
                _set_solved(m["rate"], rate, places=6)
            elif unk == ["months"] or not unk:
                if bal is None or rate is None or pmt is None:
                    return "Fill balance, rate, and payment", None
            elif unk:
                return "Fill balance, rate, and payment", None
        except ValueError as e:
            return str(e), None
        info = loan_payoff(bal, rate, pmt)
        _set_solved(m["months"], info["n_payments"], ym=True)
        _set_solved(m["interest"], info["total_interest"], money=True)
        _set_solved(m["total"], info["total_paid"], money=True)
        return None, "paid off in %s, interest %s" % (
            m["months"]["text"], m["interest"]["text"])

    run_form(d, kb, spec["title"], spec["story"], fields, on_solve,
             footer=spec["footer"])


def sheet_savings(d, kb):
    spec = spec_savings()
    fields = spec["fields"]
    keymap = {
        "target": "target", "years": "years", "rate": "annual_rate",
        "start": "start", "deposit": "deposit",
    }

    def on_solve(fs):
        m = _fields_by_key(fs)
        begin = int(m["mode"].get("on", 0)) == 1
        keys = ("target", "years", "rate", "start", "deposit")
        blank = [k for k in keys if _blank(m[k])]
        if len(blank) != 1:
            return "Leave exactly one of target, years, rate, start, or deposit blank", None
        unk = blank[0]
        kw = {"begin": begin, "pyr": 12}
        for k in keys:
            if k != unk:
                v = _num_of(m[k])
                if v is None:
                    return "Fill every blank except the one to solve", None
                kw[keymap[k]] = v
        val = savings_solve(keymap[unk], **kw)
        money = unk in ("target", "start", "deposit")
        if money:
            _set_solved(m[unk], val, money=True)
        elif unk == "years":
            _set_solved(m[unk], val, places=3)
        else:
            _set_solved(m[unk], val, places=6)
        return None, "solved %s = %s" % (m[unk]["label"], m[unk]["text"])

    run_form(d, kb, spec["title"], spec["story"], fields, on_solve,
             footer=spec["footer"])


def sheet_npv(d, kb):
    spec = spec_npv()
    fields = spec["fields"]

    def cf_fields(fs):
        return [f for f in fs if str(f.get("key", "")).startswith("cf")]

    def relabel(fs):
        n = 0
        for f in fs:
            if str(f.get("key", "")).startswith("cf"):
                f["key"] = "cf%d" % n
                f["label"] = "CF%d" % n
                n += 1

    def on_solve(fs):
        m = _fields_by_key(fs)
        mrate = _num_of(m["rate"])
        cfs = []
        for f in cf_fields(fs):
            if _blank(f):
                cfs.append(None)
            else:
                cfs.append(_num_of(f))
        while cfs and cfs[-1] is None:
            cfs.pop()
        if not cfs:
            return "Enter at least CF0", None
        cfs = [0.0 if x is None else x for x in cfs]
        bits = []
        if mrate is not None:
            val = npv(mrate, cfs)
            _set_solved(m["npv"], val, money=True)
            bits.append("NPV %s" % m["npv"]["text"])
        try:
            rate, nroots = irr(cfs)
            _set_solved(m["irr"], rate, places=6)
            bit = "IRR %s%%" % m["irr"]["text"]
            if nroots > 1:
                bit += " (more than one IRR exists)"
            bits.append(bit)
        except ValueError as e:
            if mrate is None:
                return str(e), None
            bits.append(str(e))
        if not bits:
            return "Enter a discount rate or cash flows", None
        return None, "   ".join(bits)

    def on_key(k, fs, cur):
        f = fs[cur]
        is_cf = str(f.get("key", "")).startswith("cf")
        if k in ("a", "A", "ins"):
            idx = cur + 1
            # insert before the trailing NPV/IRR outputs
            if not is_cf:
                idx = len(fs)
                for i, x in enumerate(fs):
                    if x.get("key") in ("npv", "irr"):
                        idx = i
                        break
            fs.insert(idx, _F("cfX", "CFX", "", 10))
            relabel(fs)
            return ("handled", idx)
        if k in ("r", "R") or (k == "del" and is_cf and _blank(f)):
            cfs = cf_fields(fs)
            if len(cfs) <= 1:
                return ("status", "keep at least CF0", True)
            if not is_cf:
                for i in range(len(fs) - 1, -1, -1):
                    if str(fs[i].get("key", "")).startswith("cf"):
                        fs.pop(i)
                        break
            else:
                fs.pop(cur)
            relabel(fs)
            nc = cur
            if nc >= len(fs):
                nc = len(fs) - 1
            return ("handled", nc)
        return None

    run_form(d, kb, spec["title"], None, fields, on_solve,
             footer=spec["footer"], on_key=on_key, story_fn=npv_story)


def sheet_dates(d, kb):
    spec = spec_dates()
    fields = spec["fields"]

    def on_solve(fs):
        m = _fields_by_key(fs)
        a_b, b_b, n_b = _blank(m["a"]), _blank(m["b"]), _blank(m["n"])
        nblank = (1 if a_b else 0) + (1 if b_b else 0) + (1 if n_b else 0)
        if nblank != 1:
            return "Leave exactly one of Date A, Date B, or days blank", None
        try:
            if n_b:
                a = parse_date(m["a"]["text"])
                b = parse_date(m["b"]["text"])
                n = days_between(a, b)
                m["n"]["text"] = str(int(n))
                m["n"]["solved"] = True
                return None, "%s  to  %s  is  %d days" % (
                    fmt_date(*a), fmt_date(*b), n)
            if b_b:
                a = parse_date(m["a"]["text"])
                n = int(parse_num(m["n"]["text"]))
                b = add_days(a, n)
                m["b"]["text"] = fmt_date(*b)
                m["b"]["solved"] = True
                return None, "%s  %+d  =  %s" % (fmt_date(*a), n, fmt_date(*b))
            b = parse_date(m["b"]["text"])
            n = int(parse_num(m["n"]["text"]))
            a = add_days(b, -n)
            m["a"]["text"] = fmt_date(*a)
            m["a"]["solved"] = True
            return None, "%s  is  %+d  from  %s" % (fmt_date(*a), n, fmt_date(*b))
        except ValueError as e:
            return str(e), None

    run_form(d, kb, spec["title"], spec["story"], fields, on_solve,
             footer=spec["footer"])


def sheet_percent(d, kb):
    spec = spec_percent()
    fields = spec["fields"]

    def on_solve(fs):
        m = _fields_by_key(fs)
        groups = [
            ("chg", ("old", "new", "chg")),
            ("mk", ("cost", "price", "mu", "mg")),
            ("apr", ("apr", "apy")),
        ]
        candidates = []
        for name, keys in groups:
            filled = [k for k in keys if not _blank(m[k])]
            blank = [k for k in keys if _blank(m[k])]
            if not filled:
                continue
            candidates.append((name, keys, filled, blank))
        if not candidates:
            return "Fill a group and leave one blank in it", None
        exact = [c for c in candidates if len(c[3]) == 1]
        if len(exact) == 1:
            name, keys, filled, blank = exact[0]
        elif len(exact) > 1:
            return "One group at a time; clear the others or fill them", None
        else:
            # markup group can solve from two filled fields
            mk = [c for c in candidates if c[0] == "mk" and len(c[2]) >= 2]
            if len(mk) == 1 and not exact:
                name, keys, filled, blank = mk[0]
            else:
                return "Leave exactly one blank in the group you are solving", None

        if name == "chg":
            unk = blank[0]
            if unk == "chg":
                v = pct_change(_num_of(m["old"]), _num_of(m["new"]))
                _set_solved(m["chg"], v, places=6)
            elif unk == "new":
                v = pct_new(_num_of(m["old"]), _num_of(m["chg"]))
                _set_solved(m["new"], v, money=True)
            else:
                v = pct_old(_num_of(m["new"]), _num_of(m["chg"]))
                _set_solved(m["old"], v, money=True)
            return None, "change  %s%%" % m["chg"]["text"] if unk != "chg" else "change  %s%%" % m["chg"]["text"]

        if name == "mk":
            cost, price, mu, mg = _num_of(m["cost"]), _num_of(m["price"]), _num_of(m["mu"]), _num_of(m["mg"])
            try:
                if cost is not None and price is not None:
                    mu = markup(cost, price)
                    mg = margin(cost, price)
                elif cost is not None and mu is not None:
                    price = price_from_markup(cost, mu)
                    mg = margin(cost, price)
                elif cost is not None and mg is not None:
                    price = price_from_margin(cost, mg)
                    mu = markup(cost, price)
                elif price is not None and mu is not None:
                    cost = cost_from_markup(price, mu)
                    mg = margin(cost, price)
                elif price is not None and mg is not None:
                    cost = cost_from_margin(price, mg)
                    mu = markup(cost, price)
                else:
                    return "Need cost and price, or one of those plus markup or margin", None
            except ValueError as e:
                return str(e), None
            _set_solved(m["cost"], cost, money=True)
            _set_solved(m["price"], price, money=True)
            _set_solved(m["mu"], mu, places=6)
            _set_solved(m["mg"], mg, places=6)
            return None, "markup %s%%   margin %s%%" % (m["mu"]["text"], m["mg"]["text"])

        per = _num_of(m["periods"])
        if per is None:
            per = 12
        unk = blank[0]
        if unk == "apy":
            v = apr_to_apy(_num_of(m["apr"]), per)
            _set_solved(m["apy"], v, places=6)
        else:
            v = apy_to_apr(_num_of(m["apy"]), per)
            _set_solved(m["apr"], v, places=6)
        tag = "continuous" if per <= 0 else ("%g times / yr" % per)
        return None, "%s  (%s)" % (m[unk]["text"], tag)

    run_form(d, kb, spec["title"], spec["story"], fields, on_solve,
             footer=spec["footer"])


def sheet_options(d, kb):
    spec = spec_options()
    fields = spec["fields"]

    def on_solve(fs):
        m = _fields_by_key(fs)
        s = _num_of(m["s"])
        k = _num_of(m["k"])
        days = _num_of(m["days"])
        r_pct = _num_of(m["r"])
        vol_pct = _num_of(m["vol"])
        q_pct = _num_of(m["q"])
        mkt = _num_of(m["mkt"])
        if q_pct is None:
            q_pct = 0.0
        if s is None or k is None or days is None or r_pct is None:
            return "Fill stock, strike, days left, and rate", None
        t_yr = days / BS_DAYS_PER_YEAR
        r = r_pct / 100.0
        q = q_pct / 100.0
        is_call = int(m["cp"].get("on", 0)) == 0
        solved_iv = False
        if vol_pct is None:
            if mkt is None:
                return "Enter vol %, or a market price to solve for vol", None
            vol_pct = implied_vol(s, k, t_yr, r, mkt, q, is_call)
            _set_solved(m["vol"], vol_pct, places=6)
            _set_solved(m["iv"], vol_pct, places=6)
            solved_iv = True
        sigma = vol_pct / 100.0
        out = black_scholes(s, k, t_yr, r, sigma, q)
        _set_solved(m["call"], out["call"], money=True)
        _set_solved(m["put"], out["put"], money=True)
        _set_solved(m["cd"], out["call_delta"], places=6)
        _set_solved(m["pd"], out["put_delta"], places=6)
        _set_solved(m["gamma"], out["gamma"], places=6)
        _set_solved(m["vega"], out["vega"], places=6)
        _set_solved(m["ct"], out["call_theta"], places=6)
        _set_solved(m["pt"], out["put_theta"], places=6)
        _set_solved(m["rc"], out["rho_call"], places=6)
        _set_solved(m["rp"], out["rho_put"], places=6)
        if mkt is not None and not solved_iv:
            try:
                iv = implied_vol(s, k, t_yr, r, mkt, q, is_call)
                _set_solved(m["iv"], iv, places=6)
            except ValueError:
                pass
        elif not _blank(m["vol"]) and _blank(m["iv"]):
            _set_solved(m["iv"], vol_pct, places=6)
        msg = "call %s   put %s" % (m["call"]["text"], m["put"]["text"])
        if solved_iv:
            msg = "implied vol %s%%.  %s" % (m["vol"]["text"], msg)
        return None, msg

    run_form(d, kb, spec["title"], spec["story"], fields, on_solve,
             footer=spec["footer"])


# ---------------------------------------------------------------------------
# Menu / entry
# ---------------------------------------------------------------------------

SHEETS = (
    ("tvm", "TVM   N, I/YR, PV, PMT, FV"),
    ("mortgage", "Mortgage / amortization"),
    ("loan", "Loan payoff"),
    ("savings", "Savings goal"),
    ("npv", "NPV / IRR"),
    ("dates", "Date math"),
    ("percent", "Percent / APR to APY"),
    ("options", "Options (Black-Scholes)"),
)

ALIASES = {
    "tvm": "tvm", "n": "tvm", "pmt": "tvm",
    "mortgage": "mortgage", "mort": "mortgage", "amort": "mortgage",
    "am": "mortgage", "loan": "loan", "payoff": "loan",
    "savings": "savings", "save": "savings", "goal": "savings",
    "npv": "npv", "irr": "npv",
    "date": "dates", "dates": "dates", "days": "dates",
    "percent": "percent", "pct": "percent", "apr": "percent", "apy": "percent",
    "options": "options", "option": "options", "opt": "options",
    "bs": "options", "black": "options", "scholes": "options",
}

_OPEN = {
    "tvm": sheet_tvm,
    "mortgage": sheet_mortgage,
    "loan": sheet_loan,
    "savings": sheet_savings,
    "npv": sheet_npv,
    "dates": sheet_dates,
    "percent": sheet_percent,
    "options": sheet_options,
}


def resolve_sheet(name):
    if not name:
        return None
    key = str(name).strip().lower()
    return ALIASES.get(key)


def _menu(d, kb, sel=0):
    buf = bytearray(1)
    _drain(kb, buf, 250)
    n = len(SHEETS)
    while True:
        d.beginDraw()
        d.fill(0)
        d.fill_rect(0, 0, 320, 11, BAR)
        _text(d, "12C mode  |  sheets", 2, 2, FG)
        _text(d, "HP12C-style worksheets.  Not an HP product.", 2, 16, DIM)
        y = 36
        for i, (key, label) in enumerate(SHEETS):
            mark = ">" if i == sel else " "
            line = mark + " " + label
            if i == sel:
                d.fill_rect(0, y - 1, 320, 10, HI)
            _text(d, line, 2, y, FG)
            y += 12
        d.fill_rect(0, 320 - 11, 320, 11, BAR)
        _text(d, "Up/Down  Enter opens  ESC back", 2, 320 - 9, FG)
        d.show()
        k = _read_key(kb, buf)
        if k == "esc":
            return None
        if k == "up":
            sel = (sel - 1) % n
        elif k in ("down", "tab"):
            sel = (sel + 1) % n
        elif k == "home":
            sel = 0
        elif k == "end":
            sel = n - 1
        elif k in ("enter", "solve", "right", "="):
            _drain(kb, buf, 80)
            return SHEETS[sel][0]


def run(d, kb, start=None):
    """Open 12C mode. start is a sheet name, or None for the menu."""
    gc.collect()
    buf = bytearray(1)
    _drain(kb, buf, 280)
    sel = 0
    key = resolve_sheet(start) if start else None
    if start and not key:
        key = None
    try:
        while True:
            if key:
                fn = _OPEN.get(key)
                if fn:
                    for i, (k, _lab) in enumerate(SHEETS):
                        if k == key:
                            sel = i
                            break
                    fn(d, kb)
                key = None
                gc.collect()
                continue
            picked = _menu(d, kb, sel)
            if not picked:
                break
            key = picked
    finally:
        _drain(kb, buf, 200)
        gc.collect()



def _park_vt():
    """Detach the VT terminal so its cursor timer stops drawing on our screen."""
    import os
    try:
        import picocalc
        import vtterminal
        try:
            os.dupterm(None)
        except Exception:
            pass
        if picocalc.terminal is not None:
            try:
                picocalc.terminal.wr("\x1b[?25l")
            except Exception:
                pass
        park = bytearray(len(picocalc.display.buffer))
        vtterminal.init(park)
        return park
    except Exception:
        return None


def _unpark_vt(park):
    import os
    try:
        import picocalc
        import vtterminal
        if park is not None:
            vtterminal.init(picocalc.display.buffer)
        if picocalc.terminal is not None:
            try:
                picocalc.terminal.wr("\x1b[?25h")
                os.dupterm(picocalc.terminal)
            except Exception:
                pass
    except Exception:
        pass


def _log(msg):
    try:
        with open("/sheets_log.txt", "a") as f:
            f.write(str(utime.ticks_ms()) + " " + msg + "\n")
    except Exception:
        pass


def main():
    """Standalone entry so the menu item 'SuperCalc 12C mode' opens the sheets."""
    import sys
    _log("main start")
    park = _park_vt()
    _log("vt parked" if park is not None else "vt park returned None")
    try:
        import picocalc
        run(picocalc.display, picocalc.keyboard)
        _log("run returned keys=" + repr(_KEYLOG))
    except Exception as e:
        _log("run error: " + repr(e))
        try:
            import io
            sb = io.StringIO()
            sys.print_exception(e, sb)
            _log(sb.getvalue())
        except Exception:
            pass
    finally:
        _unpark_vt(park)
        gc.collect()

