// SuperCalc.OG: forced-include header for the single-precision build.
// Same mechanism as supercalc_float_double.h; floats stay at the rp2 default
// (single), only the board soft-reset hook is added.
#ifndef SUPERCALC_FLOAT_SINGLE_H
#define SUPERCALC_FLOAT_SINGLE_H
#define MP_CONFIGFILE "supercalc_mpconfigport_single.h"
#endif
