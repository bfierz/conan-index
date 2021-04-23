set PACKAGE=%1
set PACKAGE_VERSION=%2
set PROFILE=%3
set TMP_FOLDER=%TMP%\%PACKAGE%-%PACKAGE_VERSION%

REM Prepare environment to build the correct version
conan install . %PACKAGE%/%PACKAGE_VERSION%@  --install-folder=%TMP_FOLDER%\install %PROFILE%

REM Fetch the source
conan source  . --source-folder=%TMP_FOLDER%\source --install-folder=%TMP_FOLDER%\install

REM Build the source
conan build   . --source-folder=%TMP_FOLDER%\source --install-folder=%TMP_FOLDER%\install --build-folder=%TMP_FOLDER%\build --package-folder=%TMP_FOLDER%\package

REM Copy the file for packaging
conan package . --source-folder=%TMP_FOLDER%\source --install-folder=%TMP_FOLDER%\install --build-folder=%TMP_FOLDER%\build --package-folder=%TMP_FOLDER%\package

REM Export package
conan export-pkg . %PACKAGE%/%PACKAGE_VERSION%@ --package-folder=%TMP_FOLDER%\package --force

REM Test package from exported folder
conan test test_package %PACKAGE%/%PACKAGE_VERSION%@ %PROFILE%
