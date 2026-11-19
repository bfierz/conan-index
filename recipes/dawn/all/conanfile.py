from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get, rm, rmdir
from conan.tools.microsoft import is_msvc, is_msvc_static_runtime
from conan.tools.scm import Version
from conan.tools.system.package_manager import Apt
import os


required_conan_version = ">=2.0.9"


class DawnConan(ConanFile):
    name = "dawn"
    description = "Dawn, a WebGPU implementation"
    license = "BSD-3-Clause"
    homepage = "https://dawn.googlesource.com/dawn"
    url = "https://github.com/bfierz/conan-index"
    topics = ("rendering", "webgpu")
    package_type = "shared-library"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "d3d11": [True, False],
        "d3d12": [True, False],
        "vulkan": [True, False],
        "metal": [True, False],
    }
    default_options = {
        "d3d11": True,
        "d3d12": True,
        "vulkan": True,
        "metal": True,
    }

    @property
    def _min_cppstd(self):
        # Dawn and its public webgpu_cpp.h moved to C++20 between M130 (C++17) and M139
        return 17 if Version(self.version) < "139" else 20

    @property
    def _compilers_minimum_version(self):
        if self._min_cppstd == 17:
            return {
                "apple-clang": "10",
                "clang": "7",
                "gcc": "7",
                "msvc": "191",
            }
        return {
            "apple-clang": "14",
            "clang": "12",
            "gcc": "10",
            "msvc": "193",
        }

    def config_options(self):
        if self.settings.os != "Windows":
            del self.options.d3d11
            del self.options.d3d12

        if self.settings.os == "Macos":
            del self.options.vulkan
        else:
            del self.options.metal

    def layout(self):
        cmake_layout(self, src_folder="src")

    def validate(self):
        check_min_cppstd(self, self._min_cppstd)
        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
        if minimum_version and Version(self.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration(
                f"{self.ref} requires C++{self._min_cppstd}, which your compiler does not support."
            )

    def build_requirements(self):
        self.tool_requires("ninja/[>=1.11 <2]")

    def system_requirements(self):
        # X11 surface support and the OpenGL backends need these headers on Linux
        Apt(self).install([
            "libx11-xcb-dev", "libxrandr-dev", "libxinerama-dev", "libxcursor-dev",
            "libxi-dev", "mesa-common-dev", "libgl-dev",
        ])

    def source(self):
        # googlesource "+archive" tarballs are generated on request and have no
        # stable checksum, so conandata.yml carries no sha256.
        get(self, **self.conan_data["sources"][self.version], strip_root=False)

    def generate(self):
        # Single-config generator: Dawn derives its debug settings (DAWN_ENABLE_ASSERTS, ...)
        # from CMAKE_BUILD_TYPE, which multi-config generators such as Visual Studio leave empty
        tc = CMakeToolchain(self, generator="Ninja")

        # Dawn fetches its third-party dependencies itself (needs git and python on PATH)
        tc.cache_variables["DAWN_FETCH_DEPENDENCIES"] = True

        # Single shared library with an install target
        # Since M140 the option is a string (SHARED/STATIC/OFF), before it was a boolean
        if Version(self.version) >= "140":
            tc.cache_variables["DAWN_BUILD_MONOLITHIC_LIBRARY"] = "SHARED"
        else:
            tc.cache_variables["DAWN_BUILD_MONOLITHIC_LIBRARY"] = True
        tc.cache_variables["DAWN_ENABLE_INSTALL"] = True
        if self.settings.os != "Windows":
            tc.cache_variables["DAWN_ENABLE_PIC"] = True

        # Only build the library
        tc.cache_variables["DAWN_BUILD_SAMPLES"] = False
        tc.cache_variables["DAWN_BUILD_TESTS"] = False
        tc.cache_variables["TINT_BUILD_TESTS"] = False
        tc.cache_variables["TINT_BUILD_CMD_TOOLS"] = False
        tc.cache_variables["DAWN_USE_GLFW"] = False

        # Backends
        tc.cache_variables["DAWN_ENABLE_D3D11"] = bool(self.options.get_safe("d3d11", False))
        tc.cache_variables["DAWN_ENABLE_D3D12"] = bool(self.options.get_safe("d3d12", False))
        tc.cache_variables["DAWN_ENABLE_VULKAN"] = bool(self.options.get_safe("vulkan", False))
        tc.cache_variables["DAWN_ENABLE_METAL"] = bool(self.options.get_safe("metal", False))

        # Load d3dcompiler_47.dll and vulkan-1.dll from System32. Without this, newer Dawn
        # only looks next to webgpu_dawn.dll and the executable (the bare-name fallback uses
        # LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR and fails with ERROR_INVALID_PARAMETER), and the
        # package ships neither DLL. Older releases have no such option and use LoadLibraryA.
        if self.settings.os == "Windows":
            tc.cache_variables["DAWN_FORCE_SYSTEM_COMPONENT_LOAD"] = True

        if is_msvc(self):
            tc.cache_variables["USE_MSVC_RUNTIME_LIBRARY_DLL"] = not is_msvc_static_runtime(self)

        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "share"))
        rm(self, "*.la", os.path.join(self.package_folder, "lib"))
        rm(self, "*.pdb", os.path.join(self.package_folder, "lib"))
        rm(self, "*.pdb", os.path.join(self.package_folder, "bin"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "dawn")
        self.cpp_info.set_property("cmake_target_name", "dawn::webgpu_dawn")
        self.cpp_info.libs = ["webgpu_dawn"]

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.extend(["m", "pthread", "dl"])
