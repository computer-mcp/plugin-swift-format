---
description: Keep the swift-format exporter separate from the vendor formatter and preserve its upstream notices.
---
# plugin-swift-format Agent Guide

## Plugin Boundaries

- Keep the exporter separate from the vendor formatter, preserve upstream
  notices, and do not change the global `PATH`.
- Before handoff, run `swift build`, `swift test` and swift-format lint.
