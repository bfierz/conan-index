cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CXX)

find_package(vcl REQUIRED CONFIG)

# The SIMD compiler flags come with the vcl targets, the C++ standard from the profile
add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} PRIVATE vcl::core vcl::math vcl::geometry vcl::components vcl::compute vcl::graphics)

# Each enabled graphics backend adds a source file and a TEST_<BACKEND> define
if(TEST_OPENGL)
	target_sources(${PROJECT_NAME} PRIVATE test_opengl.cpp)
	target_compile_definitions(${PROJECT_NAME} PRIVATE TEST_OPENGL)
	# EGL is tested as part of OpenGL
	if(TEST_EGL)
		target_compile_definitions(${PROJECT_NAME} PRIVATE TEST_EGL)
	endif()
endif()
if(TEST_D3D12)
	target_sources(${PROJECT_NAME} PRIVATE test_d3d12.cpp)
	target_compile_definitions(${PROJECT_NAME} PRIVATE TEST_D3D12)
endif()
if(TEST_VULKAN)
	target_sources(${PROJECT_NAME} PRIVATE test_vulkan.cpp)
	target_compile_definitions(${PROJECT_NAME} PRIVATE TEST_VULKAN)
endif()
if(TEST_WEBGPU)
	target_sources(${PROJECT_NAME} PRIVATE test_webgpu.cpp)
	target_compile_definitions(${PROJECT_NAME} PRIVATE TEST_WEBGPU)
endif()
