<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset=".github/assets/logo/logo-dark.png">
    <img src=".github/assets/logo/logo-light.png" width="128" height="128" alt="">
  </picture>
</p>

<h1 align="center">Swift Format</h1>

<p align="center">Computer MCP family plugin for verified Swift formatting and linting.</p>

<p align="center">
  <a href="https://github.com/computer-mcp/plugin-swift-format/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/computer-mcp/plugin-swift-format/ci.yml?branch=master&label=CI&style=flat"></a>
  <img alt="swift-format from Swift 6.3.1" src="https://img.shields.io/badge/swift--format-Swift%206.3.1-orange?style=flat">
  <img alt="Platform: macOS" src="https://img.shields.io/badge/platform-macOS-lightgrey?style=flat">
  <a href="LICENSE"><img alt="License: FSL-1.1-ALv2" src="https://img.shields.io/badge/license-FSL--1.1--ALv2-blue?style=flat"></a>
</p>

<p align="center">
  <a href="#install">Install</a> ·
  <a href="#usage">Usage</a> ·
  <a href="Documentation/Reference/Interface.md">Interface</a> ·
  <a href="Documentation/README.md">Documentation</a> ·
  <a href="CONTRIBUTING.md">Contributing</a>
</p>

## Overview

This plugin gives [Computer MCP](https://computer-mcp.github.io/) typed tools for the
`swift-format` supplied with Swift 6.3.1: formatting, linting, configuration output and help.
The formatter stays yours. The plugin ships no Swift or vendor binaries and does not change
`PATH`; you bind the executable you already have.

Before every authorized call, the Gateway checks the bound executable's version and native
interface digest against this plugin's verified baseline. A mismatch stops the call until you
select a compatible binding or install a reviewed plugin update. These checks run the vendor
executable with closed stdin in the registered working directory and environment, share a
bounded time budget, and never run during installation or a static doctor check.

## Quick look

The plugin adds one CLI contribution, `format`. Its root command formats, like the upstream
default, and it has these subcommands:

| Command | Result |
| --- | --- |
| `format` | Formats files or stdin; `in_place: true` overwrites the listed files |
| `lint` | Reports style findings; `strict: true` makes findings fail the command |
| `dump-configuration` | Prints the effective or default configuration as JSON |
| `help` | Prints upstream help |

Install it in the host, bind the `formatter` dependency, then call the generated tool. For
`format`, pass:

```json
{"paths":["-"],"source":"let value=1\n","color_diagnostics":false,"project_id":"YOUR_PROJECT"}
```

The result carries the real stdout, stderr, exit status and timeout information.

## Install

1. Build the package archive (see [Package archive](#package-archive)), or add this checkout with
   Computer MCP's local plugin entry.
2. Install the archive through the host's plugin management UI or CLI.
3. In the plugin's settings, bind the `formatter` dependency to the actual `swift-format` from
   Swift 6.3.1 and verify its `--version`.
4. Enable the `format` CLI contribution. The tools run inside a project and need Full Shell
   permission.

Disabling or removing the plugin revokes its contribution, not the external formatter. Host
overrides and the dependency binding belong to Computer MCP.

## Usage

Use `tools/list` to obtain the generated tool names; titles contain the registration and command
path. Pass files in `paths`; `["-"]` selects stdin explicitly. Omitting `paths` still reads stdin
but emits an upstream deprecation warning. No artificial dry run is supplied.

`cli-tree.json` is generated from the formatter's native machine export, not parsed help text or
a handwritten list. Every argument of the five observed commands is accounted for, including
hidden debug arguments; preferred spellings stand for equivalent aliases, and one Boolean covers
the verified color/inverse pair. The export's missing default-subcommand and stdin semantics are
supplemented from the matching upstream source. Coverage is explicitly partial: experimental
parser-control entry points are not formatting tools, and value-dependent validation stays in the
formatter. See [Interface](Documentation/Reference/Interface.md).

### Package archive

With Python 3.11 or newer:

```sh
python3 scripts/build_package.py OUTPUT_DIRECTORY
```

This writes `swift-format.zip` and prints its ID, version and SHA-256. The archive contains the
declaration, generated tree, manuals, license and upstream notices; it contains neither the
maintainer exporter nor the vendor formatter. Identical inputs produce identical bytes, and an
existing different archive is preserved and reported as an error. Review the dependency binding
and grants when you install it.

### Regenerate the interface

The exporter is a maintainer tool, not a replacement formatter or runtime service. Build it with
Swift 6.2 or newer; it uses swift-argument-parser for options, validation and help. In a shell
with `set -o pipefail`:

```sh
swift build
swift test
SWIFT_FORMAT=/absolute/path/to/swift-format
"$SWIFT_FORMAT" --experimental-dump-help | .build/debug/export-swift-format-tree \
  --executable-version "$("$SWIFT_FORMAT" --version)" --output cli-tree.json
```

The native export must match the pinned baseline: an unknown version or a changed export stops
generation. Review upstream source and tests before supporting another version, and do not bypass
the drift check. The exporter writes atomically after complete validation, reports structured
errors on stderr, and runs by explicit path from any directory. Updating the verified interface
needs no vendor-specific Gateway code.

## Requirements

- Computer MCP on macOS.
- `swift-format` from Swift 6.3.1, bound in the plugin's settings.
- Python 3.11 or newer to build the package archive.
- Swift 6.2 or newer to build and test the exporter.

## Documentation

The [documentation index](Documentation/README.md) covers the architecture, the
[interface](Documentation/Reference/Interface.md) and the
[release process](Documentation/Reference/Release.md). CI validates the exporter and the package
on pull requests, `master` pushes and manual runs, and repeats the package tests and build on
Python 3.11. Its downloadable workflow artifacts are validation outputs, not a public plugin
release.

## Contributing

See the [contributor guide](CONTRIBUTING.md).

## License

Computer MCP-owned code and resources use the
[Functional Source License 1.1, Apache 2.0 Future License](LICENSE) (FSL-1.1-ALv2).
[Third-party notices](THIRD_PARTY_NOTICES.md) identify the separate rights covering upstream
descriptions and dependencies.
