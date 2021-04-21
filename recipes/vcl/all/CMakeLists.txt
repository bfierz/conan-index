cmake_minimum_required(VERSION 3.1.0)
project(cmake_wrapper)

include("${CONAN_CMAKE_INSTALL_DIR}/conanbuildinfo.cmake")
conan_basic_setup(TARGETS)

add_subdirectory("source_subfolder")
