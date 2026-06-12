// picocalc_math.c — Minimal hybrid proof for SuperCalc.OG Phase 0
// Thin C extension boundary: MPy calls these for speed/accuracy on hot paths.
// Built via USER_C_MODULES + micropython.cmake (LofiFren/zenodante-style base).
//
// When the custom UF2 is flashed, `import picocalc_math` succeeds from device REPL
// and calls execute in native code (RP2350 FPU for doubles).
//
// This file + .cmake + mp/lib/hybrid.py prove the extension path exists and is
// ready for Phase 1 (real numeric kernel, complex, RPN eval, etc.).
//
// Offline-first, 320x320-aware, double baseline per DECISIONS.md.

#include "py/obj.h"
#include "py/runtime.h"
#include <math.h>

// --- Thin documented API (subject to small evolution in Phase 1) ---

STATIC mp_obj_t picocalc_math_version(void) {
    return mp_obj_new_str("SuperCalc.OG-hybrid-proof-0.2", 28);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(picocalc_math_version_obj, picocalc_math_version);

// add: accepts int or float; returns float result (math spirit, not limited to small-int)
STATIC mp_obj_t picocalc_math_add(mp_obj_t a_in, mp_obj_t b_in) {
    double a = mp_obj_get_float(a_in);
    double b = mp_obj_get_float(b_in);
    return mp_obj_new_float(a + b);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_2(picocalc_math_add_obj, picocalc_math_add);

// sin(x) — demonstrates <math.h> hot path + double precision
STATIC mp_obj_t picocalc_math_sin(mp_obj_t x_in) {
    double x = mp_obj_get_float(x_in);
    double r = sin(x);
    return mp_obj_new_float(r);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(picocalc_math_sin_obj, picocalc_math_sin);

// sqrt(x) — useful primitive; errors on negative via runtime (or we can raise ValueError)
STATIC mp_obj_t picocalc_math_sqrt(mp_obj_t x_in) {
    double x = mp_obj_get_float(x_in);
    if (x < 0.0) {
        mp_raise_ValueError(MP_ERROR_TEXT("sqrt of negative"));
    }
    return mp_obj_new_float(sqrt(x));
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(picocalc_math_sqrt_obj, picocalc_math_sqrt);

STATIC const mp_rom_map_elem_t picocalc_math_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_picocalc_math) },
    { MP_ROM_QSTR(MP_QSTR_version), MP_ROM_PTR(&picocalc_math_version_obj) },
    { MP_ROM_QSTR(MP_QSTR_add),     MP_ROM_PTR(&picocalc_math_add_obj) },
    { MP_ROM_QSTR(MP_QSTR_sin),     MP_ROM_PTR(&picocalc_math_sin_obj) },
    { MP_ROM_QSTR(MP_QSTR_sqrt),    MP_ROM_PTR(&picocalc_math_sqrt_obj) },
};
STATIC MP_DEFINE_CONST_DICT(picocalc_math_module_globals, picocalc_math_globals_table);

const mp_obj_module_t picocalc_math_module = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&picocalc_math_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_picocalc_math, picocalc_math_module);