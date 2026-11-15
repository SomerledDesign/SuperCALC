// SuperCalc.OG: board hooks shared by the single- and double-float config overlays.
// Included at the end of supercalc_mpconfigport_{single,double}.h, after the rp2
// port's mpconfigport.h has provided its (empty) default.
//
// ports/rp2/main.c calls MICROPY_BOARD_START_SOFT_RESET() first thing on every soft
// reset, before DMA/PIO/thread/soft-timer teardown and before the GC heap is swept
// and re-initialised. The LofiFren driver modules (patched by
// firmware/patches/lofifren-vtterminal-supercalc.patch) use it to stop their
// repeating timer, core-1 display refresh and audio DMA and drop their raw pointers
// into Python buffers, so nothing keeps writing/reading the old heap.
#ifndef SUPERCALC_BOARD_HOOKS_H
#define SUPERCALC_BOARD_HOOKS_H

void vtterminal_soft_reset(void);
void picocalcdisplay_soft_reset(void);
void picosampler_soft_reset(void);

#undef MICROPY_BOARD_START_SOFT_RESET
#define MICROPY_BOARD_START_SOFT_RESET() do { \
        vtterminal_soft_reset(); \
        picocalcdisplay_soft_reset(); \
        picosampler_soft_reset(); \
} while (0)

// Raw-paste flow-control window (pyexec.c sends window = MICROPY_REPL_STDIN_BUFFER_MAX/2
// as a 2-byte little-endian header right after "R\x01"). The stock 256 gives 0x80 0x00:
// mp_hal_stdout_tx_strn() mirrors it to os.dupterm, the PicoCalc vt.py stream does
// bytes.decode() on it, 0x80 is not valid UTF-8 -> UnicodeError -> MicroPython prints
// "dupterm: Exception in write() method, deactivating: ..." on USB in the middle of the
// paste -> mpremote "unexpected read during raw paste: b'd'" (payloads > 1 window).
// 252 -> window 126 = 0x7E 0x00: plain ASCII, nothing for vt.py to choke on, and not 0x7F
// (vtterminal treats DEL as backspace). SuperCalc 20261114e.
#undef MICROPY_REPL_STDIN_BUFFER_MAX
#define MICROPY_REPL_STDIN_BUFFER_MAX (252)

#endif
