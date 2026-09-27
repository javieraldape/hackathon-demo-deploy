import difflib
from pathlib import Path
import runpy
import tempfile
import unittest


apply_patches = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts/apply-patches"))["apply_patches"]


class PatchApplicationTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        self.source.mkdir()
        self.file = self.source / "example.txt"
        self.file.write_text("before\n")

    def patch(self, name, before, after, path="example.txt"):
        patch = self.root / name
        patch.write_text("".join(difflib.unified_diff(
            before.splitlines(keepends=True), after.splitlines(keepends=True),
            fromfile=f"a/{path}" if before else "/dev/null",
            tofile=f"b/{path}" if after else "/dev/null",
        )))
        return patch

    def test_applies_in_order_and_repeats_without_changes(self):
        first = self.patch("first.patch", "before\n", "middle\n")
        second = self.patch("second.patch", "middle\n", "after\n")
        self.assertEqual(apply_patches(self.source, [first, second]), "applied")
        self.assertEqual(self.file.read_text(), "after\n")
        modified = self.file.stat().st_mtime_ns
        self.assertEqual(apply_patches(self.source, [first, second]), "already applied")
        self.assertEqual(self.file.stat().st_mtime_ns, modified)

    def test_rejects_partial_series_without_writes(self):
        first = self.patch("first.patch", "before\n", "middle\n")
        second = self.patch("second.patch", "middle\n", "after\n")
        self.file.write_text("middle\n")
        with self.assertRaisesRegex(ValueError, "partial application or source drift"):
            apply_patches(self.source, [first, second])
        self.assertEqual(self.file.read_text(), "middle\n")

    def test_later_failure_does_not_apply_earlier_patch(self):
        first = self.patch("first.patch", "before\n", "middle\n")
        second = self.patch("second.patch", "unexpected\n", "after\n")
        with self.assertRaises(ValueError):
            apply_patches(self.source, [first, second])
        self.assertEqual(self.file.read_text(), "before\n")

    def test_new_and_deleted_files_are_idempotent(self):
        addition = self.patch("new.patch", "", "new\n", "nested/new.txt")
        deletion = self.patch("delete.patch", "before\n", "")
        self.assertEqual(apply_patches(self.source, [addition, deletion]), "applied")
        self.assertFalse(self.file.exists())
        self.assertEqual((self.source / "nested/new.txt").read_text(), "new\n")
        self.assertEqual(apply_patches(self.source, [addition, deletion]), "already applied")

    def test_preserves_unrelated_file_and_executable_mode(self):
        self.file.chmod(0o755)
        unrelated = self.source / "private.txt"
        unrelated.write_text("untouched\n")
        patch = self.patch("change.patch", "before\n", "after\n")
        apply_patches(self.source, [patch])
        self.assertEqual(self.file.stat().st_mode & 0o777, 0o755)
        self.assertEqual(unrelated.read_text(), "untouched\n")

    def test_rejects_symlinked_target(self):
        outside = self.root / "outside.txt"
        outside.write_text("before\n")
        self.file.unlink()
        self.file.symlink_to(outside)
        patch = self.patch("change.patch", "before\n", "after\n")
        with self.assertRaisesRegex(ValueError, "symlink"):
            apply_patches(self.source, [patch])
        self.assertEqual(outside.read_text(), "before\n")

    def test_rejects_symlinked_parent(self):
        (self.source / "nested").symlink_to(self.root, target_is_directory=True)
        patch = self.patch("change.patch", "", "new\n", "nested/new.txt")
        with self.assertRaisesRegex(ValueError, "symlink"):
            apply_patches(self.source, [patch])
        self.assertFalse((self.root / "new.txt").exists())

    def test_rejects_path_traversal(self):
        patch = self.patch("change.patch", "", "new\n", "../outside.txt")
        with self.assertRaises(ValueError):
            apply_patches(self.source, [patch])
        self.assertFalse((self.root / "outside.txt").exists())

    def test_rejects_empty_patch(self):
        patch = self.root / "empty.patch"
        patch.touch()
        with self.assertRaisesRegex(ValueError, "Invalid or empty patch"):
            apply_patches(self.source, [patch])

    def test_install_patch_order_and_pins(self):
        script = (Path(__file__).resolve().parents[1] / "scripts/install").read_text()
        self.assertLess(script.index('rev-parse HEAD)" = "$QM_COMMIT"'), script.index('patches/qm-trusted-memory.patch'))
        self.assertLess(script.index('rev-parse HEAD)" = "$GBRAIN_COMMIT"'), script.index('patches/gbrain-scoped-bridge.patch'))
        self.assertLess(script.index('patches/qm-trusted-memory.patch'), script.index('npm run build:connector-sdk'))
        self.assertLess(script.index('patches/gbrain-scoped-bridge.patch'), script.index('bun install'))
        self.assertLess(script.index('npm --prefix "$CLAW_PACKAGE" ci'), script.index('patches/openclaw-01-detach.patch'))
        self.assertLess(script.index('Pinned ${name} package version mismatch'), script.index('patches/openclaw-01-detach.patch'))
        self.assertLess(script.index('patches/openclaw-01-detach.patch'), script.index('patches/openclaw-02-arm-touch.patch'))


if __name__ == "__main__":
    unittest.main()
