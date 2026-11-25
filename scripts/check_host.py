"""Run the Swift Format consumer contract in an explicit, isolated host checkout."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys

FIXTURE = "SwiftFormatHostIntegrationTests.swift"
CASES = {
    "deterministic": {"admission", "binding", "boundaries", "revocation", "cleanup"},
    "native": {"format", "lint", "help", "configuration", "outside", "cleanup"},
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def absolute(value):
    path = Path(value)
    if not path.is_absolute():
        raise argparse.ArgumentTypeError("Use an absolute path")
    try:
        return path.resolve(strict=True)
    except OSError as error:
        raise argparse.ArgumentTypeError("Input path must exist") from error


def revision(value):
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise argparse.ArgumentTypeError("Use a full lowercase 40-character commit SHA")
    return value


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True,
                                   stderr=subprocess.PIPE, timeout=15).strip()


def verify_source(root, sha):
    if git(root, "rev-parse", "--show-toplevel") != str(root):
        raise ValueError("Source must be the repository root")
    if git(root, "rev-parse", "HEAD") != sha:
        raise ValueError("Source HEAD differs from the supplied commit")
    if git(root, "status", "--porcelain", "--untracked-files=all"):
        raise ValueError("Source checkout must be clean")


def run_process(command, cwd, environment, log, timeout):
    """Own the complete child process group, including timeout and failure paths."""
    with log.open("wb") as output:
        child = subprocess.Popen(command, cwd=cwd, env=environment, stdout=output,
                                 stderr=subprocess.STDOUT, start_new_session=True)
        try:
            result = child.wait(timeout=timeout)
        except BaseException:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            child.wait()
            raise
        finally:
            # A command that returns while leaving descendants is not a completed run.
            try:
                os.killpg(child.pid, 0)
            except ProcessLookupError:
                pass
            else:
                os.killpg(child.pid, signal.SIGKILL)
                raise RuntimeError("Test command left a live process group; cleanup was forced")
    if result:
        raise RuntimeError(f"Swift consumer test failed with exit status {result}; inspect {log}")


def run(args):
    verify_source(args.host_source, args.host_sha)
    verify_source(args.plugin_source, args.plugin_sha)
    if args.host_source == args.plugin_source:
        raise ValueError("Host and plugin sources must be separate checkouts")
    source = args.plugin_source / "Tests/Fixtures" / (FIXTURE + ".txt")
    target = args.host_source / "Tests/ComputerMCPMacOSTests" / FIXTURE
    if not target.parent.is_dir() or target.exists() or target.is_symlink():
        raise ValueError("Host test directory is missing or the consumer fixture already exists")
    if args.mode == "native" and (args.formatter is None or not args.formatter.is_file()
                                      or not os.access(args.formatter, os.X_OK)):
        raise ValueError("Native verification requires an executable --formatter input")
    inputs = [source, args.plugin_source / "computer-mcp-plugin.toml",
              args.plugin_source / "cli-tree.json"]
    if args.formatter:
        inputs.append(args.formatter)
    before = {str(path): digest(path) for path in inputs}
    output = args.plugin_source / ".agent/host-check" / args.mode
    if not git(args.plugin_source, "check-ignore", str(output / "receipt.json")):
        raise ValueError("Host-check output must be ignored by the plugin repository")
    output.mkdir(parents=True, exist_ok=True)
    evidence = output / "cases.json"
    receipt = output / "receipt.json"
    evidence.unlink(missing_ok=True)
    receipt.unlink(missing_ok=True)
    environment = dict(os.environ)
    environment.update({
        "COMPUTER_MCP_FORMATTER_PLUGIN": str(args.plugin_source),
        "COMPUTER_MCP_FORMATTER_MODE": args.mode,
        "COMPUTER_MCP_FORMATTER_EVIDENCE": str(evidence),
    })
    environment.pop("COMPUTER_MCP_FORMATTER_EXECUTABLE", None)
    if args.formatter:
        environment["COMPUTER_MCP_FORMATTER_EXECUTABLE"] = str(args.formatter)
    created = False
    try:
        with target.open("xb") as destination:
            created = True
            destination.write(source.read_bytes())
        run_process(["/usr/bin/swift", "test", "--build-system", "native", "--no-parallel",
                     "--filter", "SwiftFormatHostIntegrationTests"], args.host_source,
                    environment, output / "swift-test.log", args.timeout)
        observed = json.loads(evidence.read_text())
        if observed.get("mode") != args.mode or set(observed.get("cases", [])) != CASES[args.mode]:
            raise ValueError("Consumer case evidence is incomplete or belongs to another mode")
        if {str(path): digest(path) for path in inputs} != before:
            raise ValueError("Consumer verification changed a source or executable input")
    finally:
        if created:
            if target.is_symlink() or digest(target) != before[str(source)]:
                raise RuntimeError("Copied fixture changed; preserve it for investigation")
            target.unlink()
    verify_source(args.host_source, args.host_sha)
    verify_source(args.plugin_source, args.plugin_sha)
    result = {"host_sha": args.host_sha, "plugin_sha": args.plugin_sha,
              "inputs_sha256": before, "mode": args.mode,
              "cases": sorted(observed["cases"]), "cleanup": "confirmed"}
    receipt.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"receipt": str(receipt), "mode": args.mode, "status": "passed"}))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host-source", type=absolute, required=True)
    parser.add_argument("--host-sha", type=revision, required=True)
    parser.add_argument("--plugin-source", type=absolute, required=True)
    parser.add_argument("--plugin-sha", type=revision, required=True)
    parser.add_argument("--formatter", type=absolute)
    parser.add_argument("--mode", choices=CASES, required=True)
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args(argv)
    if not 1 <= args.timeout <= 1800:
        parser.error("--timeout must be between 1 and 1800 seconds")
    try:
        run(args)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        parser.exit(1, f"Host verification failed: {error}\n")


if __name__ == "__main__":
    main()
