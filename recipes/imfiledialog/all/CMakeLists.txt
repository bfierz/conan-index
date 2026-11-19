cmake_minimum_required(VERSION 3.15)
project(imfiledialog LANGUAGES CXX)

# Upstream ships only an example build, so the library is built from here.
# IMFILEDIALOG_SRC_DIR points at the extracted upstream sources.

find_package(imgui REQUIRED CONFIG)
find_package(stb REQUIRED CONFIG)

add_library(imfiledialog ${IMFILEDIALOG_SRC_DIR}/ImFileDialog.cpp)
target_include_directories(imfiledialog PUBLIC
	$<BUILD_INTERFACE:${IMFILEDIALOG_SRC_DIR}>
	$<INSTALL_INTERFACE:include>
)
target_compile_features(imfiledialog PUBLIC cxx_std_17)
target_link_libraries(imfiledialog PRIVATE imgui::imgui stb::stb)

if(WIN32)
	# Shell icons (SHGetFileInfo) and the user name (GetUserName)
	target_link_libraries(imfiledialog PRIVATE shell32 advapi32)
endif()

include(GNUInstallDirs)
install(TARGETS imfiledialog
	ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
	LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
	RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)
install(FILES ${IMFILEDIALOG_SRC_DIR}/ImFileDialog.h DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})
