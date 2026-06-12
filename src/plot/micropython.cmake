# CMake fragment for picocalc_plot user C module (SuperCalc.OG Phase 3+)
# Include alongside the math and vm ones in the base firmware's USER_C_MODULES build
# (LofiFren / zenodante style). The top-level micropython build will pull these.
add_library(usermod_picocalc_plot INTERFACE)
target_sources(usermod_picocalc_plot INTERFACE ${CMAKE_CURRENT_LIST_DIR}/picocalc_plot.c)
target_include_directories(usermod_picocalc_plot INTERFACE ${CMAKE_CURRENT_LIST_DIR})
target_link_libraries(usermod INTERFACE usermod_picocalc_plot)
