# Changelog

All notable user-visible changes to the Swift Format plugin are documented here.

## Unreleased

- Licensed under FSL-1.1-ALv2 (Functional Source License 1.1, Apache 2.0
  future license): any use other than a competing product or service is
  permitted, and each release becomes available under Apache-2.0 two years
  after publication. Published releases keep their original license.
- Declare Computer MCP 1.1.0, the first host that reads plugin manifests, as the
  minimum host.

## 1.0.0 — 2026-09-13

- First release: exposes the user's existing `swift-format` through a verified
  command tree with deterministic argv mapping. The verified baseline is Swift
  Format 6.3.1; an incompatible version or interface is rejected.
- Installation starts disabled and grants no tool access. The archive contains
  the declaration and verified tree, not a formatter.
