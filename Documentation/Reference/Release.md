# Release

Release status: [CI](https://github.com/computer-mcp/plugin-swift-format/blob/master/.github/workflows/ci.yml)
builds candidate archives on pull requests, `master` pushes and manual runs.
[`release.yml`](https://github.com/computer-mcp/plugin-swift-format/blob/master/.github/workflows/release.yml)
implements dry runs and publication; native and host acceptance are manual.

The organization [VERSIONING](https://github.com/computer-mcp/.github/blob/master/VERSIONING.md)
owns version rules, including tags, version choice and the changelog. This
reference records this repository's version sources, compatibility, release
procedure and checks. The shared
[release workflow guide](https://github.com/computer-mcp/github-workflows/blob/master/docs/plugin-release.md)
describes workflow verification and recovery.

## Components and Version Sources

| Shipped component | Version meaning | Version source | Mirrors and derived fields | Update and read-only check |
| --- | --- | --- | --- | --- |
| `swift-format.zip` plugin package | Package version | `version` in [`computer-mcp-plugin.toml`](../../computer-mcp-plugin.toml) | builder and release receipts, release tag, catalog entry | Edit the manifest; `release.yml` checks agreement with the tag |

The `export-swift-format-tree` executable is a maintainer tool that regenerates
`cli-tree.json`. It is not shipped and has no version of its own.

The archive contains the manifest, `cli-tree.json`, the README, contribution
guide, license, notices, `ThirdPartyNotices/` and `Documentation/`.
The exporter, tests, build scripts and workflows are excluded from the archive.

## Compatibility Surface

The package contributes the CLI tree consumed by the host's generic CLI runtime.
[Interface](Interface.md) owns command coverage, argument and stdin mapping,
output behavior and executable checks. The manifest owns `plugin_api` and
host-version constraints.

For the maintainer exporter, [`Package.swift`](https://github.com/computer-mcp/plugin-swift-format/blob/master/Package.swift) declares
the Swift tools version and macOS deployment floor. Its command options,
generated tree and structured errors are exercised by the Swift tests.

## Dependencies and Verified Combinations

`cli-tree.json` pins the formatter through its `executable_checks`: the
`--version` output and the SHA-256 of the `--experimental-dump-help` output.
The host applies them before every authorized call. A different formatter
requires regenerating the tree with the exporter and a reviewed package update.

The exporter depends on swift-argument-parser. `Package.swift` declares its
lower bound and next-major compatibility range;
[`Package.resolved`](https://github.com/computer-mcp/plugin-swift-format/blob/master/Package.resolved) records the selected version and
revision. CI resolves packages and fails if the lockfile changes. The formatter
baseline is independent of the exporter's SwiftPM dependency version.

The package builder needs only the Python 3.11 standard library; CI runs its
tests and build on Python 3.11 and 3.13. Swift tests use recorded native help;
host installation and real format/lint calls are separate manual acceptance.

## Derived Metadata and Drift Checks

`Scripts/build_package.py` verifies the plugin ID, parses the CLI tree, skips
hidden files and Python caches, rejects links and special files, and produces
the same archive bytes from the same source. The builder receipt prints the ID,
version and SHA-256.

The exporter regenerates `cli-tree.json` from verified native input; the
generation command is in [the manual](../../README.md#regenerate-and-test).
Its Swift tests cover generation from recorded help. CI checks the SwiftPM
lockfile, strict Swift formatting, Swift tests and a release exporter build
before running the Python package checks; [CONTRIBUTING](../../CONTRIBUTING.md#validation)
lists those commands.

## Candidate, Acceptance and Publication

Publication depends on the repository's GitHub release immutability setting.
The shared workflow checks that setting before writing a Release.

### Publish

1. Confirm that `version` in `computer-mcp-plugin.toml` has not been released
   and that the reviewed `master` commit has a successful `ci.yml` push run.
2. Dispatch `release.yml` from `master` with `ref` set to that full commit SHA
   and `publish` set to `false` (the default). The pinned reusable workflow runs
   `python3 Scripts/build_package.py` with an output directory and requires its
   `swift-format.zip` to match the archive in the exact
   `swift-format-plugin-<commit>` CI artifact byte for byte. Inspect the
   `plugin-release-<run-id>-<attempt>` workflow artifact: `assets/` contains the
   verified archive, `release-receipt.json` and `SHA256SUMS`. An untagged dry run
   omits tag and signature checks and reports the signed tag still required.
3. Validate and install that exact archive with the selected Computer MCP host,
   bind the supported `swift-format`, and run a format and a lint call. The
   tree's executable checks reject any other formatter version or interface.
4. Create the version tag that [VERSIONING](https://github.com/computer-mcp/.github/blob/master/VERSIONING.md) requires on the accepted commit and push it.
   Create a draft Release for that tag targeting the full commit SHA. Record
   the archive SHA-256, host and formatter versions, manual acceptance results
   and their limits in its release notes.
5. Dispatch `release.yml` from `master` with `ref` set to that version tag and
   `publish` set to `true`. The workflow verifies the tag, version, CI provenance
   and archive bytes, completes and verifies the draft's assets, then publishes
   it. The dependent notification job runs only when `publish` is true and the
   reusable workflow reports `published`.

The Release assets are `swift-format.zip`, `release-receipt.json` and
`SHA256SUMS`. `package-receipt.json` is the builder's metadata in the CI artifact,
not a Release asset. A dry run performs verification and assembly without
writing a Release or receiving catalog credentials.

### Catalog notification

`notify-catalog.yml` runs when a release is published, edited, released,
unpublished or deleted, and on manual dispatch. It asks the website to reconcile
the complete catalog. The website verifies the actual GitHub releases rather
than the event payload, keeps verified history, and applies its own withdrawal
policy; an event never withdraws a release by itself.

The workflow authenticates as the receiver-scoped catalog GitHub App through
the `CATALOG_APP_CLIENT_ID` variable and the `CATALOG_APP_PRIVATE_KEY` secret.
The App needs Actions write access to `computer-mcp/computer-mcp.github.io` only.
The job checks this repository's immutable ID, does not check out package code,
and grants its own token no repository permissions. Missing or rejected
authority fails the run visibly.

The shared notification action in `computer-mcp/github-workflows` is pinned to a
reviewed full commit. Update the pin here when adopting a reviewed change to the
notification contract.

A release published with a repository `GITHUB_TOKEN` does not trigger
release-event workflows. `release.yml` calls `notify-catalog.yml` as a dependent
job after confirmed publication. Only this notification job receives the catalog
secret; the reusable release workflow receives no secrets.

## Evidence Reuse and Invalidation

The CI artifact name identifies the source commit, and the builder receipt records
the archive SHA-256. The release workflow verifies CI provenance and artifact
digests; `release-receipt.json` records the commit, CI run and attempt, artifact
digest and archive SHA-256.

An archive with the accepted digest keeps its archive acceptance for the tested
combination. Reuse of manual results is reviewed against the native dependency,
selected host, check definitions and relevant environment recorded with them.
Changes to packaged files produce a new archive and require the affected checks
again. A check-only change can reuse unchanged archive bytes with fresh affected
checks. Source tests do not replace installation, native or authenticated
execution evidence. Keep failed-check output and result limits with the manual
acceptance record.

## Entry Points and Artifact Retention

| Operation | Existing command or explicit manual procedure | Required access |
| --- | --- | --- |
| Version update and check | Edit `computer-mcp-plugin.toml`; `python3 -m unittest discover -s Tests -p 'test_*.py'` | Local checkout |
| Candidate validation and build | `ci.yml`; locally the commands in [CONTRIBUTING](../../CONTRIBUTING.md#validation), then `python3 Scripts/build_package.py dist` | CI or local checkout with Swift toolchain and resolved dependencies |
| Native and host acceptance | Validate and install the exact archive with the selected host, bind the supported formatter and exercise format/lint calls | Selected host, formatter and authorized workspace |
| Acceptance and publication | Manual checks above; dispatch `release.yml`, dry run first | Repository Actions; publication also needs a signing key and release write access |
| Status and interrupted-run recovery | Inspect CI or `release.yml`; follow [Retry](#retry) | Repository Actions |
| Cleanup | Delete obsolete local output directories and reproducible `.build/` products | Local checkout |

CI keeps candidate artifacts for 14 days. The builder refuses to overwrite a
different archive. Local package output belongs in ignored `dist/`; remove
output and reproducible caches after use unless an acceptance record requires
retention.

### Retry

For a failed release run, use **Re-run failed jobs**. The shared workflow's
[recovery procedure](https://github.com/computer-mcp/github-workflows/blob/master/docs/plugin-release.md#run-and-recover)
owns draft recovery, frozen provenance and expired artifacts. A notification
failure needs only the notification job rerun or a manual notification dispatch.

For an operator-driven publication or a missed or failed notification, dispatch:

```sh
gh workflow run notify-catalog.yml --repo computer-mcp/plugin-swift-format --ref master
```

A successful dispatch only proves the request was accepted. Follow the run's
`run_url` output to the website run, confirm it succeeded, and confirm the public
index lists the expected release. Retrying never requires changing or
republishing the release: reconciliation is idempotent, and the website's
hourly schedule also repairs missed notifications.

The website's
[catalog publication and notification contract](https://github.com/computer-mcp/computer-mcp.github.io/blob/master/docs/plugin-catalog.md)
covers provenance, credentials, retry bounds and deployment.
