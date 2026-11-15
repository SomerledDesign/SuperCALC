// SuperCalc.OG: forced-include header for the double-precision build.
// tools/build_supercalc.sh passes "-I<this dir> -include supercalc_float_double.h"
// through CFLAGS_EXTRA (MicroPython applies CFLAGS_EXTRA to both the compiler and
// the qstr preprocessor). It only points MicroPython's documented MP_CONFIGFILE hook
// at our overlay, so the MicroPython tree itself is never edited.
#ifndef SUPERCALC_FLOAT_DOUBLE_H
#define SUPERCALC_FLOAT_DOUBLE_H
#define MP_CONFIGFILE "supercalc_mpconfigport_double.h"
#endif
