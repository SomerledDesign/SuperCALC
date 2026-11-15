// SuperCalc.OG: MP_CONFIGFILE overlay for ports/rp2 (included by py/mpconfig.h).
// Pulls in the normal rp2 port config, then switches Python floats from 32-bit
// single precision (rp2 default) to 64-bit double (~15-16 significant digits).
// Kevin chose double precision on 2026-11-13 (DECISIONS.md "double baseline").
#include <mpconfigport.h>

#undef MICROPY_FLOAT_IMPL
#define MICROPY_FLOAT_IMPL (MICROPY_FLOAT_IMPL_DOUBLE)

// Driver soft-reset hook (stops LofiFren timer/core1/DMA before the heap is reset).
#include "supercalc_board_hooks.h"
