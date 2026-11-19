from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get, replace_in_file
import os


required_conan_version = ">=2.0.9"


class ImFileDialogConan(ConanFile):
    name = "imfiledialog"
    description = "A file dialog library for Dear ImGui"
    license = "MIT"
    url = "https://github.com/bfierz/conan-index"
    homepage = "https://github.com/dfranx/ImFileDialog"
    topics = ("imgui", "file-dialog", "gui")
    # Upstream has no export macros, so only a static library is offered
    package_type = "static-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "fPIC": [True, False],
    }
    default_options = {
        "fPIC": True,
    }

    @property
    def _min_cppstd(self):
        return 17

    def export_sources(self):
        copy(self, "CMakeLists.txt", self.recipe_folder, self.export_sources_folder)
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        # ImFileDialog.h exposes no imgui or stb types; both are used in the .cpp only.
        # Upstream 0a74b05 targets imgui 1.90 (deprecated API removed); the patch adds 1.91.4+ and 1.92.
        self.requires("imgui/[>=1.90 <2]")
        self.requires("stb/cci.20240531")

    def validate(self):
        check_min_cppstd(self, self._min_cppstd)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)
        # Upstream expects imgui in an "imgui/" subfolder; the imgui package puts it at the include root
        cpp = os.path.join(self.source_folder, "ImFileDialog.cpp")
        replace_in_file(self, cpp, "#include <imgui/imgui.h>", "#include <imgui.h>")
        replace_in_file(self, cpp, "#include <imgui/imgui_internal.h>", "#include <imgui_internal.h>")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["IMFILEDIALOG_SRC_DIR"] = self.source_folder.replace("\\", "/")
        tc.generate()
        CMakeDeps(self).generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder=os.path.join(self.source_folder, os.pardir))
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "imfiledialog")
        self.cpp_info.set_property("cmake_target_name", "imfiledialog::imfiledialog")
        self.cpp_info.libs = ["imfiledialog"]
        if self.settings.os == "Windows":
            self.cpp_info.system_libs = ["shell32", "advapi32"]
        elif self.settings.os in ("Linux", "FreeBSD"):
            self.cpp_info.system_libs = ["pthread"]
