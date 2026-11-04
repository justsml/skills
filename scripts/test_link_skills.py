"""Exercise the actual installer without touching user skill directories."""
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/link-skills.sh"


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="skill-installer-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.dest = self.root / "skills with spaces"

    def run_installer(self, *destinations):
        # Refuse to exercise an older installer that would ignore the override.
        self.assertIn("--dest)", SCRIPT.read_text())
        args = ["bash", str(SCRIPT)]
        for dest in destinations or (self.dest,):
            args += ["--dest", str(dest)]
        return subprocess.run(args, capture_output=True, text=True, timeout=20)

    def test_fresh_install_and_repeat_preserve_owned_links(self):
        for _ in range(2):
            result = self.run_installer()
            self.assertEqual(result.returncode, 0, result.stderr)
            for source in (ROOT / "skills").glob("*/SKILL.md"):
                self.assertEqual((self.dest / source.parent.name).resolve(), source.parent)

    def test_existing_directory_and_file_are_preserved_without_partial_install(self):
        self.dest.mkdir()
        for directory in (True, False):
            with self.subTest(directory=directory):
                target = self.dest / "unslop"
                if directory:
                    target.mkdir()
                    content = target / "local.txt"
                else:
                    content = target
                content.write_text("user customization")
                other = self.root / "other destination"
                result = self.run_installer(other, self.dest)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(content.read_text(), "user customization")
                self.assertFalse(other.exists())
                content.unlink()
                if directory:
                    target.rmdir()

    def test_unrelated_and_dangling_links_are_preserved(self):
        self.dest.mkdir()
        for exists in (True, False):
            with self.subTest(exists=exists):
                source = self.root / ("existing" if exists else "missing")
                if exists:
                    source.mkdir()
                link = self.dest / "unslop"
                link.symlink_to(source)
                result = self.run_installer()
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(link.readlink(), source)
                link.unlink()

    def test_symlink_destination_is_refused(self):
        real = self.root / "real"
        real.mkdir()
        self.dest.symlink_to(real)
        self.assertNotEqual(self.run_installer().returncode, 0)
        self.assertEqual(list(real.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
