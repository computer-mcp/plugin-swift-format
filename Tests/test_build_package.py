import importlib.util
import io
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("build_package", ROOT / "scripts/build_package.py")
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)


class PackageTests(unittest.TestCase):
    def test_reproducible_declaration_and_notices_without_executables(self):
        first, manifest = BUILDER.package_bytes(ROOT)
        self.assertEqual(first, BUILDER.package_bytes(ROOT)[0])
        self.assertEqual(manifest["id"], "swift-format")
        self.assertIs(type(manifest["plugin_api"]), int)
        self.assertEqual(manifest["plugin_api"], 1)
        with zipfile.ZipFile(io.BytesIO(first)) as archive:
            self.assertEqual(archive.read("computer-mcp-plugin.toml"),
                             (ROOT / "computer-mcp-plugin.toml").read_bytes())
            self.assertIn("cli-tree.json", archive.namelist())
            self.assertIn("ThirdPartyNotices/SwiftFormat-LICENSE.txt", archive.namelist())
            for name in ("LICENSE", "THIRD_PARTY_NOTICES.md", "ThirdPartyNotices.txt",
                         "NOTICE.md", "ThirdPartyNotices/SwiftFormat-LICENSE.txt",
                         ".github/assets/logo/logo-light.png", ".github/assets/logo/logo-dark.png"):
                self.assertEqual(archive.read(name), (ROOT / name).read_bytes())
            self.assertEqual(archive.read("cli-tree.json"), (ROOT / "cli-tree.json").read_bytes())
            self.assertEqual(
                {name for name in archive.namelist() if name.startswith(".github/")},
                {".github/assets/logo/logo-light.png", ".github/assets/logo/logo-dark.png"})
            for item in archive.infolist():
                self.assertFalse(item.filename.startswith((".git/", ".build/", "Sources/", "bin/")))
                self.assertEqual(item.date_time, (1980, 1, 1, 0, 0, 0))
                self.assertEqual((item.external_attr >> 16) & 0o777, 0o644)

    def test_rejects_unsafe_inputs(self):
        for kind in ("symlink", "directory-link", "oversize", "fifo", "invalid-json"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temp:
                root = Path(temp) / "source"
                root.mkdir()
                for name in ("computer-mcp-plugin.toml", "cli-tree.json", "README.md", "CONTRIBUTING.md",
                             "NOTICE.md", "LICENSE", "THIRD_PARTY_NOTICES.md", "ThirdPartyNotices.txt"):
                    shutil.copyfile(ROOT / name, root / name)
                for name in ("ThirdPartyNotices", "Documentation", ".github/assets/logo"):
                    shutil.copytree(ROOT / name, root / name)
                target = root / "Documentation" / "unsafe"
                if kind == "symlink":
                    target.symlink_to(root / "README.md")
                elif kind == "directory-link":
                    (root / "Documentation").rename(root / "docs")
                    (root / "Documentation").symlink_to(root / "docs", target_is_directory=True)
                elif kind == "oversize":
                    target.write_bytes(b"x" * 1_048_577)
                elif kind == "fifo":
                    os.mkfifo(target)
                else:
                    (root / "cli-tree.json").write_text("not json")
                with self.assertRaises(ValueError):
                    BUILDER.package_bytes(root)

    def test_skips_hidden_files_and_python_caches(self):
        expected, _ = BUILDER.package_bytes(ROOT)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "source"
            shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns(".git", ".build", "__pycache__"))
            (root / "Documentation" / ".DS_Store").write_bytes(b"finder")
            (root / "ThirdPartyNotices" / "__pycache__").mkdir()
            (root / "ThirdPartyNotices" / "__pycache__" / "cached.pyc").write_bytes(b"cache")
            (root / "Documentation" / "stale.pyc").write_bytes(b"cache")
            actual, _ = BUILDER.package_bytes(root)
        self.assertEqual(actual, expected)

    def test_requires_license_notices_and_logos(self):
        for name in ("LICENSE", "THIRD_PARTY_NOTICES.md", "ThirdPartyNotices.txt",
                     ".github/assets/logo/logo-light.png", ".github/assets/logo/logo-dark.png"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                root = Path(temp) / "source"
                shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns(".git", ".build", "__pycache__"))
                (root / name).unlink()
                with self.assertRaises(FileNotFoundError):
                    BUILDER.package_bytes(root)

    def test_command_preserves_existing_artifacts(self):
        with tempfile.TemporaryDirectory() as temp:
            command = [sys.executable, str(ROOT / "scripts/build_package.py"), temp]
            first = subprocess.run(command, capture_output=True, timeout=10)
            second = subprocess.run(command, capture_output=True, timeout=10)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(first.stdout, second.stdout)
            artifact = Path(temp) / "swift-format.zip"
            artifact.write_bytes(b"preserve")
            self.assertNotEqual(subprocess.run(command, capture_output=True, timeout=10).returncode, 0)
            self.assertEqual(artifact.read_bytes(), b"preserve")


if __name__ == "__main__":
    unittest.main()
