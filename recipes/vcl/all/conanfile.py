import glob
import shutil
import os
from conans import ConanFile, CMake, tools

class LibnameConan(ConanFile):
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
            "multi_build": [True, False],
            "vectorization": ["AVX", "AVX 2", "SSE 4.2" ], 
            "d3d12": [True, False],
            "opengl": [True, False],
            "fPIC": [True, False]
            }
    default_options = {
            "multi_build": False,
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

        # Support multi-package configuration
        if self.options.multi_build:
            del self.settings.build_type
            if self.settings.compiler == "Visual Studio":
                del self.settings.compiler["Visual Studio"].runtime

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

        # Configure which parts to build
        cmake.definitions["VCL_BUILD_BENCHMARKS"] = False
        cmake.definitions["VCL_BUILD_TESTS"] = False
        cmake.definitions["VCL_BUILD_TOOLS"] = False
        cmake.definitions["VCL_BUILD_EXAMPLES"] = False

        # Support multi-package configuration
        if not hasattr(self.settings, "build_type"):
            cmake.definitions["CMAKE_DEBUG_POSTFIX"] = "_d"

        # Configure features
        cmake.definitions["VCL_CXX_STANDARD"] = self.settings.compiler.cppstd if self.settings.compiler.cppstd else 14
        cmake.definitions["VCL_VECTORIZE"] = str(self.options.vectorization)
        if self.options.opengl:
            cmake.definitions["VCL_OPENGL_SUPPORT"] = True
        if self.options.get_safe("d3d12"):
            cmake.definitions["VCL_D3D12_SUPPORT"] = self.options.d3d12
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

        if not hasattr(self.settings, "build_type"):
            if cmake.is_multi_configuration:
                cmake.build(target="vcl_core",     args=["--config","Debug"])
                cmake.build(target="vcl.geometry", args=["--config","Debug"])
                cmake.build(target="vcl_graphics", args=["--config","Debug"])
                cmake.build(target="vcl.math",     args=["--config","Debug"])
                cmake.build(target="vcl_core",     args=["--config","Release"])
                cmake.build(target="vcl.geometry", args=["--config","Release"])
                cmake.build(target="vcl_graphics", args=["--config","Release"])
                cmake.build(target="vcl.math",     args=["--config","Release"])
            else:
                for config in ("Debug", "Release"):
                    self.output.info("Building %s" % config)
                    cmake.definitions["CMAKE_BUILD_TYPE"] = config
                    cmake.configure(build_folder=self._build_subfolder)
                    shutil.rmtree("CMakeFiles")
                    os.remove("CMakeCache.txt")
        else:
            cmake.build(target="vcl_core")
            cmake.build(target="vcl.geometry")
            cmake.build(target="vcl_graphics")
            cmake.build(target="vcl.math")

        cmake.install()
    def package(self):

        bin_folder = os.path.join(self._build_subfolder, "bin")
        lib_folder = os.path.join(self._build_subfolder, "lib")
        inc_folder = os.path.join(self._source_subfolder, "include")
        
        self.copy(pattern="LICENSE", dst="licenses", src=self._source_subfolder)
        self.copy("*.dll", dst="bin", src=bin_folder)
        self.copy("*.a", dst="lib", src=lib_folder)
        self.copy("*.lib", dst="lib", src=lib_folder)
        self.copy("*.h", dst="include", src=inc_folder)
        self.copy("*.inl", dst="include", src=inc_folder)

    def package_info(self):

        self.cpp_info.defines = []
        if self.options.opengl:
            self.cpp_info.defines.append('VCL_OPENGL_SUPPORT')
        if self.options.get_safe("d3d12"):
            self.cpp_info.defines.append('VCL_D3D12_SUPPORT')

        self.cpp_info.includedirs = ['include/vcl_core', 'include/vcl.geometry', 'include/vcl_graphics', 'include/vcl.math']
        if self.settings.os == "Windows":
            # ideally it should be possible to have avx compilation flags forwarded from the recipe
            # but the current management of nvcc integration doesn't play well with cflags and cxxflags
            # avx_flag = ""
            # if self.options.vectorization == "AVX":
            #     avx_flag = "/arch:AVX"
            # if self.options.vectorization == "AVX 2":
            #     avx_flag = "/arch:AVX2"
            # self.cpp_info.cflags = [avx_flag]
            # self.cpp_info.cxxflags = [avx_flag]
            
            if not hasattr(self.settings, "build_type"):
                self.cpp_info.debug.libs = ['vcl_core_d.lib', 'vcl.math_d.lib', 'vcl.geometry_d.lib', 'vcl_graphics_d.lib']
                self.cpp_info.release.libs = ['vcl_core.lib', 'vcl.math.lib', 'vcl.geometry.lib', 'vcl_graphics.lib']
            else:
                self.cpp_info.libs = ['vcl_core.lib', 'vcl.math.lib', 'vcl.geometry.lib', 'vcl_graphics.lib']
        else:
            # ideally it should be possible to have avx compilation flags forwarded from the recipe
            # but the current management of nvcc integration doesn't play well with cflags and cxxflags
            # avx_flag = ""
            # if self.options.vectorization == "AVX":
            #     avx_flag = "-mavx"
            # if self.options.vectorization == "AVX 2":
            #     avx_flag = "-mavx2"
            # if self.options.vectorization == "SSE 4.2":
            #     avx_flag = "-msse4.2"
            # self.cpp_info.cflags = [avx_flag]
            # self.cpp_info.cxxflags = [avx_flag]

            self.cpp_info.libs = ['libvcl_core.a', 'libvcl.math.a', 'libvcl.geometry.a', 'libvcl_graphics.a']
        self.cpp_info.libdirs = [ "lib" ]
