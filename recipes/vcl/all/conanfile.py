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
    # The graphics backend options are named as in upstream's conanfile.py
    options = {
        "fPIC": [True, False],
        "with_opengl": [True, False],
        "with_egl": [True, False],
    }
    default_options = {
        "fPIC": True,
        "with_opengl": False,
        "with_egl": False,
    }

    # Graphics backend option -> VCL_* cache variable, which vcl also defines PUBLIC on vcl_graphics
    _graphics_backends = {
        "with_opengl": "VCL_OPENGL_SUPPORT",
        "with_egl": "VCL_EGL_SUPPORT",
    }

    # Instruction set passed as VCL_VECTORIZE; it is upstream's default
    _vectorize = "SSE 4.1"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

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
        for ref in self._graphics_requires:
            self.requires(ref, transitive_headers=True)

    @property
    def _graphics_requires(self):
        # What vcl::graphics links, per enabled backend; empty without a backend.
        # vcl's public headers include all of them.
        refs = []
        if self.options.with_opengl:
            # The system OpenGL is driver-bound
            refs += ["opengl/system", "glew/2.2.0"]
            if self.options.with_egl:
                # mcnopper-egl comes from this index; both export egl::egl
                refs.append("mcnopper-egl/1.0.19" if self.settings.os == "Windows" else "egl/system")
        return refs

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
        for option, variable in self._graphics_backends.items():
            tc.cache_variables[variable] = bool(self.options.get_safe(option))
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

        # vcl_graphics is always built, but only packaged as a component with a backend
        graphics_requires = self._graphics_requires
        if graphics_requires:
            names = [ref.split("/")[0] for ref in graphics_requires]
            graphics = self._add_component("graphics", "vcl_graphics", ["core"] + [f"{name}::{name}" for name in names])
            graphics.defines = [variable for option, variable in self._graphics_backends.items() if self.options.get_safe(option)]
