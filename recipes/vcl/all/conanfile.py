from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get, rmdir
from conan.tools.microsoft import is_msvc
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
        # SIMD instruction set; vcl's headers switch on it, so consumers get its compiler flags
        "vectorize": ["generic", "sse2", "sse3", "ssse3", "sse4.1", "sse4.2", "avx", "avx2", "avx512", "neon"],
    }
    default_options = {"fPIC": True, "vectorize": "sse4.1"}

    # Option value -> VCL_VECTORIZE (src/cmake/VCLConfig.cmake)
    _vcl_vectorize = {
        "generic": "Generic",
        "sse2": "SSE 2",
        "sse3": "SSE 3",
        "ssse3": "SSSE 3",
        "sse4.1": "SSE 4.1",
        "sse4.2": "SSE 4.2",
        "avx": "AVX",
        "avx2": "AVX 2",
        "avx512": "AVX 512",
        "neon": "NEON",
    }

    @property
    def _is_x86(self):
        return str(self.settings.arch) in ("x86", "x86_64")

    @property
    def _is_arm(self):
        return str(self.settings.arch).startswith(("arm", "aarch"))

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        # The default is upstream's (SSE 4.1); ARM falls back to NEON, any other arch to Generic
        if self._is_arm:
            self.options.vectorize = "neon"
        elif not self._is_x86:
            self.options.vectorize = "generic"

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        # Versions as in upstream's conanfile.py. All of them appear in vcl's public headers.
        self.requires("eigen/3.4.1", transitive_headers=True)
        self.requires("abseil/20250814.2", transitive_headers=True)
        self.requires("fmt/11.2.0", transitive_headers=True)

    def validate(self):
        check_min_cppstd(self, 17)
        vectorize = str(self.options.vectorize)
        if vectorize == "neon" and not self._is_arm:
            raise ConanInvalidConfiguration(f"{self.ref}: vectorize=neon needs an ARM arch, not {self.settings.arch}")
        if vectorize not in ("generic", "neon") and not self._is_x86:
            raise ConanInvalidConfiguration(f"{self.ref}: vectorize={vectorize} needs an x86 arch, not {self.settings.arch}")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        # The C++ standard comes from the profile's compiler.cppstd (CMAKE_CXX_STANDARD)
        tc = CMakeToolchain(self)
        tc.cache_variables["VCL_BUILD_TESTS"] = False
        tc.cache_variables["VCL_BUILD_BENCHMARKS"] = False
        tc.cache_variables["VCL_BUILD_EXAMPLES"] = False
        tc.cache_variables["VCL_BUILD_TOOLS"] = False
        tc.cache_variables["VCL_VECTORIZE"] = self._vcl_vectorize[str(self.options.vectorize)]
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
        # The PUBLIC compile options of vcl's targets for VCL_VECTORIZE (src/cmake/VCLConfig.cmake),
        # which CMakeDeps does not see
        vectorize = str(self.options.vectorize)
        is_32bit = str(self.settings.arch) in ("x86", "armv7", "armv7hf", "armv7s", "armv7k")
        if is_msvc(self):
            # MSVC on x86_64 has SSE 2 to SSE 4.2 without a flag
            flags = {"avx512": ["/arch:AVX512"], "avx2": ["/arch:AVX2"], "avx": ["/arch:AVX"]}
            if is_32bit:
                # ARM64 has NEON without a flag, and /arch:VFPv4 only exists for 32-bit ARM
                flags.update({"sse2": ["/arch:SSE2"], "neon": ["/arch:VFPv4"]})
            return flags.get(vectorize, [])
        flags = {
            "avx512": ["-mavx512f", "-mavx512vl", "-mavx512dq"],
            "avx2": ["-mavx2"],
            "avx": ["-mavx"],
            "sse4.2": ["-msse4.2"],
            "sse4.1": ["-msse4.1"],
            "ssse3": ["-mssse3"],
            "sse3": ["-msse3"],
            "sse2": ["-msse2"],
            "neon": ["-mfloat-abi=hard", "-mfpu=neon"] if is_32bit else [],
        }.get(vectorize, [])
        if self.settings.os == "Emscripten" and vectorize != "generic":
            flags.append("-msimd128")
        return flags

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
