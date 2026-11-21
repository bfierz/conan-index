from conan import ConanFile
from conan.errors import ConanException, ConanInvalidConfiguration
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get
import os


required_conan_version = ">=2.0.9"


class McNopperEglConan(ConanFile):
    name = "mcnopper-egl"
    description = "Portable EGL 1.5 implementation for Windows (OpenGL on WGL, with Vulkan HDR), exposed like egl/system"
    license = "MIT"
    url = "https://github.com/bfierz/conan-index"
    homepage = "https://github.com/McNopper/EGL"
    topics = ("egl", "opengl", "wgl", "windows")
    package_type = "static-library"
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        # The Windows backend presents through Vulkan. Only the headers and the loader are needed, no SDK.
        self.requires("vulkan-headers/[>=1.3 <2]")
        self.requires("vulkan-loader/[>=1.3 <2]")

    def validate(self):
        # Linux has egl/system in ConanCenter. Upstream's Linux backends are X11/Wayland based and are not packaged here.
        if self.settings.os != "Windows":
            raise ConanInvalidConfiguration(f"{self.ref} supports Windows only; use egl/system on Linux")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["EGL_BUILD_EXAMPLES"] = False
        # ANGLE is optional and loaded at runtime; upstream gets it from vcpkg, which is not used here
        tc.cache_variables["EGL_WIN_ENABLE_ANGLE"] = False
        # Upstream calls find_package(Vulkan) with the CMake module. Point it at the Conan packages
        # instead of an installed Vulkan SDK.
        headers = self.dependencies["vulkan-headers"].cpp_info
        loader = self.dependencies["vulkan-loader"].cpp_info
        tc.cache_variables["Vulkan_INCLUDE_DIR"] = headers.includedirs[0].replace("\\", "/")
        tc.cache_variables["Vulkan_LIBRARY"] = os.path.join(loader.libdirs[0], "vulkan-1.lib").replace("\\", "/")
        tc.generate()
        CMakeDeps(self).generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "*.h", os.path.join(self.source_folder, "include"), os.path.join(self.package_folder, "include"))
        # Upstream has no install rules and writes the archive to <source>/lib/<build tree name>/libEGL.lib,
        # so look for it below both the source and the build folder instead of assuming a path
        archives = [os.path.join(root, name)
                    for folder in (self.source_folder, self.build_folder)
                    for root, _, names in os.walk(folder) for name in names
                    if name.lower() == "libegl.lib"]
        if not archives:
            found = [os.path.join(root, name) for root, _, names in os.walk(self.source_folder) for name in names
                     if name.lower().endswith(".lib")]
            raise ConanException(f"libEGL.lib was not built; archives found: {found}")
        copy(self, os.path.basename(archives[0]), os.path.dirname(archives[0]),
             os.path.join(self.package_folder, "lib"))

    def package_info(self):
        # Same package and target names as ConanCenter's egl/system, so consumers need no OS branch
        self.cpp_info.set_property("cmake_file_name", "egl")
        self.cpp_info.set_property("cmake_target_name", "egl::egl")
        self.cpp_info.libs = ["libEGL"]
        self.cpp_info.system_libs = ["opengl32"]
        # Upstream marks the headers as statically linked for every consumer
        self.cpp_info.defines = ["KHRONOS_STATIC"]
