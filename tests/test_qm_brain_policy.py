import runpy
from pathlib import Path
import unittest


module = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts/configure-qm-brain"))
merge_policy = module["merge_policy"]
BEGIN = module["BEGIN"]
END = module["END"]


class BrainPolicyTest(unittest.TestCase):
    def test_preserves_existing_instructions(self):
        self.assertTrue(merge_policy("Existing policy", "Brain policy").startswith("Existing policy\n\n"))

    def test_repeated_configuration_is_idempotent(self):
        once = merge_policy("Existing policy", "Brain policy")
        self.assertEqual(merge_policy(once, "Brain policy"), once)

    def test_updates_only_managed_block(self):
        current = f"Before\n{BEGIN}\nOld\n{END}\nAfter"
        self.assertEqual(merge_policy(current, "New"), f"Before\n{BEGIN}\nNew\n{END}\nAfter")

    def test_rejects_ambiguous_markers(self):
        for current in [BEGIN, END, END + BEGIN, BEGIN + END + BEGIN + END]:
            with self.subTest(current=current), self.assertRaises(ValueError):
                merge_policy(current, "New")


if __name__ == "__main__":
    unittest.main()
