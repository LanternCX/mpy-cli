#!/usr/bin/env python3
"""Build cross-platform release archives."""

from __future__ import annotations

import argparse
import shutil
import tarfile
import tempfile
import zipfile
from pathlib import Path


INCLUDE_PATHS = [
    Path("mpy_cli"),
    Path("README.md"),
    Path("pyproject.toml"),
    Path("assets/default-config.toml"),
    Path("assets/runtime.db"),
]


def build_release_archive(
    target: str, archive: str, version: str, output_dir: Path
) -> Path:
    """@brief 构建发布压缩包。

    @param target 目标平台标识。
    @param archive 压缩格式（tar.gz/zip）。
    @param version 版本号。
    @param output_dir 输出目录。
    @return 生成的压缩包路径。
    """

    package_name = f"mpy-cli-{version}-{target}"
    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="mpy-cli-release-") as temp_dir:
        staging_root = Path(temp_dir) / package_name
        staging_root.mkdir(parents=True, exist_ok=True)

        for relative_path in INCLUDE_PATHS:
            _copy_relative_path(relative_path=relative_path, staging_root=staging_root)

        if archive == "zip":
            archive_path = output_dir / f"{package_name}.zip"
            _write_zip(source_root=staging_root, archive_path=archive_path)
            return archive_path

        archive_path = output_dir / f"{package_name}.tar.gz"
        _write_tar_gz(source_root=staging_root, archive_path=archive_path)
        return archive_path


def _copy_relative_path(relative_path: Path, staging_root: Path) -> None:
    """@brief 复制相对路径文件到 staging 目录。"""

    source = Path.cwd() / relative_path
    if not source.exists():
        return

    destination = staging_root / relative_path
    if source.is_dir():
        shutil.copytree(source, destination)
        return

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def _write_zip(source_root: Path, archive_path: Path) -> None:
    """@brief 写入 zip 压缩包。"""

    with zipfile.ZipFile(
        archive_path, mode="w", compression=zipfile.ZIP_DEFLATED
    ) as zf:
        for path in source_root.rglob("*"):
            arcname = path.relative_to(source_root.parent).as_posix()
            zf.write(path, arcname)


def _write_tar_gz(source_root: Path, archive_path: Path) -> None:
    """@brief 写入 tar.gz 压缩包。"""

    with tarfile.open(archive_path, mode="w:gz") as tf:
        tf.add(source_root, arcname=source_root.name)


def parse_args() -> argparse.Namespace:
    """@brief 解析脚本参数。"""

    parser = argparse.ArgumentParser(description="Build mpy-cli release archives")
    parser.add_argument("--target", required=True, help="target name, e.g. linux-x64")
    parser.add_argument("--archive", choices=["tar.gz", "zip"], required=True)
    parser.add_argument("--version", required=True, help="release version")
    parser.add_argument("--output", default="release", help="output directory")
    return parser.parse_args()


def main() -> int:
    """@brief 脚本入口。"""

    args = parse_args()
    archive_path = build_release_archive(
        target=args.target,
        archive=args.archive,
        version=args.version,
        output_dir=Path(args.output),
    )
    print(f"Archive built: {archive_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
