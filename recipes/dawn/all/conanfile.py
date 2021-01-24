import glob
import pathlib
import os
import shutil
from conans import ConanFile, CMake, tools

class LibnameConan(ConanFile):
    name = "dawn"
    
    description = "Dawn, a WebGPU implementation"
    topics = ("Rendering")

    homepage = "https://dawn.googlesource.com/dawn"
    url = "https://github.com/conan-io/conan-center-index"

    license = "Apache 2.0 Public License"

    exports_sources = ["patches/**"]
    generators = "cmake"

    # Enforce short paths due to long paths of sub-modules
    short_paths = True

    # Avoid copying source to the huge number of files
    no_copy_source = True

    settings = "os", "arch", "compiler", "build_type"
    options = {
            "shared": [True, False],
            "d3d12": [True, False],
            "vulkan": [True, False],
            "metal": [True, False],
            "fPIC": [True, False]
            }
    default_options = {
            "shared": False,
            "d3d12": True,
            "vulkan": True,
            "metal": True,
            "fPIC": True
    }

    def requirements(self):
        pass

    @property
    def _depot_tools_subfolder(self):
        return "depot_tools"
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
        
        if self.settings.os != 'Macos':
            del self.options.metal

    def configure(self):
        minimal_cpp_standard = "14"
        if self.settings.compiler.cppstd:
            tools.check_min_cppstd(self, 14)

    def checkout(self, url, commit):

        git = tools.Git(folder=self._source_subfolder)
        git.clone(url)
        git.checkout(element=commit)

    def source(self):

        # Download Google Depot Tools to build Dawn
        depot_tools_git = tools.Git(folder=self._depot_tools_subfolder)
        depot_tools_git.clone("https://chromium.googlesource.com/chromium/tools/depot_tools.git")
        depot_tools_git.checkout(element='main')
        os.environ['PATH'] = f"{self.source_folder}/{self._depot_tools_subfolder}{os.pathsep}{os.environ.get('PATH')}"

        self.checkout(**self.conan_data["sources"][self.version])

        with tools.chdir(self._source_subfolder):

            # Avoid downloading bundled toolchain (only works from within Google)
            if self.settings.os == 'Windows':
                os.environ["DEPOT_TOOLS_WIN_TOOLCHAIN"] = "0"

            shutil.copyfile("scripts/standalone.gclient", ".gclient")
            self.run("gclient sync")

        for patch in self.conan_data.get("patches", {}).get(self.version, []):
            tools.patch(**patch)

    def build(self):
        os.environ['PATH'] = f"{self.source_folder}/{self._depot_tools_subfolder}{os.pathsep}{os.environ.get('PATH')}"
        with tools.chdir(f"{self.source_folder}/{self._source_subfolder}"):
            local_build_folder = f"{self.build_folder}/{self._build_subfolder}"
            pathlib.Path(local_build_folder).mkdir(parents=False, exist_ok=True)

            with open(f"{local_build_folder}/args.gn", "w") as file:
                file.write("is_clang=false\n")
                file.write("visual_studio_version=\"2019\"\n")

                if self.settings.build_type == "Debug":
                    file.write("is_debug=true\n")
                    file.write("enable_iterator_debugging=true\n")
                    file.write("symbol_level=2\n")
                else:
                    file.write("is_debug=false\n")
                    file.write("enable_iterator_debugging=false\n")
                    file.write("symbol_level=0\n")

                if self.options.shared == False:
                    file.write("dawn_complete_static_libs=true\n")

                file.write("dawn_enable_d3d12={}\n".format('true' if self.options.get_safe("d3d12") else 'false'))
                file.write("dawn_enable_vulkan={}\n".format('true' if self.options.get_safe("vulkan") else 'false'))
                file.write("dawn_enable_metal={}\n".format('true' if self.options.get_safe("metal") else 'false'))

                # Disable legacy backends
                file.write("dawn_enable_opengl=false\n")
                file.write("dawn_use_angle=false\n")

            self.run(f'gn gen {local_build_folder} --target_cpu="x64"')
            self.run(f"ninja -C {local_build_folder} dawn_native_shared dawn_proc_shared dawncpp")

            # Build static library from 'webgpu_cpp.cpp' to fix the conan packaging approach
            pathlib.Path(f"{self.build_folder}/webgpucpp").mkdir(parents=False, exist_ok=True)
            with open(f"{self.build_folder}/webgpucpp/CMakeLists.txt", "w") as file:
                file.write(f"add_library(webgpu_cpp STATIC {local_build_folder}/gen/src/dawn/webgpu_cpp.cpp)\n")
                file.write(f"target_include_directories(webgpu_cpp PRIVATE\n")
                file.write(f"{local_build_folder}/gen/src/include\n")
                file.write(f"{self.source_folder}/{self._source_subfolder}/src/include)\n")

            cmake = CMake(self)
            cmake.configure(source_folder=f"{self.build_folder}/webgpucpp", build_folder=f"{self.build_folder}/webgpucpp/build")
            cmake.build()

    def package(self):

        local_source_folder = f"{self.source_folder}/{self._source_subfolder}"
        local_build_folder = f"{self.build_folder}/{self._build_subfolder}"
        dawn_inc_folder = f"{local_source_folder}/src/include"
        dawn_gen_inc_folder = f"{local_build_folder}/gen/src/include"

        self.copy(pattern="LICENSE", dst="licenses", src=local_source_folder)
        self.copy("dawn_*.dll", dst="bin", src=local_build_folder)
        self.copy("dawn_*.lib", dst="lib", src=local_build_folder)
        self.copy("dawn_*.so", dst="bin", src=local_build_folder)
        self.copy("dawn_*.a", dst="lib", src=local_build_folder)

        self.copy("webgpu_cpp.lib", dst="lib", src=f"{self.build_folder}/webgpucpp/build")

        self.copy("*.h", dst="include", src=dawn_inc_folder)
        self.copy("*.h", dst="include", src=dawn_gen_inc_folder)
        self.copy("*.inl", dst="include", src=dawn_inc_folder)
        self.copy("*.inl", dst="include", src=dawn_gen_inc_folder)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
