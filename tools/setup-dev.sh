#!/usr/bin/env bash
# Sets up an isolated environment for developing the recipes in this repository.
#
#   source tools/setup-dev.sh          # set up and activate
#   source tools/setup-dev.sh --reset  # wipe .venv and .conan2 first
#
# Creates .venv with the Conan version pinned in requirements.txt (plus requirements-dev.txt) and uses the
# Conan home in .conan2, so the user-wide ~/.conan2 is untouched. Safe to rerun.

_setup_dev() {
    local root python venv conan_home
    root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    python="${PYTHON:-python3}"
    venv="$root/.venv"
    conan_home="$root/.conan2"

    if [ "${1:-}" = "--reset" ]; then
        rm -rf "$venv" "$conan_home"
    fi

    if [ ! -x "$venv/bin/python" ]; then
        echo "Creating virtual environment in $venv"
        "$python" -m venv "$venv" || return 1
    fi

    "$venv/bin/python" -m pip install --quiet --disable-pip-version-check --upgrade pip || return 1
    "$venv/bin/python" -m pip install --quiet --disable-pip-version-check -r "$root/requirements-dev.txt" || return 1

    # shellcheck disable=SC1091
    . "$venv/bin/activate"
    export CONAN_HOME="$conan_home"

    if [ ! -f "$conan_home/profiles/default" ]; then
        echo "Detecting default Conan profile"
        conan profile detect || return 1
        # Match the C++ standard the CI builds with by default
        sed -i 's/^compiler\.cppstd=.*/compiler.cppstd=20/' "$conan_home/profiles/default"
    fi

    # Make any other Conan (e.g. a user-wide install on PATH) refuse to work on
    # this Conan home, instead of silently migrating it to its own version.
    local pinned
    pinned="$(sed -n 's/^conan==\([^[:space:]]*\).*/\1/p' "$root/requirements.txt")"
    sed -i '/^core:required_conan_version/d' "$conan_home/global.conf"
    echo "core:required_conan_version=$pinned" >> "$conan_home/global.conf"

    echo
    echo "$(conan --version) with home $(conan config home)"
}

_setup_dev "$@"
_status=$?
unset -f _setup_dev
if [ "${BASH_SOURCE[0]}" = "$0" ]; then
    echo "Run 'source tools/setup-dev.sh' to keep the environment active in this shell."
    exit $_status
fi
return $_status
