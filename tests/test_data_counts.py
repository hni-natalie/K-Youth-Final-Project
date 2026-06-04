import unittest
from pathlib import Path


class TestJobDataConsistency(unittest.TestCase):
    """Test job_blocks consistency with job_data"""

    @classmethod
    def setUpClass(cls):
        cls.project_root = Path(__file__).parent.parent
        cls.data_dir = cls.project_root / "data"

    def test_job_blocks_and_job_data_have_same_file_count(self):
        job_blocks_dir = self.data_dir / "job_blocks"
        job_data_dir = self.data_dir / "job_data"

        count_blocks = self._count_files(job_blocks_dir)
        count_data = self._count_files(job_data_dir)

        print(f"\n📂 job_blocks: {count_blocks} files")
        print(f"📂 job_data:   {count_data} files")

        self.assertEqual(
            count_blocks,
            count_data,
            f"❌ Mismatch: job_blocks ({count_blocks}) != job_data ({count_data})"
        )

    def test_new_job_blocks_folder_exists_and_counts(self):
        """
        Ensure incremental pipeline output folder is valid
        """
        new_blocks_dir = self.data_dir / "job_blocks" / "new"

        count_new = self._count_files(new_blocks_dir)

        print(f"\n📂 job_blocks/new: {count_new} files")

        # optional safety checks
        self.assertTrue(
            new_blocks_dir.exists(),
            "❌ job_blocks/new folder does not exist"
        )

        # if pipeline ran, it should not be negative or broken
        self.assertGreaterEqual(
            count_new,
            0,
            "❌ Invalid file count in job_blocks/new"
        )

    def _count_files(self, folder: Path) -> int:
        if not folder.exists():
            return 0
        return len([f for f in folder.iterdir() if f.is_file()])


if __name__ == "__main__":
    unittest.main(verbosity=2)