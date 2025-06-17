from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get, replace_in_file, rm, rmdir
from conan.tools.microsoft import check_min_vs, is_msvc, is_msvc_static_runtime
from conan.tools.scm import Version
import os


required_conan_version = ">=1.53.0"


class DawnConan(ConanFile):
    name = "dawn"
    
    description = "Dawn, a WebGPU implementation"
    topics = ("Rendering")
    homepage = "https://dawn.googlesource.com/dawn"
    url = "https://github.com/conan-io/conan-center-index"
    license = "BSD 3-Clause License"
    topics = ("Rendering", "WebGPU")
    package_type = "shared-library"

    settings = "os", "arch", "compiler", "build_type"
    options = {
            "d3d11": [True, False],
            "d3d12": [True, False],
            "vulkan": [True, False],
            "metal": [True, False]
    }
    default_options = {
            "d3d11": True,
            "d3d12": True,
            "vulkan": True,
            "metal": True
    }

    @property
    def _min_cppstd(self):
        return 17

    @property
    def _compilers_minimum_version(self):
        return {
            "apple-clang": "10",
            "clang": "7",
            "gcc": "7",
            "msvc": "191",
            "Visual Studio": "19",
        }

    def config_options(self):

        if self.settings.os != 'Windows':
            del self.options.d3d11
            del self.options.d3d12
        
        if self.settings.os != 'Macos':
            del self.options.metal
        else:
            del self.options.vulkan

    def layout(self):
        cmake_layout(self, src_folder="src")

    def validate(self):
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, self._min_cppstd)
        minimum_version = self._compilers_minimum_version.get(str(self.settings.compiler), False)
        if minimum_version and Version(self.settings.compiler.version) < minimum_version:
            raise ConanInvalidConfiguration(
                f"{self.ref} requires C++{self._min_cppstd}, which your compiler does not support."
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=False)

    def generate(self):
        tc = CMakeToolchain(self)

        #  Automatically fetch the required dependencies
        tc.variables["DAWN_FETCH_DEPENDENCIES"] = True

        #  Generate install target
        tc.variables["DAWN_ENABLE_INSTALL"] = True

        # Backends
        tc.variables["DAWN_ENABLE_D3D11"] = bool(self.options.d3d11) if "d3d11" in self.options else False
        tc.variables["DAWN_ENABLE_D3D12"] = bool(self.options.d3d12) if "d3d12" in self.options else False
        tc.variables["DAWN_ENABLE_VULKAN"] = bool(self.options.vulkan) if "vulkan" in self.options else False
        tc.variables["DAWN_ENABLE_METAL"] = bool(self.options.metal) if "metal" in self.options else False

        if is_msvc(self):
            # Don't use self.settings.compiler.runtime
            tc.variables["USE_MSVC_RUNTIME_LIBRARY_DLL"] = not is_msvc_static_runtime(self)

        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

        # some files extensions and folders are not allowed. Please, read the FAQs to get informed.
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "share"))
        rm(self, "*.la", os.path.join(self.package_folder, "lib"))
        rm(self, "*.pdb", os.path.join(self.package_folder, "lib"))
        rm(self, "*.pdb", os.path.join(self.package_folder, "bin"))

    def package_info(self):
        self.cpp_info.libs = ["webgpu_dawn"]

        self.cpp_info.set_property("cmake_file_name", "dawn")
        self.cpp_info.set_property("cmake_target_name", "dawn::webgpu_dawn")
        
        # If they are needed on Linux, m, pthread and dl are usually needed on FreeBSD too
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("m")
            self.cpp_info.system_libs.append("pthread")
            self.cpp_info.system_libs.append("dl")

        # TODO: to remove in conan v2 once cmake_find_package_* generators removed
        self.cpp_info.filenames["cmake_find_package"] = "DAWN"
        self.cpp_info.filenames["cmake_find_package_multi"] = "dawn"
        self.cpp_info.names["cmake_find_package"] = "DAWN"
        self.cpp_info.names["cmake_find_package_multi"] = "dawn"
