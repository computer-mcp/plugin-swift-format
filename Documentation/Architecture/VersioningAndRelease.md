# Versioning and Release

The organization's [VERSIONING.md](https://github.com/computer-mcp/.github/blob/master/VERSIONING.md)
owns shared version rules, plugin API and host-version compatibility, dependency
requirements, tags, release contents and immutability. This document owns the
plugin-swift-format version sources, package boundaries and acceptance checks.
The [release guide](../Reference/Release.md) describes the operator procedure.

## Components and Version Authority

| Shipped component | Version meaning | Authoritative source | Derived fields | Update and read-only check |
| --- | --- | --- | --- | --- |
| `swift-format.zip` plugin package | Package version | `version` in `computer-mcp-plugin.toml` | builder and release receipts, tag `vX.Y.Z`, catalog entry | Edit the manifest; `release.yml` verifies agreement with the tag |

The `export-swift-format-tree` executable is a maintainer tool that regenerates
`cli-tree.json`. It is not shipped and has no version of its own.

The archive contains the manifest, `cli-tree.json`, the README, contribution
guide, license, notices, `ThirdPartyNotices/` and `Documentation/`. Changes to
these files change the archive. The exporter, tests, scripts and workflows are
not packaged.

## Dependencies and Verified Combinations

`cli-tree.json` pins the formatter through its `executable_checks`: the
`--version` output and the SHA-256 of the `--experimental-dump-help` output. The
host applies them before every call. A different formatter requires regenerating
the tree with the exporter and a reviewed package update.

`computer-mcp-plugin.toml` declares the plugin API and host-version constraints
under the organization's compatibility rules.

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

The candidate is `swift-format-plugin-<commit>` from a successful `ci.yml` push
run for a reviewed `master` commit. It contains `swift-format.zip` and the
builder's `package-receipt.json`.

`release.yml` calls the organization's pinned reusable release workflow with
`python3 Scripts/build_package.py` and that exact CI artifact name. The workflow
rebuilds and compares the archive bytes. Manual acceptance validates and
installs the verified archive with the selected Computer MCP host, binds the
supported formatter, and exercises format and lint calls. Record those results
and their limits in the draft Release notes before publication.

The release caller invokes `notify-catalog.yml` only when publication was
requested and the reusable workflow reports `published`. Only that notification
job receives the catalog App private key.

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
| Release verification and publication | `release.yml`; dry run and acceptance steps in [Release](../Reference/Release.md) | Repository Actions; signing key for the version tag |
| Status and interrupted-run recovery | Rerun failed jobs; shared recovery rules in [VERSIONING.md](https://github.com/computer-mcp/.github/blob/master/VERSIONING.md#plugin-release-contents) | Repository Actions |
| Cleanup | Delete local output directories and `.build/` | Local checkout |

CI keeps candidate artifacts for 14 days. The builder refuses to overwrite a
different archive. Local package outputs belong in ignored `dist/`.
