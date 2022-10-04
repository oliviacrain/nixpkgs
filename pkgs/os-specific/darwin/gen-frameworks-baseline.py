#!/usr/bin/env nix-shell
#!nix-shell -i python -p python3 swiftPackages.swift-unwrapped

"""
Generate a baseline frameworks.nix for a macOS SDK.
"""

import json
import os
import subprocess
import sys

ALLOWED_LIBS = ["simd"]

HEADER = """\
{ libs, frameworks }: with libs; with frameworks;
{
"""

FOOTER = """\
}
"""


def eprint(*args):
    print(*args, file=sys.stderr)


def name_from_ident(ident):
    return ident.get("swift", ident.get("clang"))


def scan_sdk(sdk):
    # Find frameworks by scanning the SDK frameworks directory.
    frameworks = [
        framework.removesuffix(".framework")
        for framework in os.listdir(f"{sdk}/System/Library/Frameworks")
        if not framework.startswith("_")
    ]
    frameworks.sort()

    # Determine the longest name for padding output.
    width = len(max(frameworks, key=len))

    output = HEADER

    for framework in frameworks:
        deps = []

        # Use Swift to scan dependencies, because a module may have both Clang
        # and Swift parts. Using Clang only imports the Clang module, whereas
        # using Swift will usually import both Clang + Swift overlay.
        #
        # TODO: The above is an assumption. Not sure if it's possible a Swift
        # module completely shadows a Clang module. (Seems unlikely)
        #
        # TODO: Handle "module 'Foobar' is incompatible with feature 'swift'"
        #
        # If there were a similar Clang invocation for scanning, we could fix
        # the above todos, but that doesn't appear to exist.
        eprint(f"# scanning {framework}")
        result = subprocess.run(
            [
                "swiftc",
                "-scan-dependencies",
                # We provide a source snippet via stdin.
                "-",
                # Use the provided SDK.
                "-sdk",
                sdk,
                # This search path is normally added automatically by the
                # compiler based on the SDK, but we have a patch in place that
                # removes that for SDKs in /nix/store, because our xcbuild stub
                # SDK doesn't have the directory.
                # (swift-prevent-sdk-dirs-warning.patch)
                "-I",
                f"{sdk}/usr/lib/swift",
                # For some reason, 'lib/swift/shims' from both the SDK and
                # Swift compiler are picked up, causing redefinition errors.
                # This eliminates the latter.
                "-resource-dir",
                f"{sdk}/usr/lib/swift",
            ],
            input=f"import {framework}".encode(),
            stdout=subprocess.PIPE,
        )
        if result.returncode != 0:
            eprint(f"# Scanning {framework} failed (exit code {result.returncode})")
            result.stdout = b""

        # Parse JSON output.
        if len(result.stdout) != 0:
            data = json.loads(result.stdout)

            # Entries in the modules list come in pairs. The first is an
            # identifier (`{ swift: "foobar" }` or `{ clang: "foobar" }`), and
            # the second metadata for that module. Here we look for the pair
            # that matches the framework we're scanning (and ignore the rest).
            modules = data["modules"]
            for i in range(0, len(modules), 2):
                ident, meta = modules[i : i + 2]

                # NOTE: We may match twice, for a Swift module _and_ for a
                # Clang module. So matching here doesn't break from the loop,
                # and deps is appended to.
                if name_from_ident(ident) == framework:
                    dep_idents = meta["directDependencies"]
                    deps += [name_from_ident(ident) for ident in dep_idents]
                    # List unfiltered deps in progress output.
                    eprint(ident, "->", dep_idents)

        # Filter out modules that are not separate derivations.
        # Also filter out duplicates (when a Swift overlay imports the Clang module)
        allowed = frameworks + ALLOWED_LIBS
        deps = set([dep for dep in deps if dep in allowed])

        # Filter out self-references. (Swift overlay importing Clang module.)
        if framework in deps:
            deps.remove(framework)

        # Generate a Nix attribute line.
        if len(deps) != 0:
            deps = list(deps)
            deps.sort()
            deps = " ".join(deps)
            output += f"  {framework.ljust(width)} = {{ inherit {deps}; }};\n"
        else:
            output += f"  {framework.ljust(width)} = {{}};\n"

    output += FOOTER
    sys.stdout.write(output)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        eprint(f"Usage: {sys.argv[0]} <path to MacOSX.sdk>")
        sys.exit(64)

    scan_sdk(sys.argv[1])
