cmake_minimum_required(VERSION 3.14)
project(test_package)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()

find_package(llvm)

add_executable(${PROJECT_NAME} test_package.cpp)
target_compile_features(${PROJECT_NAME} PRIVATE cxx_std_14)

if(TARGET llvm::interpreter)  # static libraries
    target_link_libraries(${PROJECT_NAME} PRIVATE
        llvm::interpreter
        llvm::irreader
        llvm::x86codegen
    )
else()  # shared library
    target_link_libraries(${PROJECT_NAME} llvm::llvm)
endif()
