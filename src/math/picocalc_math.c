// Minimal hybrid proof module for SuperCalc.OG Phase 0/1 gate
// Builds as a MicroPython user C module (see micropython.cmake)

#include "py/obj.h"
#include "py/runtime.h"

// Trivial example: return version or a computed value
STATIC mp_obj_t picocalc_math_version(void) {
    return mp_obj_new_str("SuperCalc.OG-hybrid-proof-0.1", 28);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(picocalc_math_version_obj, picocalc_math_version);

// Another trivial: add two numbers (demonstrates arg passing + return)
STATIC mp_obj_t picocalc_math_add(mp_obj_t a_in, mp_obj_t b_in) {
    mp_int_t a = mp_obj_get_int(a_in);
    mp_int_t b = mp_obj_get_int(b_in);
    return mp_obj_new_int(a + b);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_2(picocalc_math_add_obj, picocalc_math_add);

STATIC const mp_rom_map_elem_t picocalc_math_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_picocalc_math) },
    { MP_ROM_QSTR(MP_QSTR_version), MP_ROM_PTR(&picocalc_math_version_obj) },
    { MP_ROM_QSTR(MP_QSTR_add), MP_ROM_PTR(&picocalc_math_add_obj) },
};
STATIC MP_DEFINE_CONST_DICT(picocalc_math_module_globals, picocalc_math_globals_table);

const mp_obj_module_t picocalc_math_module = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&picocalc_math_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_picocalc_math, picocalc_math_module);