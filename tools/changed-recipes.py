#!/usr/bin/env python3
"""List the recipe versions a pull request touches, for the PR check workflow.

Usage: changed-recipes.py [--all] [BASE_REF]

Prints a JSON object {"include": [{"package": ..., "version": ..., "folder": ...}]}
that a GitHub Actions matrix can consume. Without --all, only recipes with
changed files (compared to the merge-base with BASE_REF, default origin/main)
are listed; with --all, every recipe version in the index is listed.
Recipes listed in EXCLUDED are never selected.
A change to a recipe's config.yml or to any file below its recipes/<name>/
directory selects every version of that recipe.
"""
import json
import subprocess
import sys
from pathlib import Path

import yaml

RECIPES = Path(__file__).resolve().parent.parent / "recipes"

# Recipes the checks skip, with the reason. Remove an entry once its recipe is
# ported, so that it is checked again.
EXCLUDED = {}


def changed_packages(base):
    out = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...HEAD", "--", "recipes"],
        check=True, capture_output=True, text=True, cwd=RECIPES.parent,
    ).stdout
    return {Path(p).parts[1] for p in out.splitlines() if len(Path(p).parts) > 2}


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    everything = "--all" in argv
    base = args[0] if args else "origin/main"

    packages = sorted(p.name for p in RECIPES.iterdir() if p.is_dir() and p.name not in EXCLUDED)
    if not everything:
        wanted = changed_packages(base)
        packages = [p for p in packages if p in wanted]

    include = []
    for package in packages:
        config = RECIPES / package / "config.yml"
        if not config.is_file():
            continue  # e.g. a recipe removed by the PR
        versions = yaml.safe_load(config.read_text())["versions"]
        for version, data in versions.items():
            include.append({"package": package, "version": str(version), "folder": data["folder"]})
    json.dump({"include": include}, sys.stdout)
    print()


if __name__ == "__main__":
    main(sys.argv[1:])
