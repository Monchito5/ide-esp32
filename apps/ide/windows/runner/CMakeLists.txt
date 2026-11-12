cmake_minimum_required(VERSION 3.14)
project(runner LANGUAGES CXX)

# Some setups build this file directly without the top-level CMake defining
# BINARY_NAME, or they may leave it set to a keyword such as "PRIVATE".
# Guard against that so the generated runner target remains valid and CMake
# does not interpret "PRIVATE" as the target name.
if(NOT DEFINED BINARY_NAME OR BINARY_NAME STREQUAL "" OR BINARY_NAME STREQUAL "PRIVATE")
  set(BINARY_NAME "runner")
endif()

# Some generated Flutter project layouts do not expose apply_standard_settings()
# from the top-level build. Define it locally so the runner target can still
# use the standard C++ settings expected by the template.
function(apply_standard_settings target)
  if(NOT target)
    set(target "${BINARY_NAME}")
  endif()

  if(NOT target)
    return()
  endif()

  if(MSVC)
    target_compile_options(${target} PRIVATE /W4 /wd"4100")
  else()
    target_compile_options(${target} PRIVATE -Wall -Wextra -Wpedantic)
  endif()

  set_target_properties(${target} PROPERTIES
    CXX_STANDARD 17
    CXX_STANDARD_REQUIRED YES
    CXX_EXTENSIONS NO
  )
endfunction()

# Define the application target. To change its name, change BINARY_NAME in the
# top-level CMakeLists.txt, not the value here, or `flutter run` will no longer
# work.
#
# Any new source files that you add to the application should be added here.
# Some generated Flutter projects do not define FLUTTER_MANAGED_DIR or may not
# have a generated_plugin_registrant.cc file yet. Guard the registration source
# so the runner still configures correctly when the generated file is absent.
set(RUNNER_SOURCES
  "flutter_window.cpp"
  "main.cpp"
  "utils.cpp"
  "win32_window.cpp"
  "Runner.rc"
  "runner.exe.manifest"
)

if(DEFINED FLUTTER_MANAGED_DIR AND NOT FLUTTER_MANAGED_DIR STREQUAL "" AND EXISTS "${FLUTTER_MANAGED_DIR}/generated_plugin_registrant.cc")
  list(APPEND RUNNER_SOURCES "${FLUTTER_MANAGED_DIR}/generated_plugin_registrant.cc")
endif()

add_executable(${BINARY_NAME} WIN32 ${RUNNER_SOURCES})

# Apply the standard set of build settings. This can be removed for applications
# that need different build settings.
apply_standard_settings(${BINARY_NAME})

# Add preprocessor definitions for the build version.
target_compile_definitions(${BINARY_NAME} PRIVATE "FLUTTER_VERSION=\"${FLUTTER_VERSION}\"")
target_compile_definitions(${BINARY_NAME} PRIVATE "FLUTTER_VERSION_MAJOR=${FLUTTER_VERSION_MAJOR}")
target_compile_definitions(${BINARY_NAME} PRIVATE "FLUTTER_VERSION_MINOR=${FLUTTER_VERSION_MINOR}")
target_compile_definitions(${BINARY_NAME} PRIVATE "FLUTTER_VERSION_PATCH=${FLUTTER_VERSION_PATCH}")
target_compile_definitions(${BINARY_NAME} PRIVATE "FLUTTER_VERSION_BUILD=${FLUTTER_VERSION_BUILD}")

# Disable Windows macros that collide with C++ standard library functions.
target_compile_definitions(${BINARY_NAME} PRIVATE "NOMINMAX")

# Add dependency libraries and include directories. Add any application-specific
# dependencies here.
target_link_libraries(${BINARY_NAME} PRIVATE flutter flutter_wrapper_app)
target_link_libraries(${BINARY_NAME} PRIVATE "dwmapi.lib")
target_include_directories(${BINARY_NAME} PRIVATE "${CMAKE_SOURCE_DIR}")

# Run the Flutter tool portions of the build. This must not be removed.
# Guard against standalone or partial CMake setups that do not define
# flutter_assemble, which can happen when the runner is built directly.
if(TARGET flutter_assemble)
  add_dependencies(${BINARY_NAME} flutter_assemble)
endif()
