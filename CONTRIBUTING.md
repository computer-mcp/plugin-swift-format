# Contributing

Changes belong to the artifact that owns their behavior. Describe the observable
change and include focused regression evidence. Preserve user configuration,
external dependencies and credentials.

## Validation

CI runs these checks; run them before opening a pull request:

```sh
swift package resolve && git diff --exit-code -- Package.resolved
swift format lint --strict --recursive --configuration .swift-format Package.swift Sources Tests
swift test --disable-automatic-resolution
swift build -c release --disable-automatic-resolution
python3 -m unittest discover -s Tests -p 'test_*.py'
python3 scripts/build_package.py OUTPUT_DIRECTORY
```

CI also repeats the Python tests and package build on Python 3.11. Exercise help, valid input and invalid input from outside the checkout. Keep command output contracts and generated resources covered by tests.

## Host consumer verification

Use an isolated, clean host checkout at the reviewed full 40-character commit.
The plugin checkout must also be clean at its supplied commit. The driver adds
one consumer-owned Swift fixture to the host test target for the run and removes
it afterward; it refuses an existing fixture. It never fetches, installs a
formatter or uses the installed App. Supply the actual existing Swift 6.3.1
formatter path explicitly for native cases.

```sh
python3 -B scripts/check_host.py \
  --host-source "$HOST_TEST_SOURCE" --host-sha "$REVIEWED_HOST_SHA" \
  --plugin-source "$FORMAT_PLUGIN_SOURCE" --plugin-sha "$FORMAT_PLUGIN_SHA" \
  --mode deterministic
python3 -B scripts/check_host.py \
  --host-source "$HOST_TEST_SOURCE" --host-sha "$REVIEWED_HOST_SHA" \
  --plugin-source "$FORMAT_PLUGIN_SOURCE" --plugin-sha "$FORMAT_PLUGIN_SHA" \
  --formatter "$FORMATTER_EXECUTABLE" --mode native
```

The driver invokes SwiftPM’s native build system from the host root. Its bounded
run writes the test log, case evidence and success receipt under the plugin
checkout’s ignored `.build/host-check/<mode>/` directory. Nonzero exits, missing
case evidence, changed inputs, timeouts and unconfirmed process cleanup fail
verification. Native cases must execute for verification to pass. Retain receipts
with the owning task’s evidence, then remove the ignored output directory when no
longer required. If a timeout interrupts host cleanup, retain the fixture root
named in the log for host execution recovery.
A failed or interrupted run has no success receipt and does not confirm that
isolated host executions have exited.

Deterministic cases exercise CLI admission, compatibility rejection before target
dispatch, container placement, outside-write/symlink/network denial and revocation.
Native cases format files in a host-created worktree, lint, print help and
configuration, and attempt writes outside that worktree with network none.
The test removes its own disposable worktrees through the host and joins process
cleanup before removing temporary state. The macOS CI job runs the deterministic
mode against the public Host source commit in
[.github/computer-mcp-host.sha](.github/computer-mcp-host.sha) and the plugin
commit actually checked out by CI. For the same check locally, set
`REVIEWED_HOST_SHA` from that pin and `FORMAT_PLUGIN_SHA` from the clean plugin
checkout's `git rev-parse HEAD`. Native mode is run separately with the explicit
formatter binding.

## Documentation

The [documentation index](Documentation/README.md) links current architecture
and reference material. Agent work routes live in AGENTS.md; public usage lives
in the root README. GitHub collaboration files belong in .github/ and contributor
policy belongs in root governance files.

Contributions are licensed under this repository's [LICENSE](LICENSE),
FSL-1.1-ALv2.
