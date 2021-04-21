import glob
import shutil
import os
from conans import ConanFile, CMake, tools

class VclConan(ConanFile):
    name = "vcl"
    
    description = "Visual Computing Library (VCL)"
    topics = ("Visual Computing")

    homepage = "https://github.com/bfierz/vcl"
    url = "https://github.com/conan-io/conan-center-index"

    license = "MIT License"

    exports_sources = ["CMakeLists.txt", "patches/**"]
    generators = "cmake"

    settings = "os", "arch", "compiler", "build_type"
    options = {
            "vectorization": ["AVX", "AVX 2", "SSE 4.2" ], 
            "d3d12": [True, False],
            "opengl": [True, False],
            "fPIC": [True, False]
            }
    default_options = {
            "vectorization": "AVX",
            "d3d12": False,
            "opengl": False,
            "fPIC": True
    }
    _cmake = None

    def requirements(self):
        self.requires("abseil/20200923.2")
        self.requires("eigen/3.3.9")
        self.requires("fmt/7.1.3")

        if self.options.opengl:
            self.requires("glew/2.1.0")

    @property
    def _source_subfolder(self):
        return "source_subfolder"
    @property
    def _build_subfolder(self):
        return "build_subfolder"

    def config_options(self):

        if self.settings.os == 'Windows':
            del self.options.fPIC
        else:
            del self.options.d3d12
            self.options["abseil"].fPIC = self.options.fPIC
            self.options["glew"].fPIC = self.options.fPIC

    def configure(self):
        minimal_cpp_standard = "14"
        if self.settings.compiler.cppstd:
            tools.check_min_cppstd(self, 14)

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        extracted_dir = glob.glob('vcl-*/')[0]
        os.rename(extracted_dir, self._source_subfolder)
        
        for patch in self.conan_data.get("patches", {}).get(self.version, []):
            tools.patch(**patch)
        
    def _configure_cmake(self):
        cmake = CMake(self)

        # Conan configuration
        cmake.definitions["CONAN_CMAKE_INSTALL_DIR"] = self.install_folder

        # Configure which parts to build
        cmake.definitions["VCL_BUILD_BENCHMARKS"] = False
        cmake.definitions["VCL_BUILD_TESTS"] = False
        cmake.definitions["VCL_BUILD_TOOLS"] = False
        cmake.definitions["VCL_BUILD_EXAMPLES"] = False

        # Configure features
        cmake.definitions["VCL_CXX_STANDARD"] = self.settings.compiler.cppstd if self.settings.compiler.cppstd else 14
        cmake.definitions["VCL_VECTORIZE"] = str(self.options.vectorization)
        if self.options.opengl:
            cmake.definitions["VCL_OPENGL_SUPPORT"] = True
        if hasattr(self.options, "d3d12") and self.options.d3d12:
            cmake.definitions["VCL_D3D12_SUPPORT"] = True
        if self.settings.os != "Windows":
            cmake.definitions["CMAKE_POSITION_INDEPENDENT_CODE"] = self.options.fPIC

        # Configure external targets
        cmake.definitions["vcl_ext_absl"] = "CONAN_PKG::abseil"
        cmake.definitions["vcl_ext_eigen"] = "CONAN_PKG::eigen"
        cmake.definitions["vcl_ext_fmt"] = "CONAN_PKG::fmt"
        if self.options.opengl:
            cmake.definitions["vcl_ext_glew"] = "CONAN_PKG::glew"

        return cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.configure(build_folder=self._build_subfolder)

        cmake.build(target="vcl_core")
        cmake.build(target="vcl.components")
        cmake.build(target="vcl_compute")
        cmake.build(target="vcl.geometry")
        cmake.build(target="vcl_graphics")
        cmake.build(target="vcl.math")

        cmake.install()

    def package(self):
        # Only copy missing files, not covered by cmake install, to the package folder
        self.copy(pattern="LICENSE", dst="licenses", src=os.path.join(self.source_folder, self._source_subfolder))

    def package_info(self):
        self.cpp_info.defines = []
        if self.options.opengl:
            self.cpp_info.defines.append('VCL_OPENGL_SUPPORT')
        if hasattr(self.options, "d3d12") and self.options.d3d12:
            self.cpp_info.defines.append('VCL_D3D12_SUPPORT')

        self.cpp_info.includedirs = ['include/vcl_core', 'include/vcl.geometry', 'include/vcl_graphics', 'include/vcl.math']
        if self.settings.os == "Windows":
            self.cpp_info.libs = ['vcl_core.lib', 'vcl.math.lib', 'vcl.geometry.lib', 'vcl_graphics.lib']
        else:
            self.cpp_info.libs = ['libvcl_core.a', 'libvcl.math.a', 'libvcl.geometry.a', 'libvcl_graphics.a']
        self.cpp_info.libdirs = [ "lib" ]
