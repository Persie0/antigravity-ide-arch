#!/usr/bin/env python3
"""Update the AUR recipe from Google's official *standalone IDE* x64 release.

Never select the similarly named Antigravity 2.0 product. No external Python
dependencies, third-party release mirrors, or unverified archive URLs.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import os
from pathlib import Path
import re
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request

DOWNLOAD_PAGE = "https://antigravity.google/download"
# Trust only Google's stable standalone IDE Linux x64 release CDN path.
IDE_URL_RE = re.compile(
    r"https://edgedl\.me\.gvt1\.com/edgedl/release2/[a-zA-Z0-9]+/"
    r"antigravity/stable/(?P<version>\d+\.\d+\.\d+)-(?P<build>\d+)/"
    r"linux-x64/Antigravity%20IDE\.tar\.gz"
)
VERSION_RE = re.compile(r"^pkgver=(\d+\.\d+\.\d+)$", re.M)
BUILD_RE = re.compile(r"^_buildid=(\d+)$", re.M)
HASH_RE = re.compile(r"(?m)^(sha256sums=\(')[0-9a-f]{64}(')")
HEADERS = {"User-Agent": "antigravity-ide-arch-updater/1.0 (+https://github.com/Persie0/antigravity-ide-arch)"}


def fetch_page() -> str:
    request = urllib.request.Request(DOWNLOAD_PAGE, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=40) as response:
        if response.status != 200:
            raise RuntimeError(f"Google download page returned HTTP {response.status}")
        return response.read(5_000_000).decode("utf-8")


def select_latest_ide_url(page: str) -> tuple[str, str, str]:
    # Some renderers HTML-escape or slash-escape the URLs.
    page = html.unescape(page).replace(r"\/", "/").replace(r"\u002F", "/")
    matches = list(IDE_URL_RE.finditer(page))
    if not matches:
        raise RuntimeError("No official standalone Antigravity IDE Linux x64 stable download URL found")
    match = max(
        matches,
        key=lambda m: (tuple(int(v) for v in m["version"].split(".")), int(m["build"])),
    )
    return match["version"], match["build"], match.group(0)


def versioned_content(original: str, version: str, build: str, sha256: str) -> str:
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("Unexpected upstream version")
    if not re.fullmatch(r"\d+", build):
        raise ValueError("Unexpected upstream build ID")
    if not re.fullmatch(r"[0-9a-f]{64}", sha256):
        raise ValueError("Invalid SHA-256")
    result = original
    for pattern, replacement in (
        (VERSION_RE, f"pkgver={version}"),
        (BUILD_RE, f"_buildid={build}"),
        (HASH_RE, lambda m: m.group(1) + sha256 + m.group(2)),
    ):
        result, n = pattern.subn(replacement, result)
        if n != 1:
            raise RuntimeError(f"Expected exactly one PKGBUILD field matching {pattern.pattern}, found {n}")
    old_version = VERSION_RE.search(original)
    old_build = BUILD_RE.search(original)
    if not old_version or not old_build:
        raise RuntimeError("PKGBUILD is missing version/build fields")
    # The same release number can have a new Google build ID: bump pkgrel.
    if old_version.group(1) == version and old_build.group(1) != build:
        rel = re.search(r"(?m)^pkgrel=(\d+)$", original)
        if rel is None:
            raise RuntimeError("PKGBUILD missing pkgrel")
        result, n = re.subn(r"(?m)^pkgrel=\d+$", f"pkgrel={int(rel.group(1)) + 1}", result)
    else:
        result, n = re.subn(r"(?m)^pkgrel=\d+$", "pkgrel=1", result)
    if n != 1:
        raise RuntimeError("Expected exactly one PKGBUILD pkgrel")
    return result


def download_and_hash(url: str) -> str:
    if IDE_URL_RE.fullmatch(url) is None:
        raise ValueError("Refusing non-official or non-IDE download URL")
    request = urllib.request.Request(url, headers=HEADERS)
    with tempfile.TemporaryDirectory(prefix="antigravity-ide-") as tmp:
        file = Path(tmp) / "ide.tar.gz"
        digest = hashlib.sha256()
        with urllib.request.urlopen(request, timeout=120) as response, file.open("wb") as output:
            if response.status != 200:
                raise RuntimeError(f"Google IDE tarball returned HTTP {response.status}")
            while chunk := response.read(1024 * 1024):
                digest.update(chunk)
                output.write(chunk)
        # Check this is genuinely an archive with the known IDE layout before
        # updating the AUR's trusted SHA-256. The Arch build checks the rest.
        with tarfile.open(file, "r:gz") as archive:
            names = set(archive.getnames())
            if not any(n.endswith("/bin/antigravity-ide") and n.startswith("Antigravity IDE/") for n in names):
                raise RuntimeError("Official download archive missing the standalone IDE launcher")
        return digest.hexdigest()


def update(path: Path, *, check_only: bool = False) -> bool:
    original = path.read_text(encoding="utf-8")
    old_version = VERSION_RE.search(original)
    old_build = BUILD_RE.search(original)
    if old_version is None or old_build is None:
        raise RuntimeError("PKGBUILD does not have a recognizable version/build ID")
    version, build, url = select_latest_ide_url(fetch_page())
    print(f"Google standalone IDE: {version} build {build}")
    print(f"Current PKGBUILD:      {old_version.group(1)} build {old_build.group(1)}")
    print(f"Official x64 download: {url}")
    if (version, build) == (old_version.group(1), old_build.group(1)):
        print("Already current; no download or publishing needed.")
        return False
    if check_only:
        print("New upstream build detected (--check: files unchanged).")
        return True
    sha256 = download_and_hash(url)
    replacement = versioned_content(original, version, build, sha256)
    if replacement == original:
        return False
    # Atomic replace: failed download never leaves a partial PKGBUILD.
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, prefix=".PKGBUILD.", delete=False
    ) as tmp:
        tmp.write(replacement)
        tmp_path = Path(tmp.name)
    try:
        os.replace(tmp_path, path)
    finally:
        tmp_path.unlink(missing_ok=True)
    print(f"Updated {path} with SHA-256 {sha256}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Discover updates but do not download or edit")
    parser.add_argument("--pkgbuild", type=Path, default=Path(__file__).resolve().parent.parent / "PKGBUILD")
    args = parser.parse_args()
    try:
        changed = update(args.pkgbuild, check_only=args.check)
    except (OSError, ValueError, RuntimeError, tarfile.TarError, urllib.error.URLError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
