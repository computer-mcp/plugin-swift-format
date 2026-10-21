# Release

This guide covers releasing through `.github/workflows/release.yml` and
notifying the official plugin catalog.
[Versioning and Release](../Architecture/VersioningAndRelease.md) owns this
repository's version sources and acceptance checks. The organization's
[VERSIONING.md](https://github.com/computer-mcp/.github/blob/master/VERSIONING.md)
owns shared version, release-content and immutability rules; its
[release workflow guide](https://github.com/computer-mcp/.github/blob/master/Documentation/Reference/PluginRelease.md)
describes verification, receipts and recovery.

Before the first release, the repository owner must enable GitHub release
immutability in the repository settings. The release workflow refuses
publication if that prerequisite is disabled or cannot be verified.

## Publish

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
4. Create a signed annotated tag `vX.Y.Z` on the accepted commit and push it.
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

## Catalog notification

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

The website's notification action is pinned to a reviewed full commit. Publish
that website commit first, then update the pin here when adopting a change to
the notification contract.

A release published with a repository `GITHUB_TOKEN` does not trigger
release-event workflows. `release.yml` calls `notify-catalog.yml` as a dependent
job after confirmed publication. Only this notification job receives the catalog
secret; the reusable release workflow receives no secrets.

## Retry

For a failed release run, use **Re-run failed jobs**. The shared workflow's
[recovery procedure](https://github.com/computer-mcp/.github/blob/master/Documentation/Reference/PluginRelease.md#run-and-recover)
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
