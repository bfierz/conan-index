$env:CONAN_LOGIN_USERNAME_UPSTREAM="b4z"
$env:CONAN_PASSWORD_UPSTREAM="qso7aRsHZQLVH3vz"

$env:CONAN_UPLOAD="https://b4z.jfrog.io/artifactory/api/conan/conan@True@upstream"

$env:CONAN_ARCHS="x86_64"
$env:CONAN_BUILD_TYPES="Debug,Release"
$env:CONAN_VISUAL_VERSIONS="16"
$env:CONAN_VISUAL_RUNTIMES="MD,MDd"

$env:CONAN_USERNAME="b4z"
$env:CONAN_CHANNEL="testing"

$env:CONAN_REFERENCE="vcl/20210108"
$env:CONAN_BUILD_ALL_OPTIONS_VALUES="vcl:vectorization,vcl:d3d12,vcl:opengl"
python $PSScriptRoot/build.py
