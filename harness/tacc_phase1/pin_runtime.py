#!/usr/bin/env python3
"""Derive framework-dependent manifests without modifying release binaries."""
import argparse
import json
from pathlib import Path

RUNTIME_PACK = "runtimepack.Microsoft.NETCore.App.Runtime.linux-x64/8.0.12"


def derive(config, deps):
    config = json.loads(json.dumps(config))
    deps = json.loads(json.dumps(deps))
    options = config["runtimeOptions"]
    assert options.pop("includedFrameworks") == [
        {"name": "Microsoft.NETCore.App", "version": "8.0.12"}]
    options["framework"] = {"name": "Microsoft.NETCore.App", "version": "8.0.21"}
    options["rollForward"] = "Disable"
    assert deps["libraries"].pop(RUNTIME_PACK)["type"] == "runtimepack"
    removed = sum(target.pop(RUNTIME_PACK, None) is not None
                  for target in deps["targets"].values())
    assert removed == 1
    return config, deps


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    root = args.root
    config, deps = derive(json.loads((root / "Renode.runtimeconfig.json").read_text()),
                          json.loads((root / "Renode.deps.json").read_text()))
    for name, value in (("Renode.pinned.runtimeconfig.json", config),
                        ("Renode.pinned.deps.json", deps)):
        (root / name).write_text(json.dumps(value, indent=2) + "\n")


if __name__ == "__main__":
    main()
