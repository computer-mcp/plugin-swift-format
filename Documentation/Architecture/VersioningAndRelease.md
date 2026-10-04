# Versioning and Release

Release status: partly manual. CI builds and checks candidate archives on every
pull request and `master` push; tagging, acceptance and publication are manual
steps described in [Release](../Reference/Release.md).

This document owns the current version and release rules for
plugin-swift-format.

## Components and Version Authority

| Shipped component | Version meaning | Authoritative source | Derived fields | Update and read-only check |
| --- | --- | --- | --- | --- |
| `swift-format.zip` plugin package | SemVer 2.0.0 package version | `version` in `computer-mcp-plugin.toml` | builder receipt, tag `vX.Y.Z`, catalog entry | Edit the manifest; agreement with the tag is checked manually |

The `export-swift-format-tree` executable is a maintainer tool that regenerates
`cli-tree.json`. It is not shipped and has no version of its own.

Compatible fixes advance the patch number, compatible features the minor number,
and incompatible changes the major number. Compatibility is established by
review and tests, not by comparing version numbers.

The archive contains the manifest, `cli-tree.json`, the README, contribution
guide, license, notices, `ThirdPartyNotices/` and `Documentation/`. Any change to
those files ships only under a new version; a published version is never rebuilt
from different bytes. Changes to the exporter, tests, scripts or workflows alone
do not change the archive and do not require a release.

## Dependencies and Verified Combinations

`cli-tree.json` pins the formatter through its `executable_checks`: the
`--version` output and the SHA-256 of the `--experimental-dump-help` output. The
host applies them before every call. A different formatter requires regenerating
the tree with the exporter and a reviewed package update.

`minimum_host` in `[compatibility]` declares the oldest Computer MCP host that
reads every manifest field this package uses. Raise it only when the package
needs a newer host contract, after validating against that host.

The exporter depends on swift-argument-parser, locked in `Package.resolved`. CI
resolves packages and fails if the lockfile changes. The package builder needs
only the Python 3.11 standard library; CI runs its tests and build on Python
3.11 and 3.13.

## Derived Metadata and Drift Checks

`Scripts/build_package.py` verifies the plugin ID, parses the CLI tree, skips
hidden files and Python caches, rejects links and special files, and produces
the same archive bytes from the same source. The exporter's Swift tests cover
tree generation from recorded native help. The builder receipt prints the ID,
version and SHA-256.

## Candidate, Acceptance and Publication

The candidate is the CI artifact for a reviewed `master` commit. Acceptance
requires a byte-identical local rebuild, and host validation and installation of
that exact archive with format and lint calls against the supported formatter.

A signed annotated `vX.Y.Z` tag binds the accepted commit, and the GitHub
Release publishes that exact archive with its builder receipt. The published
`v1.0.0` tag is lightweight and stays as published. Published tags and archives
are immutable; a defect is fixed in a new version. Publishing triggers the
catalog notification.

## Evidence Reuse and Invalidation

The CI artifact name binds the source commit, and the builder receipt binds the
archive SHA-256. An archive whose digest matches the accepted one keeps its
acceptance. Any change to a packaged file produces a new archive that needs the
affected checks again.

## Entry Points and Artifact Retention

| Operation | Existing command or explicit manual procedure | Required access |
| --- | --- | --- |
| Version update and check | Edit `computer-mcp-plugin.toml`; `python3 -m unittest discover -s Tests -p 'test_*.py'` | Local checkout |
| Candidate validation and build | `ci.yml`; locally the commands in [CONTRIBUTING](../../CONTRIBUTING.md) | CI or local checkout |
| Status and interrupted-run recovery | Rerun the failed CI job or check; outputs go to new directories | Repository Actions |
| Acceptance and publication | Manual steps in [Release](../Reference/Release.md) | Signing key and release write access |
| Cleanup | Delete local output directories and `.build/` | Local checkout |

CI keeps candidate artifacts for 14 days. The builder refuses to overwrite a
different archive. Keep local evidence outside the repository.
