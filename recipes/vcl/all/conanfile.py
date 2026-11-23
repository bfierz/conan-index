from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get, rmdir
from conan.tools.microsoft import is_msvc
from conan.tools.scm import Version
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
    # The graphics backend options are named as in upstream's conanfile.py.
    # CI (pr-check.yml) builds only the default options; with_webgpu is verified by hand,
    # because building Dawn from source takes hours.
    options = {
        "fPIC": [True, False],
        # SIMD instruction set; vcl's headers switch on it, so consumers get its compiler flags
        "vectorize": ["generic", "sse2", "sse3", "ssse3", "sse4.1", "sse4.2", "avx", "avx2", "avx512", "neon"],
        "with_opengl": [True, False],
        "with_egl": [True, False],
        "with_d3d12": [True, False],
        "with_vulkan": [True, False],
        "with_webgpu": [True, False],
    }
    default_options = {
        "fPIC": True,
        "vectorize": "sse4.1",
        "with_opengl": False,
        "with_egl": False,
        "with_d3d12": False,
        "with_vulkan": False,
        "with_webgpu": False,
    }

    # Per `vectorize` value: VCL_VECTORIZE, the arch family it needs (None: any), and the PUBLIC
    # compile options vcl_configure sets for it (src/cmake/VCLConfig.cmake), which CMakeDeps does
    # not see. "*_32bit" flags are added on 32-bit archs only. MSVC on x86_64 has SSE 2 to SSE 4.2
    # without a flag, ARM64 has NEON without a flag, and /arch:VFPv4 only exists for 32-bit ARM.
    _vectorizations = {
        "generic": {"vcl": "Generic", "arch": None},
        "sse2": {"vcl": "SSE 2", "arch": "x86", "gcc": ["-msse2"], "msvc_32bit": ["/arch:SSE2"]},
        "sse3": {"vcl": "SSE 3", "arch": "x86", "gcc": ["-msse3"]},
        "ssse3": {"vcl": "SSSE 3", "arch": "x86", "gcc": ["-mssse3"]},
        "sse4.1": {"vcl": "SSE 4.1", "arch": "x86", "gcc": ["-msse4.1"]},
        "sse4.2": {"vcl": "SSE 4.2", "arch": "x86", "gcc": ["-msse4.2"]},
        "avx": {"vcl": "AVX", "arch": "x86", "gcc": ["-mavx"], "msvc": ["/arch:AVX"]},
        "avx2": {"vcl": "AVX 2", "arch": "x86", "gcc": ["-mavx2"], "msvc": ["/arch:AVX2"]},
        "avx512": {"vcl": "AVX 512", "arch": "x86", "gcc": ["-mavx512f", "-mavx512vl", "-mavx512dq"], "msvc": ["/arch:AVX512"]},
        "neon": {"vcl": "NEON", "arch": "arm", "gcc_32bit": ["-mfloat-abi=hard", "-mfpu=neon"], "msvc_32bit": ["/arch:VFPv4"]},
    }

    @property
    def _vectorization(self):
        return self._vectorizations[str(self.options.vectorize)]

    @property
    def _min_cppstd(self):
        return 17

    @property
    def _compilers_minimum_version(self):
        # First versions with C++17 support
        return {
            "apple-clang": "10",
            "clang": "7",
            "gcc": "7",
            "msvc": "191",
        }

    @property
    def _is_x86(self):
        return str(self.settings.arch) in ("x86", "x86_64")

    @property
    def _is_arm(self):
        return str(self.settings.arch).startswith(("arm", "aarch"))

    @property
    def _with_native_webgpu(self):
        # WebGPU through Dawn; Emscripten ships its own WebGPU bindings
        return self.options.with_webgpu and self.settings.os != "Emscripten"

    @property
    def _egl(self):
        # The Conan reference and the component to require; both export the CMake target egl::egl.
        # mcnopper-egl comes from this index.
        if self.settings.os == "Windows":
            return {"ref": "mcnopper-egl/1.0.19", "component": "mcnopper-egl::mcnopper-egl"}
        return {"ref": "egl/system", "component": "egl::egl"}

    @property
    def _simd_flags(self):
        # The gcc flags also apply to Clang, as in vcl_configure
        compiler = "msvc" if is_msvc(self) else "gcc"
        is_32bit = str(self.settings.arch) in ("x86", "armv7", "armv7hf", "armv7s", "armv7k")
        flags = list(self._vectorization.get(compiler, []))
        if is_32bit:
            flags.extend(self._vectorization.get(f"{compiler}_32bit", []))
        if compiler == "gcc" and self.settings.os == "Emscripten" and self.options.vectorize != "generic":
            flags.append("-msimd128")
        return flags

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        else:
            # Direct3D 12 is only packaged for Windows
            del self.options.with_d3d12
        if self.settings.os == "Emscripten":
            # Emscripten provides OpenGL ES through WebGL; upstream has no EGL support there
            del self.options.with_egl
        # The default is upstream's (SSE 4.1); ARM falls back to NEON, any other arch to Generic
        if self._is_arm:
            self.options.vectorize = "neon"
        elif not self._is_x86:
            self.options.vectorize = "generic"

    def configure(self):
        # EGL creates OpenGL contexts
        if not self.options.with_opengl:
            self.options.rm_safe("with_egl")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        # Versions as in upstream's conanfile.py. All of them appear in vcl's public headers.
        self.requires("eigen/3.4.1", transitive_headers=True)
        self.requires("abseil/20250814.2", transitive_headers=True)
        self.requires("fmt/11.2.0", transitive_headers=True)
        if self.options.with_opengl and self.settings.os != "Emscripten":
            # vcl's OpenGL headers include <GL/glew.h>. The system OpenGL is driver-bound.
            # Emscripten's own OpenGL replaces both (src/libs/vcl.graphics/CMakeLists.txt).
            self.requires("opengl/system", transitive_headers=True)
            self.requires("glew/2.2.0", transitive_headers=True)
            if self.options.get_safe("with_egl"):
                # vcl's OpenGL context header includes <EGL/egl.h>
                self.requires(self._egl["ref"], transitive_headers=True)
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
        if self._with_native_webgpu:
            # dawn comes from this index. vcl uses only its C API (webgpu/webgpu.h), so vcl stays
            # on C++17, while Dawn itself needs C++20: profiles set dawn/*:compiler.cppstd=20.
            self.requires("dawn/159.0.8154", transitive_headers=True)

    def validate(self):
        check_min_cppstd(self, self._min_cppstd)
        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
        if minimum_version and Version(self.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration(
                f"{self.ref} requires C++{self._min_cppstd}, which your compiler does not support."
            )
        arch_family = self._vectorization["arch"]
        if arch_family == "arm" and not self._is_arm:
            raise ConanInvalidConfiguration(f"{self.ref}: vectorize={self.options.vectorize} needs an ARM arch, not {self.settings.arch}")
        if arch_family == "x86" and not self._is_x86:
            raise ConanInvalidConfiguration(f"{self.ref}: vectorize={self.options.vectorize} needs an x86 arch, not {self.settings.arch}")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        # The C++ standard comes from the profile's compiler.cppstd (CMAKE_CXX_STANDARD)
        tc = CMakeToolchain(self)
        tc.cache_variables["VCL_BUILD_TESTS"] = False
        tc.cache_variables["VCL_BUILD_BENCHMARKS"] = False
        tc.cache_variables["VCL_BUILD_EXAMPLES"] = False
        tc.cache_variables["VCL_BUILD_TOOLS"] = False
        tc.cache_variables["VCL_VECTORIZE"] = self._vectorization["vcl"]
        tc.cache_variables["VCL_OPENGL_SUPPORT"] = bool(self.options.with_opengl)
        tc.cache_variables["VCL_EGL_SUPPORT"] = bool(self.options.get_safe("with_egl"))
        tc.cache_variables["VCL_D3D12_SUPPORT"] = bool(self.options.get_safe("with_d3d12"))
        tc.cache_variables["VCL_VULKAN_SUPPORT"] = bool(self.options.with_vulkan)
        tc.cache_variables["VCL_WEBGPU_SUPPORT"] = bool(self.options.with_webgpu)
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
        # vcl_configure (src/cmake/VCLConfig.cmake) sets these PUBLIC, but CMakeDeps does not see
        # them. Its PUBLIC warning flags are left out: consumers choose their own warnings.
        core.cxxflags = self._simd_flags
        if is_msvc(self):
            # Exceptions and RTTI
            core.cxxflags.extend(["/EHsc", "/GR"])
        if self.settings.compiler in ("clang", "apple-clang"):
            core.defines = ["__STRICT_ANSI__"]
        self._add_component("math", "vcl.math", ["core"])
        self._add_component("geometry", "vcl.geometry", ["core"])
        self._add_component("components", "vcl.components", ["core"])
        self._add_component("compute", "vcl_compute", ["core"])

        # vcl_graphics is built in every configuration. Each enabled backend adds its
        # requires, defines and system libraries (src/libs/vcl.graphics/CMakeLists.txt).
        graphics_requires = ["core", "abseil::abseil"]
        graphics_defines = []
        graphics_system_libs = []
        if self.options.with_opengl:
            graphics_defines.append("VCL_OPENGL_SUPPORT")
            if self.settings.os != "Emscripten":
                graphics_requires.extend(["opengl::opengl", "glew::glew"])
            if self.options.get_safe("with_egl"):
                graphics_requires.append(self._egl["component"])
                graphics_defines.append("VCL_EGL_SUPPORT")
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
        if self.options.with_webgpu:
            graphics_defines.append("VCL_WEBGPU_SUPPORT")
            if self._with_native_webgpu:
                graphics_requires.append("dawn::dawn")
        graphics = self._add_component("graphics", "vcl_graphics", graphics_requires)
        graphics.defines = graphics_defines
        graphics.system_libs = graphics_system_libs
