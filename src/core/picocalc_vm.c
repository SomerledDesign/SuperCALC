// picocalc_vm.c — C VM / program execution kernel for SuperCalc.OG (Phase 2+)
// Thin C extension boundary for the RPL-inspired programmable language.
//
// Phase 2 inc1: skeleton only. Registers the module so USER_C_MODULES builds can
// include it. Real work (bytecode format, control structures IF/START/FOR, locals
// frames via -> , call/return stack, fast inner dispatch) comes in later incs.
//
// For now the execution hot paths for simple sequential programs still ride the
// Phase 1 expr + hybrid (C math) until the dedicated VM is filled in.
// Programs as first-class + "run" semantics are proven in MPy first (rapid syntax
// iteration per architecture), then accelerated.
//
// When the custom UF2 includes usermod_picocalc_vm, `import picocalc_vm` succeeds
// on device and native code runs.
//
// See mp/lang/prog.py + expr.py for the current program object model and exec driver.
// See DECISIONS.md for RPN_STACK_MAX tracking and VM boundary choices.
//
// Offline-first, double baseline, thin documented boundary.

#include "py/obj.h"
#include "py/runtime.h"
#include "py/objiter.h"
#include <string.h>

// --- Skeleton API ---

STATIC mp_obj_t picocalc_vm_version(void) {
    const char *v = "SuperCalc.OG-vm-skel-0.5";
    return mp_obj_new_str(v, strlen(v));
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(picocalc_vm_version_obj, picocalc_vm_version);

// Placeholder exec. In inc1 the real work is in the MPy layer (shared stack executor
// in expr._execute_rpn_body + prog). Later this will accept bytecode or token forms
// and run with C speed + dedicated control stack.
STATIC mp_obj_t picocalc_vm_exec(mp_obj_t obj_in) {
    // For skel we simply document that full impl is pending and raise a clear error
    // so accidental use during Phase 2 inc1 is obvious. Host tests use the py fallback
    // in hybrid; on-device after full wiring the C path will be taken for hot programs.
    mp_raise_NotImplementedError(MP_ERROR_TEXT("vm_exec skel: use lang.prog / expr for Phase 2 inc1; C impl in later increment"));
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(picocalc_vm_exec_obj, picocalc_vm_exec);

// Module table
STATIC const mp_rom_map_elem_t picocalc_vm_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_picocalc_vm) },
    { MP_ROM_QSTR(MP_QSTR_version),  MP_ROM_PTR(&picocalc_vm_version_obj) },
    { MP_ROM_QSTR(MP_QSTR_exec),     MP_ROM_PTR(&picocalc_vm_exec_obj) },
};
STATIC MP_DEFINE_CONST_DICT(picocalc_vm_module_globals, picocalc_vm_globals_table);

const mp_obj_module_t picocalc_vm_module = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&picocalc_vm_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_picocalc_vm, picocalc_vm_module);
