"""Build the declarative formatter plugin; the exporter and vendor stay outside it."""

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import tomllib
import zipfile


def package_bytes(root):
    pending = [root / name for name in (
        "computer-mcp-plugin.toml", "cli-tree.json", "README.md", "CONTRIBUTING.md",
        "LICENSE", "THIRD_PARTY_NOTICES.md", "ThirdPartyNotices.txt",
        "NOTICE.md", "ThirdPartyNotices", "Documentation")]
    contents = {}
    count = total = 0
    while pending:
        path = pending.pop()
        count += 1
        if count > 512:
            raise ValueError("Package contains too many entries")
        mode = path.lstat().st_mode
        if stat.S_ISDIR(mode):
            with os.scandir(path) as children:
                for child in children:
                    if count + len(pending) >= 512:
                        raise ValueError("Package contains too many entries")
                    pending.append(Path(child.path))
            continue
        if not stat.S_ISREG(mode):
            raise ValueError("Package source must contain only regular files and directories")
        with path.open("rb") as source:
            data = source.read(1_048_577)
        total += len(data)
        if len(data) > 1_048_576 or total > 8_388_608:
            raise ValueError("Package source exceeds its size limit")
        contents[path.relative_to(root).as_posix()] = data
    manifest = tomllib.loads(contents["computer-mcp-plugin.toml"].decode())
    if manifest["id"] != "swift-format":
        raise ValueError("Unexpected plugin identity")
    json.loads(contents["cli-tree.json"])
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, data in sorted(contents.items()):
            entry = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(entry, data)
    return output.getvalue(), manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_directory", type=Path)
    args = parser.parse_args()
    data, manifest = package_bytes(Path(__file__).resolve().parent.parent)
    output = args.output_directory.resolve()
    output.mkdir(parents=True, exist_ok=True)
    artifact = output / "swift-format.zip"
    if artifact.exists() or artifact.is_symlink():
        if (artifact.is_symlink() or not artifact.is_file()
                or artifact.stat().st_size != len(data) or artifact.read_bytes() != data):
            raise ValueError("Output differs; use a new directory")
    else:
        with artifact.open("xb") as destination:
            destination.write(data)
    print(json.dumps({"id": manifest["id"], "version": manifest["version"],
                      "archive": str(artifact), "sha256": hashlib.sha256(data).hexdigest()}, sort_keys=True))


if __name__ == "__main__":
    main()
