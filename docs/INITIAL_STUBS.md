# Initial Stubs & Extension Points (Phase 0 / early Phase 1)

This file contains lightweight starter code and notes so we have something concrete to build on.

## 1. Custom C Module Skeleton (Example)

We will add modules such as:

- `picocalc_math` — numeric kernel + complex + matrix basics + solvers
- `picocalc_plot` — sampling and fast drawing helpers
- `picocalc_vm`   — bytecode interpreter for the HP-style custom language

### Example directory layout inside the build

```
user_modules/
├── picocalc_math/
│   ├── picocalc_math.c
│   ├── picocalc_math.h
│   └── micropython.cmake
├── picocalc_plot/
│   └── ...
└── picocalc_vm/
    └── ...
```

### Minimal picocalc_math.c (stub)

```c
// picocalc_math.c - Initial stub for hybrid calculator core
#include "py/obj.h"
#include "py/runtime.h"
#include <math.h>

// Example: fast sin wrapper (we will expand dramatically)
STATIC mp_obj_t picocalc_math_sin(mp_obj_t x_in) {
    double x = mp_obj_get_float(x_in);
    double result = sin(x);
    return mp_obj_new_float(result);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(picocalc_math_sin_obj, picocalc_math_sin);

// Module globals table
STATIC const mp_rom_map_elem_t picocalc_math_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_picocalc_math) },
    { MP_ROM_QSTR(MP_QSTR_sin), MP_ROM_PTR(&picocalc_math_sin_obj) },
    // ... many more to come: cos, exp, log, complex, matrix ops, eval_rpn, etc.
};
STATIC MP_DEFINE_CONST_DICT(picocalc_math_module_globals, picocalc_math_globals_table);

const mp_obj_module_t picocalc_math_module = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&picocalc_math_module_globals,
};
MP_REGISTER_MODULE(MP_QSTR_picocalc_math, picocalc_math_module);
```

### micropython.cmake (example)

```cmake
add_library(usermod_picocalc_math INTERFACE)

target_sources(usermod_picocalc_math INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}/picocalc_math.c
)

target_include_directories(usermod_picocalc_math INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}
)

target_link_libraries(usermod INTERFACE usermod_picocalc_math)
```

Then in the top-level `micropython.cmake` (or the one used by the base port build):

```cmake
list(APPEND USER_C_MODULES
    ${PROJECT_SOURCE_DIR}/user_modules/picocalc_math/micropython.cmake
    # + plot and vm later
)
```

Rebuild the UF2 and you can do `import picocalc_math; print(picocalc_math.sin(0.5))` from the REPL — with the work happening in fast C.

## 2. MicroPython Side Thin Wrapper (Early Prototype)

Even before the C module is rich, we can create a nice MPy API that will later delegate to C.

`mp/lib/hybrid.py` (starter):

```python
# Thin hybrid math interface
# Phase 0/1: can fall back to math/ulab; later calls into C extensions

try:
    import picocalc_math as _c
    HAS_C_MATH = True
except ImportError:
    HAS_C_MATH = False
    import math as _py

def sin(x):
    if HAS_C_MATH:
        return _c.sin(x)
    return _py.sin(x)

# TODO: rpn_eval(tokens), complex, matrices, solve, etc.
```

This pattern lets us develop the UI and language in MPy immediately while the C implementation catches up.

## 3. Expression Internal Form (Sketch)

We will converge on a simple shared representation:

- RPN list of tokens (numbers, operators, function calls, variables)
- Or a tiny AST for cases where we want algebraic manipulation

Example (Python for now):

```python
# RPN example: sin(2 * pi) + 1   →   [2, 'pi', '*', 'sin', 1, '+']
```

The C side will have a fast evaluator for this form.

## 4. Next Concrete Files We Should Create

- `src/math/math_core.c` + header (real start of numeric kernel)
- `mp/lang/parser.py` (infix + rpn converter)
- `mp/ui/calc_repl.py` (early calculator UI mode)
- Program storage manager (`mp/lang/program_store.py`)
- Test harness (host Python that mirrors the on-device API for fast iteration)

## Notes for Build Integration

Because the base ports use Docker for reproducible builds, we will likely:

1. Clone the chosen base (LofiFren recommended).
2. Add our `src/` tree as a submodule or copy.
3. Modify the `micropython.cmake` include list.
4. Provide a small wrapper script in `tools/build_graphingcalc.sh` that does the Docker invocation with our modules.

We can keep our main source tree here and mount it during build.

---

This file will be replaced / expanded as real code lands. Use it as a shared scratchpad during early Ralph Loop iterations.
