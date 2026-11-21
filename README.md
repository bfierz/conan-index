# conan-index
Conan recipes for personal projects

## Development environment

Recipes are developed in an isolated environment:

- **Pinned Conan**: a Python virtual environment in `.venv` with the Conan
  version from [requirements.txt](requirements.txt) (also used by CI), plus a
  recent CMake from [requirements-dev.txt](requirements-dev.txt).
- **Separate Conan home**: [.conanrc](.conanrc) points Conan at `.conan2` in
  this repository. Packages, profiles, remotes and settings created here never
  touch your user-wide `~/.conan2`, and vice versa. Both folders are ignored by git.

### Setup

Windows (PowerShell):

```powershell
. .\tools\setup-dev.ps1
```

Linux (bash):

```bash
source tools/setup-dev.sh
```

The script creates the venv, installs the requirements, detects a default
profile (with `compiler.cppstd=20`, as CI uses), and activates the environment
in the current shell. It is safe to rerun. Run it again after changing a
requirements file, and to re-activate in a new shell. Use `-Reset` / `--reset`
to start over from an empty venv and Conan home.

### Usage

```powershell
conan create recipes/slang/all --version 2026.22 --build=missing
conan create recipes/dawn/all --version 159.0.8154 --build=missing -s build_type=Debug
```

Remotes other than ConanCenter must be added to the local home once, e.g.
`conan remote add <name> <url>`.

### Notes

- `.conanrc` applies to every Conan run inside this repository, including a
  user-wide install on `PATH`. To keep such a Conan from working on (and
  migrating) the local home, the setup script adds
  `core:required_conan_version=<pinned version>` to `.conan2/global.conf`, so
  any other version stops with an error. Activate the environment first.
- To upgrade Conan, change the version in `requirements.txt` and rerun the setup
  script.

## Pull request checks

[pr-check.yml](.github/workflows/pr-check.yml) runs on pull requests that touch `recipes/`:

- **Export**: every recipe version in the index is exported on Linux, which catches
  a recipe or `config.yml` that no longer parses.
- **Build**: the recipes the pull request changes (all versions listed in their
  `config.yml`) are built with `conan create` and their `test_package` is run, in
  Release with `compiler.cppstd=20`, on Linux and Windows. A recipe whose
  `validate()` rejects the platform is skipped there, not failed.

`python tools/changed-recipes.py [--all] [BASE_REF]` prints the selected recipe versions,
to preview what a pull request will build. The "Manual Deploy" workflow remains the way
to build Debug packages and to upload.
