from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get, replace_in_file, rm, rmdir
from conan.tools.microsoft import check_min_vs, is_msvc, is_msvc_static_runtime
from conan.tools.scm import Version
import os


required_conan_version = ">=2.0.0"


class SlangConan(ConanFile):
    name = "slang"
    
    description = "Slang shading language compiler"
    topics = ("Rendering")
    homepage = "http://shader-slang.com/"
    url = "https://github.com/shader-slang/slang"
    license = "Apache-2.0 WITH LLVM-exception"
    topics = ("Rendering", "Slang")
    package_type = "application"

    settings = "os", "arch"
    options = {
    }
    default_options = {
    }

    def build(self):
        os = {"Windows": "windows", "Linux": "linux", "Macos": "macos"}.get(str(self.settings.os))
        arch = str(self.settings.arch).lower()
        url = f"https://github.com/shader-slang/slang/releases/download/v{self.version}/slang-{self.version}-{os}-{arch}.tar.gz"
        get(self, url)

    def package(self):
        copy(self, "*", os.path.join(self.build_folder, "bin"), os.path.join(self.package_folder, "bin"))
        copy(self, "*.h", os.path.join(self.build_folder, "include"), os.path.join(self.package_folder, "include"))
        copy(self, "*.lib", os.path.join(self.build_folder, "lib"), os.path.join(self.package_folder, "lib"))
        copy(self, "*.a", os.path.join(self.build_folder, "lib"), os.path.join(self.package_folder, "lib"))

    def package_info(self):
        self.buildenv_info.append("PATH", os.path.join(self.package_folder, "bin"))
