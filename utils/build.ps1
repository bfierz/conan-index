$env:CONAN_LOGIN_USERNAME_UPSTREAM=""
$env:CONAN_PASSWORD_UPSTREAM=""

$env:CONAN_UPLOAD="@True@upstream"

$env:CONAN_ARCHS="x86_64"
$env:CONAN_BUILD_TYPES="Debug,Release"
$env:CONAN_VISUAL_VERSIONS="16"
$env:CONAN_VISUAL_RUNTIMES="MD,MDd"

$env:CONAN_USERNAME="b4z"
$env:CONAN_CHANNEL="testing"

$env:CONAN_REFERENCE="vcl/20210108"
$env:CONAN_BUILD_ALL_OPTIONS_VALUES="vcl:vectorization,vcl:d3d12,vcl:opengl"
python $PSScriptRoot/build.py
