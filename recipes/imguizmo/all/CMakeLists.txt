cmake_minimum_required(VERSION 3.15)
project(imguizmo LANGUAGES CXX)

find_package(imgui CONFIG REQUIRED)

file(GLOB IMGUIZMO_SOURCES "${IMGUIZMO_SRC_DIR}/src/*.cpp")
file(GLOB IMGUIZMO_HEADERS "${IMGUIZMO_SRC_DIR}/src/*.h")

add_library(imguizmo ${IMGUIZMO_SOURCES})
target_include_directories(imguizmo PUBLIC $<BUILD_INTERFACE:${IMGUIZMO_SRC_DIR}/src>)
target_compile_definitions(imguizmo PRIVATE IMGUI_DEFINE_MATH_OPERATORS)
target_link_libraries(imguizmo PUBLIC imgui::imgui)
set_target_properties(imguizmo PROPERTIES WINDOWS_EXPORT_ALL_SYMBOLS ON)

install(TARGETS imguizmo
	ARCHIVE DESTINATION lib
	LIBRARY DESTINATION lib
	RUNTIME DESTINATION bin
)
install(FILES ${IMGUIZMO_HEADERS} DESTINATION include)
