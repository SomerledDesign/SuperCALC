// SuperCalc.OG: MP_CONFIGFILE overlay for ports/rp2, single-precision floats
// (rp2 default, unchanged). Adds only the driver soft-reset hook.
#include <mpconfigport.h>

// Driver soft-reset hook (stops LofiFren timer/core1/DMA before the heap is reset).
#include "supercalc_board_hooks.h"
