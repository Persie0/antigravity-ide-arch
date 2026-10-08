"""Offline regression tests: never select Antigravity 2.0 as the IDE."""
import sys
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import update_package as updater


class ReleaseParsingTests(unittest.TestCase):
    def url(self, ver, build):
        return (
            "https://edgedl.me.gvt1.com/edgedl/release2/j0qc3/"
            f"antigravity/stable/{ver}-{build}/linux-x64/Antigravity%20IDE.tar.gz"
        )

    def test_picks_latest_ide_not_other_antigravity_product(self):
        page = (
            "Antigravity 2.0 v8.20.0 "
            "https://storage.googleapis.com/antigravity-public/antigravity-hub/"
            "8.20.0-999/linux-x64/Antigravity.tar.gz "
            + self.url("2.5.4", "200")
            + " "
            + self.url("2.5.5", "100")
        )
        self.assertEqual(updater.select_latest_ide_url(page), ("2.5.5", "100", self.url("2.5.5", "100")))

    def test_must_be_official_stable_linux_x64_url(self):
        with self.assertRaises(RuntimeError):
            updater.select_latest_ide_url(
                "https://evil.example/antigravity/stable/99.0.0-1/linux-x64/Antigravity%20IDE.tar.gz"
            )
        with self.assertRaises(ValueError):
            updater.download_and_hash("https://evil.example/software.tar.gz")

    def test_selects_newest_build_for_same_version(self):
        page = self.url("2.5.5", "200") + " " + self.url("2.5.5", "201")
        self.assertEqual(updater.select_latest_ide_url(page)[1], "201")

    def test_decodes_escaped_url(self):
        page = self.url("2.5.5", "3").replace("/", r"\u002F")
        self.assertEqual(updater.select_latest_ide_url(page)[0], "2.5.5")


class PackageUpdateTests(unittest.TestCase):
    ORIGINAL = (
        "pkgver=2.5.5\n_buildid=100\npkgrel=1\n"
        "source=(\"https://example.org/${pkgver}-${_buildid}\")\n"
        "sha256sums=('" + "a" * 64 + "' 'SKIP')\n"
    )

    def test_new_version_resets_pkgrel_and_changes_hash(self):
        updated = updater.versioned_content(self.ORIGINAL, "2.5.6", "101", "b" * 64)
        self.assertIn("pkgver=2.5.6", updated)
        self.assertIn("_buildid=101", updated)
        self.assertIn("pkgrel=1", updated)
        self.assertIn("b" * 64, updated)

    def test_same_version_new_build_bumps_pkgrel(self):
        updated = updater.versioned_content(self.ORIGINAL, "2.5.5", "101", "b" * 64)
        self.assertIn("pkgrel=2", updated)

    def test_rejects_non_sha_and_malformed_pkgbuild(self):
        with self.assertRaises(ValueError):
            updater.versioned_content(self.ORIGINAL, "2.5.6", "101", "SKIP")
        with self.assertRaises(RuntimeError):
            updater.versioned_content("pkgver=1.0.0", "2.5.6", "101", "b" * 64)

    def test_unchanged_build_does_not_download(self):
        import tempfile
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "PKGBUILD"
            p.write_text(self.ORIGINAL)
            with patch.object(updater, "fetch_page", return_value=ReleaseParsingTests().url("2.5.5", "100")), \
                 patch.object(updater, "download_and_hash", side_effect=AssertionError("must not download")):
                self.assertFalse(updater.update(p))
            self.assertEqual(p.read_text(), self.ORIGINAL)


if __name__ == "__main__":
    unittest.main()
