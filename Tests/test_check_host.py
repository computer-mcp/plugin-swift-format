import argparse
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("check_host", ROOT / "scripts/check_host.py")
DRIVER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DRIVER)


class DriverTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.host = self.root / "host"
        self.plugin = self.root / "plugin"
        self.output = self.plugin / ".build/host-check/deterministic"
        (self.host / "Tests/ComputerMCPMacOSTests").mkdir(parents=True)
        (self.plugin / "Tests/Fixtures").mkdir(parents=True)
        self.source = self.plugin / "Tests/Fixtures" / (DRIVER.FIXTURE + ".txt")
        self.source.write_text("consumer fixture\n")
        self.target = self.host / "Tests/ComputerMCPMacOSTests" / DRIVER.FIXTURE
        for name in ("computer-mcp-plugin.toml", "cli-tree.json"):
            (self.plugin / name).write_text("unchanged input")
        self.args = argparse.Namespace(host_source=self.host, host_sha="a" * 40,
                                       plugin_source=self.plugin, plugin_sha="b" * 40,
                                       formatter=None, mode="deterministic", timeout=2)

    def execute(self, runner):
        with patch.object(DRIVER, "verify_source"), patch.object(DRIVER, "git", return_value="ignored"), \
                patch.object(DRIVER, "run_process", side_effect=runner), \
                contextlib.redirect_stdout(io.StringIO()):
            DRIVER.run(self.args)

    def evidence(self, environment, cases=None):
        Path(environment["COMPUTER_MCP_FORMATTER_EVIDENCE"]).write_text(json.dumps({
            "mode": self.args.mode, "cases": list(cases or DRIVER.CASES[self.args.mode])}))

    def test_success_runs_explicit_host_and_removes_fixture(self):
        def runner(command, cwd, environment, log, timeout):
            self.assertEqual(cwd, self.host)
            self.assertEqual(command, ["/usr/bin/swift", "test", "--build-system", "native",
                                      "--no-parallel", "--filter", "SwiftFormatHostIntegrationTests"])
            self.assertEqual(self.target.read_bytes(), self.source.read_bytes())
            self.assertEqual(environment["COMPUTER_MCP_FORMATTER_PLUGIN"], str(self.plugin))
            self.assertNotIn("COMPUTER_MCP_FORMATTER_EXECUTABLE", environment)
            self.assertEqual(log, self.output / "swift-test.log")
            self.assertEqual(Path(environment["COMPUTER_MCP_FORMATTER_EVIDENCE"]),
                             self.output / "cases.json")
            self.evidence(environment)
        with patch.dict(os.environ, {"COMPUTER_MCP_FORMATTER_EXECUTABLE": "/ambient/tool"}):
            self.execute(runner)
        self.assertFalse(self.target.exists())
        receipt = json.loads((self.output / "receipt.json").read_text())
        self.assertEqual(receipt["host_sha"], "a" * 40)
        self.assertEqual(receipt["cleanup"], "confirmed")
        self.assertEqual(receipt["inputs_sha256"][str(self.source)], DRIVER.digest(self.source))

    def test_missing_or_incomplete_evidence_is_not_a_pass(self):
        for kind in ("missing", "incomplete", "wrong-mode"):
            with self.subTest(kind=kind):
                def runner(command, cwd, environment, log, timeout):
                    if kind == "incomplete":
                        self.evidence(environment, ["admission"])
                    elif kind == "wrong-mode":
                        Path(environment["COMPUTER_MCP_FORMATTER_EVIDENCE"]).write_text(
                            '{"mode":"native","cases":[]}')
                with self.assertRaises((ValueError, FileNotFoundError)):
                    self.execute(runner)
                self.assertFalse(self.target.exists())
                self.assertFalse((self.output / "receipt.json").exists())

    def test_runner_failure_removes_only_owned_fixture(self):
        def runner(*args):
            raise RuntimeError("build failed")
        with self.assertRaisesRegex(RuntimeError, "build failed"):
            self.execute(runner)
        self.assertFalse(self.target.exists())
        self.assertTrue(self.source.exists())

    def test_existing_fixture_is_preserved(self):
        self.target.write_text("someone else's fixture")
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.execute(lambda *args: self.fail("must not execute"))
        self.assertEqual(self.target.read_text(), "someone else's fixture")

    def test_missing_native_binding_is_rejected(self):
        self.args.mode = "native"
        with self.assertRaisesRegex(ValueError, "--formatter"):
            self.execute(lambda *args: self.fail("must not execute"))
        self.assertFalse(self.target.exists())

    def test_changed_input_fails_without_receipt(self):
        def runner(command, cwd, environment, log, timeout):
            (self.plugin / "cli-tree.json").write_text("unexpected change")
            self.evidence(environment)
        with self.assertRaisesRegex(ValueError, "changed a source"):
            self.execute(runner)
        self.assertFalse(self.target.exists())

    def test_changed_copied_fixture_is_retained_for_investigation(self):
        def runner(command, cwd, environment, log, timeout):
            self.target.write_text("unexpected change")
            self.evidence(environment)
        with self.assertRaisesRegex(RuntimeError, "Copied fixture changed"):
            self.execute(runner)
        self.assertEqual(self.target.read_text(), "unexpected change")

    def test_revision_and_source_preflight(self):
        for value in ("relative/path", str(self.root / "missing")):
            with self.assertRaises(argparse.ArgumentTypeError):
                DRIVER.absolute(value)
        for value in ("master", "abcd", "A" * 40, "b" * 64):
            with self.assertRaises(argparse.ArgumentTypeError):
                DRIVER.revision(value)
        self.assertEqual(DRIVER.revision("a" * 40), "a" * 40)
        for responses in ([str(self.host), "b" * 40], [str(self.host), "a" * 40, " M file"],
                          [str(self.root)]):
            with patch.object(DRIVER, "git", side_effect=responses), self.assertRaises(ValueError):
                DRIVER.verify_source(self.host, "a" * 40)
        with patch.object(DRIVER, "git", side_effect=[str(self.host), "a" * 40, ""]):
            DRIVER.verify_source(self.host, "a" * 40)
        self.assertFalse(self.target.exists())

    def test_process_failure_and_timeout_are_failures(self):
        log = self.root / "process.log"
        with self.assertRaisesRegex(RuntimeError, "exit status 7"):
            DRIVER.run_process([sys.executable, "-c", "raise SystemExit(7)"], self.root,
                               dict(os.environ), log, 2)
        with self.assertRaises(subprocess.TimeoutExpired):
            DRIVER.run_process([sys.executable, "-c", "import time; time.sleep(10)"], self.root,
                               dict(os.environ), log, 0.05)

    def test_descendant_cannot_outlive_successful_parent(self):
        code = "import subprocess,sys; subprocess.Popen([sys.executable,'-c','import time; time.sleep(10)'])"
        with self.assertRaisesRegex(RuntimeError, "live process group"):
            DRIVER.run_process([sys.executable, "-c", code], self.root, dict(os.environ),
                               self.root / "descendant.log", 2)

    def test_help_and_invalid_arguments_from_outside_checkout(self):
        command = [sys.executable, "-B", str(ROOT / "scripts/check_host.py")]
        help_result = subprocess.run(command + ["--help"], cwd=self.root, capture_output=True,
                                     text=True, timeout=5)
        self.assertEqual(help_result.returncode, 0)
        self.assertIn("--host-sha", help_result.stdout)
        invalid = subprocess.run(command, cwd=self.root, capture_output=True, timeout=5)
        self.assertEqual(invalid.returncode, 2)


if __name__ == "__main__":
    unittest.main()
