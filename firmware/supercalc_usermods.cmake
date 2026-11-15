# SuperCalc.OG — top-level USER_C_MODULES file for the custom PicoCalc UF2.
# Passed to MicroPython's rp2 port as: make BOARD=RPI_PICO2_W USER_C_MODULES=<this file>
# (tools/build_supercalc.sh does this for you).
#
# External source trees come from environment variables set by build_supercalc.sh:
#   PICOCALC_DRIVER_DIR  LofiFren-PicoCalc/MicroPython dir (picocalcdisplay, vtterminal, picosampler)
#   EIGENMATH_DIR        zenodante/eigenmath_micropython checkout
# Defaults assume the Dropbox layout: PicoCalc/LofiFren-PicoCalc next to PicoCalc/SuperCalc.OG.

get_filename_component(SUPERCALC_ROOT "${CMAKE_CURRENT_LIST_DIR}/.." ABSOLUTE)

if(DEFINED ENV{PICOCALC_DRIVER_DIR})
    set(PICOCALC_DRIVER_DIR "$ENV{PICOCALC_DRIVER_DIR}")
else()
    get_filename_component(PICOCALC_DRIVER_DIR "${SUPERCALC_ROOT}/../LofiFren-PicoCalc/MicroPython" ABSOLUTE)
endif()

if(NOT DEFINED ENV{EIGENMATH_DIR})
    message(FATAL_ERROR "SuperCalc: set EIGENMATH_DIR to a zenodante/eigenmath_micropython checkout")
endif()
set(EIGENMATH_DIR "$ENV{EIGENMATH_DIR}")

# 1. PicoCalc base drivers, identical to the stock LofiFren v1.25 firmware
#    (picocalcdisplay + vtterminal + picosampler C modules; picocalc.py stays on /modules).
include(${PICOCALC_DRIVER_DIR}/micropython.cmake)

# 2. SuperCalc native math kernel (import picocalc_math -> HAS_C_MATH True)
include(${SUPERCALC_ROOT}/src/math/micropython.cmake)

# 3. Eigenmath CAS (import eigenmath; eigenmath.EigenMath(heap_bytes)).
#    Note: its micropython.cmake forces PICO_STACK_SIZE=0x4000.
include(${EIGENMATH_DIR}/micropython.cmake)
