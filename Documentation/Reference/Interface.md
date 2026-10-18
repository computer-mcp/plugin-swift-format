# Interface Contract

The formatter is executed directly by Computer MCP's generic CLI runtime. This
package contributes a file-backed tree; no proxy process or extra RPC is involved.
The Swift package builds a maintainer exporter and tests, not a copy of Swift Format.

## Sources and supplements

The pinned native `--experimental-dump-help` export uses ArgumentParser
`serializationVersion: 0`, contains five nodes and is identified by SHA-256
`afce7a2f8c5b0825b90ce7061c6508eb5545b07b1414ed853c23a0fb6ab8c14e`.
The exporter checks its exact bytes and the separately captured `--version` output
before decoding. The generated tree also declares two host-side executable checks:
`--version` must return exactly `6.3.1\n`, and `--experimental-dump-help` must match
the pinned stdout digest. The Gateway runs both before each authorized command;
neither generation nor runtime checks are signatures or grants.

The checks share a maximum five-second execution budget, capped by the registered
timeout; the target command then receives its own registered timeout. Both checks
use the same resolved executable, cwd and environment, with closed stdin and a
4 MiB capture bound. Failure or cancellation prevents the target invocation.
Observed executable/interpreter file changes also stop it. This is not atomic
kernel pinning or a sandbox, and does not verify dynamically loaded dependencies.
File-backed discovery, package installation and static diagnostics do not run
these checks. A tool listing reports that checks are required, not already passed.

Matching upstream `swift-6.3.1-RELEASE` sources establish:

- [SwiftFormatCommand](https://github.com/swiftlang/swift-format/blob/swift-6.3.1-RELEASE/Sources/swift-format/SwiftFormatCommand.swift): the root defaults to `format`.
- [LintFormatOptions](https://github.com/swiftlang/swift-format/blob/swift-6.3.1-RELEASE/Sources/swift-format/Subcommands/LintFormatOptions.swift): optional color Boolean with `prefixedNo`, repeated offsets/features, paths and validation.
- [Format](https://github.com/swiftlang/swift-format/blob/swift-6.3.1-RELEASE/Sources/swift-format/Subcommands/Format.swift): stdin when paths are absent, explicit in-place mutation.
- [DumpConfiguration](https://github.com/swiftlang/swift-format/blob/swift-6.3.1-RELEASE/Sources/swift-format/Subcommands/DumpConfiguration.swift): configuration requires effective mode.
- [ConfigurationOptions](https://github.com/swiftlang/swift-format/blob/swift-6.3.1-RELEASE/Sources/swift-format/Subcommands/ConfigurationOptions.swift): configuration is a string containing a path or JSON.

## Mapping

Paths, argument names, optionality, repetition, flags and descriptions come from
the native export. Hyphens in parameter names become underscores. Command words
precede options; options use `--name=value` (one per array element), followed by
`--` and positional values. This preserves empty strings, Unicode, whitespace,
quotes, leading hyphens, and shell metacharacters as literal argument bytes.

`source` is an optional UTF-8 stdin parameter for root/format/lint. Omission closes
stdin with no bytes; it does not start an interactive session. Use `paths: ["-"]`
for explicit stdin: omitted paths produce an upstream deprecation warning that
strict lint treats as an error. The Gateway preserves this diagnostic.
`color_diagnostics`
true/false emits the positive/negative flag; absence leaves terminal detection
to the formatter. Other flags are one-way: true or omitted. Array defaults are
metadata and are never inserted into argv. Hidden debug flags are included as
reported by the native interface and retain their upstream effects.

The root combines its own arguments with the default Format node, deduplicating
the inherited help flag. Configuration in `dump-configuration` requires the
one-way `effective` flag. Conditional constraints such as offsets applying to
one file, recursive paths, and assume-filename requiring stdin are validated by
the formatter; invalid calls return its real nonzero status and diagnostics.

All nodes preserve text output. In particular, `dump-configuration` can produce
JSON or help text depending on its help flag, so the tree does not claim an
unconditional JSON output schema. The Gateway's execution envelope remains
structured. No schema, risk hint, or package installation grants tool permission.

The capture includes every observed node/argument but is not a claim of every
ArgumentParser control entry point or every repeated-alias token sequence.
Unsupported formatter versions require a reviewed plugin update. File trees
are refreshed by the host; this package never installs or upgrades the formatter.
