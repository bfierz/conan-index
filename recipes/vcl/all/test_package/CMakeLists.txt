cmake_minimum_required(VERSION 3.1.0)
project(test_package CXX)

if(MSVC)
	set(CMAKE_C_FLAGS "/arch:AVX")
	set(CMAKE_CXX_FLAGS "/arch:AVX")
elseif(UNIX)
	set(CMAKE_C_FLAGS "-mavx")
	set(CMAKE_CXX_FLAGS "-mavx")
endif()

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup(TARGETS)

add_executable(${PROJECT_NAME} test_package.cpp)
conan_target_link_libraries(${PROJECT_NAME})
