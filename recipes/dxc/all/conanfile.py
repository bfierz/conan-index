from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import copy, get
import os


required_conan_version = ">=2.0.0"


class DxcConan(ConanFile):
    name = "dxc"
    description = "DirectX Shader Compiler: compiles HLSL to DXIL and SPIR-V (prebuilt release binaries)"
    license = ("NCSA", "MIT")
    url = "https://github.com/bfierz/conan-index"
    homepage = "https://github.com/microsoft/DirectXShaderCompiler"
    topics = ("hlsl", "dxil", "spirv", "shader-compiler", "directx", "pre-built")
    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"

    # Release assets per OS, and the arch folder names inside the Windows zip.
    # The Linux tarball ships x86_64 only and has no arch folders.
    _windows_arch = {"x86_64": "x64", "x86": "x86", "armv8": "arm64"}

    def layout(self):
        self.folders.source = "src"

    def package_id(self):
        # Prebuilt binaries: only the platform matters
        del self.info.settings.compiler
        del self.info.settings.build_type

    def validate(self):
        os_ = str(self.settings.os)
        arch = str(self.settings.arch)
        if os_ not in self.conan_data["sources"][self.version]:
            raise ConanInvalidConfiguration(f"{self.ref} has no prebuilt release for {os_}")
        if os_ == "Windows" and arch not in self._windows_arch:
            raise ConanInvalidConfiguration(f"{self.ref} has no prebuilt Windows release for {arch}")
        if os_ == "Linux" and arch != "x86_64":
            raise ConanInvalidConfiguration(f"{self.ref} has no prebuilt Linux release for {arch}")

    def build(self):
        # The archive depends on the OS, so it is fetched here rather than in source()
        get(self, **self.conan_data["sources"][self.version][str(self.settings.os)],
            destination=self.source_folder)

    def package(self):
        src = self.source_folder
        licenses = os.path.join(self.package_folder, "licenses")
        copy(self, "LICEN*", src, licenses)

        if self.settings.os == "Windows":
            arch = self._windows_arch[str(self.settings.arch)]
            copy(self, "*", os.path.join(src, "bin", arch), os.path.join(self.package_folder, "bin"))
            copy(self, "*.lib", os.path.join(src, "lib", arch), os.path.join(self.package_folder, "lib"))
            # Match the Linux layout: <dxc/dxcapi.h>, <hlsl/...>
            inc = os.path.join(src, "inc")
            include = os.path.join(self.package_folder, "include")
            copy(self, "*", os.path.join(inc, "hlsl"), os.path.join(include, "hlsl"))
            copy(self, "*", inc, os.path.join(include, "dxc"), excludes=("hlsl/*", "hlsl\\*"))
            copy(self, "LICEN*", os.path.join(inc, "hlsl"), licenses)
        else:
            copy(self, "*", os.path.join(src, "bin"), os.path.join(self.package_folder, "bin"))
            copy(self, "*", os.path.join(src, "lib"), os.path.join(self.package_folder, "lib"))
            copy(self, "*", os.path.join(src, "include"), os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "dxc")
        self.cpp_info.set_property("cmake_target_name", "dxc::dxcompiler")
        self.cpp_info.libs = ["dxcompiler"]
        self.cpp_info.includedirs = ["include", os.path.join("include", "dxc")]
        # The bin dir goes on PATH for consumers that use dxc as a tool_requires.
        # The Linux binary finds lib/libdxcompiler.so through its $ORIGIN/../lib rpath.
        self.cpp_info.bindirs = ["bin"]
