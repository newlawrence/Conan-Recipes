cmake_minimum_required(VERSION 2.8)
project(conanllvm)

message(STATUS "Conan CMake Wrapper")
include(${CMAKE_CURRENT_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()

add_subdirectory("source")
