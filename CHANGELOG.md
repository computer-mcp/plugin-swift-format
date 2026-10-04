# Changelog

All notable user-visible changes to the Swift Format plugin are documented here.

## Unreleased

- Declare Computer MCP 1.1.0, the first host that reads plugin manifests, as the
  minimum host.

## 1.0.0 — 2026-09-13

- First release: exposes the user's existing `swift-format` through a verified
  command tree with deterministic argv mapping. The verified baseline is Swift
  Format 6.3.1; an incompatible version or interface is rejected.
- Installation starts disabled and grants no tool access. The archive contains
  the declaration and verified tree, not a formatter.
