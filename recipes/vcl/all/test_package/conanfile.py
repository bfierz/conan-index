from conan import ConanFile
from conan.errors import ConanException
from conan.tools.build import can_run
from conan.tools.cmake import cmake_layout, CMake, CMakeToolchain
import io
import os


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeDeps", "VirtualRunEnv"
    test_type = "explicit"

    def requirements(self):
        self.requires(self.tested_reference_str)

    def layout(self):
        cmake_layout(self)

    def generate(self):
        # One switch per graphics backend that the tested vcl package enables
        vcl_options = self.dependencies[self.tested_reference_str].options
        tc = CMakeToolchain(self)
        tc.cache_variables["TEST_OPENGL"] = bool(vcl_options.get_safe("with_opengl"))
        tc.cache_variables["TEST_EGL"] = bool(vcl_options.get_safe("with_egl"))
        tc.cache_variables["TEST_D3D12"] = bool(vcl_options.get_safe("with_d3d12"))
        # Exist on every OS: read them directly, so that a recipe without them fails here
        tc.cache_variables["TEST_VULKAN"] = bool(vcl_options.with_vulkan)
        tc.cache_variables["TEST_WEBGPU"] = bool(vcl_options.with_webgpu)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        if can_run(self):
            bin_path = os.path.join(self.cpp.build.bindir, "test_package")
            output = io.StringIO()
            self.run(bin_path, output, env="conanrun")
            # The package must be built for the instruction set its option selects
            vectorize = self.dependencies[self.tested_reference_str].options.vectorize
            # Compare whole lines: on Windows the program's output ends its lines with \r\n
            if f"vcl: instruction set {vectorize}" not in output.getvalue().splitlines():
                raise ConanException(f"vcl was not built for vectorize={vectorize}; test_package printed:\n{output.getvalue()}")
