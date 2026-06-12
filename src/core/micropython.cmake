# CMake fragment for picocalc_vm user C module (SuperCalc.OG Phase 2+)
# Include alongside the math one in the base firmware's USER_C_MODULES build
# (LofiFren / zenodante style). The top-level micropython build will pull these.
add_library(usermod_picocalc_vm INTERFACE)
target_sources(usermod_picocalc_vm INTERFACE ${CMAKE_CURRENT_LIST_DIR}/picocalc_vm.c)
target_include_directories(usermod_picocalc_vm INTERFACE ${CMAKE_CURRENT_LIST_DIR})
target_link_libraries(usermod INTERFACE usermod_picocalc_vm)
