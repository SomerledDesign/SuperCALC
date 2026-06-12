// picocalc_plot.c — Graphing sampling + raster kernel for SuperCalc.OG (Phase 3+)
// Thin C extension boundary for fast 2D plot data and (future) framebuffer drawing.
//
// Phase 3 inc1: skeleton only. Registers the module so USER_C_MODULES builds can
// include it alongside picocalc_math and picocalc_vm. Real work (dense sampling
// loops over RPN/bytecode exprs, linspace in C, line raster into existing
// picocalc.display LUT/framebuffer, axis/grid, viewport clip) comes in later incs.
//
// For now the hot sampling path for Cartesian (and later polar/parametric) rides
// the Phase 1/2 expr + hybrid (C math) in pure Python loop. This gives immediate
// usable plot *data* on host and (after UF2) on device while the C module is wired.
//
// When the custom UF2 includes usermod_picocalc_plot, `import picocalc_plot`
// succeeds on device and native code runs.
//
// See mp/plot/plot.py for the current (inc1) sampling implementation.
// See ARCHITECTURE.md and DECISIONS.md for 320x320 + data-first strategy.
//
// Offline-first, double baseline, thin documented boundary, 320x320-aware.

#include "py/obj.h"
#include "py/runtime.h"
#include "py/objiter.h"
#include <string.h>

// --- Skeleton API (Phase 3 inc1) ---

STATIC mp_obj_t picocalc_plot_version(void) {
    const char *v = "SuperCalc.OG-plot-skel-0.5";
    return mp_obj_new_str(v, strlen(v));
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(picocalc_plot_version_obj, picocalc_plot_version);

// Placeholder. In inc1 the real sampling + render work is in the MPy layer
// (mp/plot/plot.py cartesian_sample re-using expr/eval_rpn + hybrid math).
// Later this (or new entrypoints) will accept x-buffers + RPN/bytecode and
// produce y results or draw directly, all in C for speed on 320+ samples.
STATIC mp_obj_t picocalc_plot_sample(mp_obj_t obj_in) {
    // For skel we document that full impl (C sampling loop, raster) is pending
    // and raise a clear error so accidental use during Phase 3 inc1 is obvious.
    // Host tests and REPL use the py fallback in mp/plot; on-device after
    // wiring the C path will be taken for hot graphs.
    mp_raise_NotImplementedError(MP_ERROR_TEXT("plot_sample skel: use mp.plot.cartesian_sample for Phase 3 inc1; C impl + raster in later increment"));
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(picocalc_plot_sample_obj, picocalc_plot_sample);

// Module table
STATIC const mp_rom_map_elem_t picocalc_plot_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_picocalc_plot) },
    { MP_ROM_QSTR(MP_QSTR_version),  MP_ROM_PTR(&picocalc_plot_version_obj) },
    { MP_ROM_QSTR(MP_QSTR_sample),   MP_ROM_PTR(&picocalc_plot_sample_obj) },
};
STATIC MP_DEFINE_CONST_DICT(picocalc_plot_module_globals, picocalc_plot_globals_table);

const mp_obj_module_t picocalc_plot_module = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&picocalc_plot_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_picocalc_plot, picocalc_plot_module);
