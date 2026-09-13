# Swift Format Plugin

A Computer MCP plugin for the Swift Format supplied with Swift 6.3.1. It exposes
formatting, linting, configuration output, and help through the Gateway's typed
CLI tools. The installed formatter remains user-owned.

## Setup

Add this checkout with Computer MCP's local plugin entry. In its settings, bind
the `formatter` dependency to the actual `swift-format` executable supplied with
Swift 6.3.1, verify its `--version`, then enable the `format` CLI contribution.
The Gateway requires a workspace and Full Shell permission for these tools.
Before every authorized invocation, the Gateway checks the executable's version
and native interface digest against this plugin's baseline. A mismatch stops the
invocation; select a compatible dependency binding or a reviewed plugin update.
These checks run vendor code with closed stdin in the registered cwd/environment,
share a bounded check budget, and do not run during installation or static doctor.
This package installs neither Swift nor vendor binaries and does not alter PATH.

Use `tools/list` to obtain generated tool names; titles contain the registration
and command path. For the `format` command, pass:

```json
{"paths":["-"],"source":"let value=1\n","color_diagnostics":false,"workspace_id":"YOUR_WORKSPACE"}
```

The result contains real stdout/stderr, exit status, and timeout information.
Use `paths` for files; `in_place: true` explicitly overwrites those files. Omitted
paths still select stdin but emit an upstream deprecation warning; `["-"]` is
the supported explicit stdin form. `lint` checks source and `strict: true` makes
findings fail the command. No artificial dry-run is supplied.

## Interface coverage

`cli-tree.json` is generated from the native machine export, not parsed help text
or a handwritten command list. Every argument of the five observed nodes is
accounted for, including hidden debug arguments. Preferred spellings represent
equivalent aliases; one Boolean represents the verified color/inverse pair.
The native export's missing default-subcommand and stdin semantics are supplemented
from the matching upstream source. See [Interface](Documentation/Reference/Interface.md).

Coverage is explicitly partial: experimental parser-control entry points are
not formatting tools, and value-dependent upstream validation remains in the
formatter. Unknown versions or a changed native export stop generation. Updating
this plugin's verified interface does not require vendor-specific Gateway code.

## Package archive

With Python 3.11 or newer, run `python3 Scripts/build_package.py OUTPUT_DIRECTORY`
to produce `swift-format.zip` and print its ID, version and SHA-256. The archive
contains the declaration, generated tree, manuals, license and upstream notices; it
contains neither the maintainer exporter nor the vendor formatter. Identical
inputs produce identical bytes. An existing different artifact is preserved
and causes an error. Install the ZIP through the host's plugin management UI or
CLI, reviewing the dependency binding and grants independently.

`.github/workflows/validate.yml` validates the exporter and package on pull
requests, pushes and manual runs. Its downloadable workflow artifacts are
validation outputs, not a public plugin release or publisher verification.

## Regenerate and test

Requires Swift 6.2 or newer to build the exporter. It uses swift-argument-parser
for named options, validation and generated help.
The exporter is a maintainer tool, not a replacement formatter or runtime service.

```sh
swift build
swift test
SWIFT_FORMAT=/absolute/path/to/swift-format
"$SWIFT_FORMAT" --experimental-dump-help | .build/debug/export-swift-format-tree \
  --executable-version "$("$SWIFT_FORMAT" --version)" --output cli-tree.json
```

Use a shell with pipeline failure propagation (`set -o pipefail`). The native
export must match the pinned baseline. Review upstream source and tests before
supporting another version; do not bypass the drift check. The exporter writes
atomically after complete validation, and reports structured errors on stderr.
No global installation is needed; it runs by explicit path from any directory.

Disabling or removing the plugin revokes its contribution, not the external
formatter. Host overrides and the dependency binding belong to Computer MCP.

See the [documentation index](Documentation/README.md) and
[contributor guide](CONTRIBUTING.md) for architecture and validation guidance.

## License

Computer MCP-owned code and resources use the
[Computer MCP Source-Visible License 1.0](LICENSE). Source visibility is not an
open-source license. [Third-party notices](THIRD_PARTY_NOTICES.md) identify the
separate rights covering upstream descriptions and dependencies.
