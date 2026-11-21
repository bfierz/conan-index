from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get
import os


required_conan_version = ">=2.0.9"


class ImGuizmoConan(ConanFile):
    name = "imguizmo"
    description = "Immediate mode 3D gizmo for scene editing and other controls based on Dear Imgui"
    license = "MIT"
    url = "https://github.com/bfierz/conan-index"
    homepage = "https://github.com/CedricGuillemet/ImGuizmo"
    topics = ("imgui", "3d", "graphics", "gizmo")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}

    def export_sources(self):
        copy(self, "CMakeLists.txt", self.recipe_folder, self.export_sources_folder)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        # ConanCenter's imguizmo/cci.20231114 uses ImGui::BeginChildFrame, which imgui 1.92 removed.
        # This snapshot of upstream master builds against imgui >= 1.92.
        self.requires("imgui/[>=1.92 <2]", transitive_headers=True)

    def validate(self):
        check_min_cppstd(self, 14)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["IMGUIZMO_SRC_DIR"] = self.source_folder.replace("\\", "/")
        tc.generate()
        CMakeDeps(self).generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder=os.path.join(self.source_folder, os.pardir))
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        CMake(self).install()

    def package_info(self):
        self.cpp_info.libs = ["imguizmo"]
        self.cpp_info.set_property("cmake_file_name", "imguizmo")
        self.cpp_info.set_property("cmake_target_name", "imguizmo::imguizmo")
