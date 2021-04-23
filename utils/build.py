import conans
import yaml

from cpt.packager import ConanMultiPackager

# All yaml serialization of conan version object used by the ConanMultiPackager (forwarded to the conanfile)
def ConansVersion_representer(dumper, data):
    return dumper.represent_str(str(data))

if __name__ == "__main__":
    # Register type serializer for yaml
    yaml.add_representer(conans.model.version.Version, ConansVersion_representer, yaml.SafeDumper)

    builder = ConanMultiPackager()
    builder.add_common_builds()
    for settings, options, env_vars, build_requires in builder.builds:
        if settings["compiler"] == "clang":
            env_vars["CC"] = "/usr/bin/clang-" + settings["compiler.version"]
            env_vars["CXX"] = "/usr/bin/clang++-" + settings["compiler.version"]
        elif settings["compiler"] == "gcc":
            env_vars["CC"] = "/usr/bin/gcc-" + settings["compiler.version"]
            env_vars["CXX"] = "/usr/bin/g++-" + settings["compiler.version"]
    builder.run()
