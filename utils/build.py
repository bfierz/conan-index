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
    builder.run()
