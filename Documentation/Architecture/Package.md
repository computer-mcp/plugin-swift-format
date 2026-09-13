# Swift Format package

## Scope and structure

The plugin contributes a CLI Tree for an externally installed Swift Format.
ExportSwiftFormatTree is a maintainer executable: it decodes the pinned native
machine interface, validates its version and digest, supplements source-verified
stdin/default-command semantics, then atomically emits cli-tree.json.
The Gateway consumes that tree and encodes deterministic argv; the exporter
is not part of invocation-time formatting.

## Dependencies

swift-argument-parser 1.8.2 owns named-option parsing, validation and generated
help for the exporter. It removes fixed-position argument handling while the
export use case retains bounded stdin, atomic writes and JSON failures on stderr.
Foundation and CryptoKit supply data and digest operations. The vendor formatter
is a separately resolved host dependency, never bundled or installed here.

## Boundaries

The host owns workspace access, caller permissions, executable bindings and
runtime output limits. Version/interface checks distinguish the reviewed tree
from an incompatible external installation. Current mapping and intentional
coverage limits are described in [Interface](../Reference/Interface.md).

## Distribution

`Scripts/build_package.py` packages regular, bounded source files into a
deterministic ZIP. It includes the host-consumed declaration and CLI Tree,
manuals and notices, while build products and maintainer source stay in the
repository. The Python standard-library builder requires no vendor process.
The validation workflow tests the Swift exporter and archive boundaries before
retaining the archive and digest receipt as workflow artifacts. Publishing
requires a separately authorized release with reviewed provenance and licensing.
