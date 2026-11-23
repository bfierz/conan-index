cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CXX)

find_package(vcl REQUIRED CONFIG)

# The SIMD compiler flags come with the vcl targets, the C++ standard from the profile
add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} PRIVATE vcl::core vcl::math vcl::geometry vcl::components vcl::compute)
