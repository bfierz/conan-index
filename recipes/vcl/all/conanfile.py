from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get, rmdir
import os


required_conan_version = ">=2.0.9"


class VclConan(ConanFile):
    name = "vcl"
    description = "Visual Computing Library (VCL)"
    license = "MIT"
    url = "https://github.com/bfierz/conan-index"
    homepage = "https://github.com/bfierz/vcl"
    topics = ("visual computing", "simd", "geometry", "graphics")
    # vcl only builds static libraries
    package_type = "static-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "fPIC": [True, False],
        "with_d3d12": [True, False],
        "with_vulkan": [True, False],
    }
    default_options = {
        "fPIC": True,
        "with_d3d12": False,
        "with_vulkan": False,
    }

    # Instruction set passed as VCL_VECTORIZE; it is upstream's default
    _vectorize = "SSE 4.1"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        else:
            # Direct3D 12 is only packaged for Windows
            del self.options.with_d3d12

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        # Versions as in upstream's conanfile.py. All of them appear in vcl's public headers.
        self.requires("eigen/3.4.1", transitive_headers=True)
        self.requires("abseil/20250814.2", transitive_headers=True)
        self.requires("fmt/11.2.0", transitive_headers=True)
        if self.options.get_safe("with_d3d12"):
            # vcl's D3D12 headers include <directx/d3dx12.h>
            self.requires("directx-headers/1.614.0", transitive_headers=True)
        if self.options.with_vulkan:
            # Only the vendor-neutral headers and the loader, which finds the driver at runtime:
            # no Vulkan SDK is needed. The validation layers are used at runtime only.
            # spirv-cross/cci.20211113 declares CMake < 3.5, which CMake 4 rejects when it is built
            # from source: the profile sets spirv-cross/*:CMAKE_POLICY_VERSION_MINIMUM=3.5 in [buildenv].
            self.requires("vulkan-headers/1.4.350.0", transitive_headers=True)
            self.requires("vulkan-loader/1.4.350.0")
            self.requires("spirv-cross/cci.20211113")

    def validate(self):
        check_min_cppstd(self, 17)
        if str(self.settings.arch) not in ("x86", "x86_64"):
            raise ConanInvalidConfiguration(f"{self.ref} is only configured for x86 SIMD (VCL_VECTORIZE={self._vectorize})")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        # The C++ standard comes from the profile's compiler.cppstd (CMAKE_CXX_STANDARD)
        tc = CMakeToolchain(self)
        tc.cache_variables["VCL_BUILD_TESTS"] = False
        tc.cache_variables["VCL_BUILD_BENCHMARKS"] = False
        tc.cache_variables["VCL_BUILD_EXAMPLES"] = False
        tc.cache_variables["VCL_BUILD_TOOLS"] = False
        tc.cache_variables["VCL_VECTORIZE"] = self._vectorize
        tc.cache_variables["VCL_D3D12_SUPPORT"] = bool(self.options.get_safe("with_d3d12"))
        tc.cache_variables["VCL_VULKAN_SUPPORT"] = bool(self.options.with_vulkan)
        tc.generate()
        CMakeDeps(self).generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        CMake(self).install()
        # CMakeDeps generates the config files from package_info()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    @property
    def _simd_flags(self):
        # The PUBLIC compile options of vcl's targets (src/cmake/VCLConfig.cmake), which CMakeDeps
        # does not see. MSVC on x86_64 has SSE 4.1 without a flag.
        if self.settings.compiler in ("gcc", "clang", "apple-clang", "intel-cc"):
            return ["-msse4.1"]
        return []

    def _add_component(self, name, lib, requires):
        component = self.cpp_info.components[name]
        component.set_property("cmake_target_name", f"vcl::{name}")
        component.libs = [lib]
        component.requires = requires
        return component

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "vcl")
        self.cpp_info.set_property("cmake_target_name", "vcl::vcl")

        core = self._add_component("core", "vcl_core", ["eigen::eigen", "abseil::abseil", "fmt::fmt"])
        core.cxxflags = self._simd_flags
        self._add_component("math", "vcl.math", ["core"])
        self._add_component("geometry", "vcl.geometry", ["core"])
        self._add_component("components", "vcl.components", ["core"])
        self._add_component("compute", "vcl_compute", ["core"])

        # vcl_graphics is built in every configuration. Each enabled backend adds its
        # requires, defines and system libraries (src/libs/vcl.graphics/CMakeLists.txt).
        graphics_requires = ["core", "abseil::abseil"]
        graphics_defines = []
        graphics_system_libs = []
        if self.options.get_safe("with_d3d12"):
            graphics_requires.append("directx-headers::directx-headers")
            graphics_defines.append("VCL_D3D12_SUPPORT")
            graphics_system_libs.extend(["d3d12", "dxgi", "dxguid"])
            if self.settings.compiler == "gcc":
                # MinGW's RPC headers declare an older version than the D3D12 headers require
                graphics_defines.append("__REQUIRED_RPCNDR_H_VERSION__=475")
        if self.options.with_vulkan:
            # spirv-cross is PRIVATE upstream, but vcl_graphics is static, so consumers link it
            graphics_requires.extend(["vulkan-headers::vulkan-headers", "vulkan-loader::vulkan-loader", "spirv-cross::spirv-cross"])
            graphics_defines.append("VCL_VULKAN_SUPPORT")
        graphics = self._add_component("graphics", "vcl_graphics", graphics_requires)
        graphics.defines = graphics_defines
        graphics.system_libs = graphics_system_libs
