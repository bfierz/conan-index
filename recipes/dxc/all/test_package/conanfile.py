from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.layout import basic_layout
import os


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "VirtualBuildEnv"
    test_type = "explicit"

    def layout(self):
        basic_layout(self)

    def build_requirements(self):
        self.tool_requires(self.tested_reference_str)

    def test(self):
        if can_run(self):
            self.run("dxc --version", env="conanbuild")
            shader = os.path.join(self.source_folder, "test_package.hlsl")
            # DXIL for D3D12 and SPIR-V for Vulkan, the two targets VCL uses
            dxil = os.path.join(self.build_folder, "test_package.dxil")
            spirv = os.path.join(self.build_folder, "test_package.spv")
            self.run(f'dxc -T ps_6_6 -E main "{shader}" -Fo "{dxil}"', env="conanbuild")
            self.run(f'dxc -spirv -T ps_6_6 -E main "{shader}" -Fo "{spirv}"', env="conanbuild")
